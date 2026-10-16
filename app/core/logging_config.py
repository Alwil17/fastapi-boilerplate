import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

from app.core.config import settings

# Set per request by RequestContextMiddleware; "-" outside of a request.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# Attributes every LogRecord has: anything else came from `extra=` and is logged too.
# color_message: uvicorn's ANSI-coloured duplicate of the message.
_RESERVED = set(vars(logging.makeLogRecord({}))) | {
    "message",
    "asctime",
    "taskName",
    "color_message",
}
_HANDLER_MARK = "_app_log_handler"


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line: timestamp, level, logger, message, request_id, extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_var.get()),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and key not in payload:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def build_formatter() -> logging.Formatter:
    if settings.LOG_FORMAT == "json":
        return JsonFormatter()
    return logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s: %(message)s"
    )


def configure_logging() -> None:
    """Send all logs (app and uvicorn) to stdout, as JSON or human-readable text.

    Idempotent: replaces only the handler installed by a previous call.
    """
    root = logging.getLogger()
    for handler in [h for h in root.handlers if getattr(h, _HANDLER_MARK, False)]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    setattr(handler, _HANDLER_MARK, True)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(build_formatter())
    root.addHandler(handler)
    root.setLevel(settings.LOG_LEVEL)

    # uvicorn installs its own handlers; route them through ours. Its access log is
    # replaced by the request log of RequestContextMiddleware.
    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    access = logging.getLogger("uvicorn.access")
    access.handlers.clear()
    access.propagate = False
