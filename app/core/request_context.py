import logging
import re
import time
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import internal_error_response
from app.core.logging_config import request_id_var
from app.core.sentry import ACCESS_LOGGER, capture_exception

REQUEST_ID_HEADER = "X-Request-ID"
# Only accept ids that are safe to echo into headers and logs.
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
# Probes and scrapes fire constantly; log them at DEBUG only.
QUIET_PATHS = {"/health/live", "/health/ready", "/metrics"}
MAX_LOGGED_PATH = 200

logger = logging.getLogger(ACCESS_LOGGER)
error_logger = logging.getLogger("app.request")


class RequestContextMiddleware:
    """Per-request context: request id, access log and last-resort 500 handling.

    - Reuses a well-formed inbound X-Request-ID, otherwise generates one, and echoes
      it in the response so a client can quote it when reporting a problem.
    - Logs one line per request (method, path without query string, status, duration).
    - Turns unhandled exceptions into the standard 500 error body here, inside the
      CORS/security-headers middlewares, so those headers are kept on error responses.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        inbound = Headers(scope=scope).get(REQUEST_ID_HEADER)
        request_id = (
            inbound
            if inbound and _VALID_REQUEST_ID.fullmatch(inbound)
            else uuid.uuid4().hex
        )
        token = request_id_var.set(request_id)
        scope.setdefault("state", {})["request_id"] = request_id

        status_code = 500
        response_started = False
        started_at = time.perf_counter()

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            try:
                await self.app(scope, receive, send_with_request_id)
            except Exception as exc:
                capture_exception(exc)
                error_logger.exception(
                    "Unhandled exception", extra=_request_fields(scope)
                )
                if response_started:
                    raise
                await internal_error_response()(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            path = scope["path"]
            if status_code >= 500:
                level = logging.ERROR
            elif path in QUIET_PATHS:
                level = logging.DEBUG
            else:
                level = logging.INFO
            logger.log(
                level,
                "%s %s %s",
                scope["method"],
                _loggable_path(scope),
                status_code,
                extra={
                    **_request_fields(scope),
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
            )
            request_id_var.reset(token)


def _loggable_path(scope: Scope) -> str:
    # raw_path keeps %0a-style escapes undecoded, so a crafted URL cannot inject lines.
    raw = scope.get("raw_path") or scope["path"].encode("utf-8")
    return raw.split(b"?", 1)[0].decode("latin-1")[:MAX_LOGGED_PATH]


def _request_fields(scope: Scope) -> dict:
    client = scope.get("client")
    return {
        "method": scope["method"],
        "path": _loggable_path(scope),
        "client_ip": client[0] if client else None,
    }
