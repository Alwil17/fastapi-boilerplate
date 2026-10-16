"""Single error format for every non-2xx response produced by the app.

    {"error": {"code": "not_found", "message": "...", "request_id": "..."}}

Validation errors (422) add `error.details`: a list of {"loc", "msg", "type"}.
Headers set on the exception (WWW-Authenticate, Retry-After) are preserved.
"""

from collections.abc import Mapping

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging_config import request_id_var

ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    422: "validation_error",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_error",
    status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
}
INTERNAL_ERROR_MESSAGE = "Internal server error"


def error_response(
    status_code: int,
    message: str,
    *,
    code: str | None = None,
    details: list | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    error: dict = {
        "code": code or ERROR_CODES.get(status_code, f"http_{status_code}"),
        "message": message,
        "request_id": request_id_var.get(),
    }
    if details is not None:
        error["details"] = details
    return JSONResponse({"error": error}, status_code=status_code, headers=headers)


def internal_error_response() -> JSONResponse:
    """Body for unhandled exceptions: never exposes the exception itself."""
    return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, INTERNAL_ERROR_MESSAGE)


async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return error_response(exc.status_code, message, headers=exc.headers)


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    # Pydantic's `input` and `ctx` are dropped: `input` would echo submitted values
    # (e.g. a rejected password) back and into logs, `ctx` may not be serializable.
    details = [
        {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
        for err in exc.errors()
    ]
    return error_response(422, "Validation failed", details=details)


def register_exception_handlers(app: FastAPI) -> None:
    # Starlette types handlers as taking `Exception`; ours take the narrower type.
    app.add_exception_handler(
        StarletteHTTPException, http_exception_handler  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        RequestValidationError, validation_exception_handler  # type: ignore[arg-type]
    )
