import json
import logging

from app.core import logging_config
from app.core.logging_config import JsonFormatter, configure_logging, request_id_var


def _record(msg="hello", **extra):
    record = logging.LogRecord("app.test", logging.INFO, __file__, 1, msg, None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_formatter_outputs_one_json_object():
    token = request_id_var.set("abc123")
    try:
        out = json.loads(JsonFormatter().format(_record("hi", user_id=7)))
    finally:
        request_id_var.reset(token)
    assert out["message"] == "hi"
    assert out["level"] == "INFO"
    assert out["logger"] == "app.test"
    assert out["request_id"] == "abc123"
    assert out["user_id"] == 7
    assert out["timestamp"].endswith("+00:00")


def test_json_formatter_escapes_newlines_in_messages():
    line = JsonFormatter().format(_record('a\nb\r\n{"level": "FAKE"}'))
    assert "\n" not in line
    assert json.loads(line)["level"] == "INFO"


def test_json_formatter_includes_exception_and_unserializable_extras():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = _record("failed", obj=object())
        record.exc_info = sys.exc_info()
    out = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in out["exception"]
    assert out["obj"].startswith("<object")


def test_configure_logging_is_idempotent():
    root = logging.getLogger()
    configure_logging()
    configure_logging()
    ours = [h for h in root.handlers if getattr(h, logging_config._HANDLER_MARK, False)]
    assert len(ours) == 1


def test_configure_logging_routes_uvicorn_through_root():
    configure_logging()
    assert logging.getLogger("uvicorn.error").propagate is True
    assert logging.getLogger("uvicorn.error").handlers == []
    assert logging.getLogger("uvicorn.access").propagate is False
