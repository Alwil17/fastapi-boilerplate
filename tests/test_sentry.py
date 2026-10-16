import pytest
import sentry_sdk
from fastapi.testclient import TestClient
from sentry_sdk.transport import Transport

from app.core import sentry
from app.core.config import settings
from app.main import app


class RecordingTransport(Transport):
    events: list = []

    def capture_envelope(self, envelope):
        event = envelope.get_event()
        if event is not None:
            self.events.append(event)


@pytest.fixture(autouse=True)
def reset_sentry():
    yield
    sentry._enabled = False
    sentry_sdk.get_client().close()


def test_disabled_without_dsn(monkeypatch):
    monkeypatch.setattr(settings, "SENTRY_DSN", None)
    called = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: called.append(kw))
    assert sentry.init_sentry() is False
    assert called == []


def test_init_collects_no_request_data(monkeypatch):
    monkeypatch.setattr(settings, "SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
    monkeypatch.setattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.25)
    called = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: called.append(kw))
    assert sentry.init_sentry() is True
    kwargs = called[0]
    collection = kwargs["data_collection"]
    assert collection["http_bodies"] == []
    assert collection["user_info"] is False
    assert collection["stack_frame_variables"] is False
    assert collection["cookies"] == {"mode": "off"}
    assert collection["http_headers"] == {"request": {"mode": "off"}}
    assert kwargs["traces_sample_rate"] == 0.25
    assert kwargs["environment"] == settings.APP_ENV
    assert kwargs["release"] == settings.APP_VERSION


def test_capture_is_a_noop_when_disabled(monkeypatch):
    called = []
    monkeypatch.setattr(sentry_sdk, "capture_exception", called.append)
    sentry.capture_exception(RuntimeError("x"))
    assert called == []


def test_unhandled_500_reaches_sentry(client, monkeypatch):
    """The 500 fallback swallows the exception, so it must report it explicitly."""
    events = RecordingTransport.events = []
    real_init = sentry_sdk.init
    monkeypatch.setattr(settings, "SENTRY_DSN", "https://key@o0.ingest.sentry.io/1")
    monkeypatch.setattr(
        sentry_sdk, "init", lambda **kw: real_init(**kw, transport=RecordingTransport)
    )
    assert sentry.init_sentry()

    async def boom():
        raise RuntimeError("kaboom")

    app.add_api_route("/__boom", boom)
    try:
        response = TestClient(app, raise_server_exceptions=False).get("/__boom")
    finally:
        del app.router.routes[-1]

    assert response.status_code == 500
    assert len(events) == 1
    exception = events[0]["exception"]["values"][0]
    assert exception["type"] == "RuntimeError"
    assert exception["value"] == "kaboom"
    assert events[0]["tags"]["request_id"] == response.headers["X-Request-ID"]
    assert "data" not in events[0].get("request", {})
