import logging
import re

import pytest

from app.main import app

REQUEST_ID = re.compile(r"[0-9a-f]{32}")


@pytest.fixture
def boom_route():
    async def boom():
        raise RuntimeError("secret internal detail")

    async def boom_started():
        from fastapi.responses import StreamingResponse

        async def gen():
            yield b"partial"
            raise RuntimeError("late failure")

        return StreamingResponse(gen())

    app.add_api_route("/__boom", boom)
    app.add_api_route("/__boom_started", boom_started)
    yield
    del app.router.routes[-2:]


def test_401_uses_error_envelope_and_keeps_headers(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
    body = response.json()["error"]
    assert body["code"] == "unauthorized"
    assert body["message"] == "Not authenticated"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_404_uses_error_envelope(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_405_uses_error_envelope(client):
    response = client.delete("/health/live")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_422_lists_fields_without_echoing_input(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "pw7char", "name": "x"},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert {"email", "password"} <= {d["loc"][-1] for d in error["details"]}
    for detail in error["details"]:
        assert set(detail) == {"loc", "msg", "type"}
    assert "pw7char" not in response.text
    assert "not-an-email" not in response.text


def test_unhandled_exception_returns_generic_500(client, boom_route, caplog):
    safe = type(client)(client.app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR):
        response = safe.get("/__boom")
    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "internal_error"
    assert error["message"] == "Internal server error"
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert "secret internal detail" not in response.text
    # the real cause is logged server-side, with the same request id
    failure = next(r for r in caplog.records if r.message == "Unhandled exception")
    assert failure.exc_info[0] is RuntimeError
    assert failure.request_id == error["request_id"]


def test_500_keeps_security_headers(client, boom_route):
    safe = type(client)(client.app, raise_server_exceptions=False)
    response = safe.get("/__boom")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_generated_request_id_is_returned(client):
    response = client.get("/health/live")
    assert REQUEST_ID.fullmatch(response.headers["X-Request-ID"])


def test_inbound_request_id_is_propagated(client):
    response = client.get("/auth/me", headers={"X-Request-ID": "trace-abc_123.4"})
    assert response.headers["X-Request-ID"] == "trace-abc_123.4"
    assert response.json()["error"]["request_id"] == "trace-abc_123.4"


@pytest.mark.parametrize("bad", ["a b", "x" * 65, "id;drop"])
def test_malformed_inbound_request_id_is_replaced(client, bad):
    response = client.get("/health/live", headers={"X-Request-ID": bad})
    assert REQUEST_ID.fullmatch(response.headers["X-Request-ID"])


def test_access_log_has_one_line_without_query_string(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/auth/me?token=supersecret")
    records = [r for r in caplog.records if r.name == "app.access"]
    assert len(records) == 1
    record = records[0]
    assert record.method == "GET"
    assert record.path == "/auth/me"
    assert record.status == 401
    assert record.duration_ms >= 0
    assert "supersecret" not in record.getMessage()


def test_probes_are_logged_at_debug_only(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/health/live")
    assert not [r for r in caplog.records if r.name == "app.access"]


def test_encoded_newline_in_path_cannot_forge_log_lines(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/x%0aINFO fake")
    record = next(r for r in caplog.records if r.name == "app.access")
    assert "\n" not in record.getMessage()
