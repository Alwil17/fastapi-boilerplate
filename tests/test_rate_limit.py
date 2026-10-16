import pytest

from app.core import rate_limit
from app.core.config import settings


@pytest.fixture
def limited(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    rate_limit.reset_rate_limits()
    yield
    rate_limit.reset_rate_limits()


def _login(client):
    return client.post(
        "/auth/token", data={"username": "x@example.com", "password": "nope-nope"}
    )


def test_login_is_rate_limited(client, limited):
    statuses = [_login(client).status_code for _ in range(12)]
    assert statuses[:10] == [401] * 10
    assert statuses[10:] == [429, 429]


def test_429_has_retry_after(client, limited):
    for _ in range(10):
        _login(client)
    response = _login(client)
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1
    assert response.json()["error"]["code"] == "rate_limited"
    assert response.json()["error"]["message"] == "Too many requests"


def test_limits_are_per_scope(client, limited):
    for _ in range(11):
        _login(client)
    refresh = client.post("/auth/refresh", json={"refresh_token": "nope"})
    assert refresh.status_code == 401  # login being limited does not block refresh


def test_register_is_rate_limited(client, limited):
    codes = [
        client.post(
            "/auth/register",
            json={
                "name": "N",
                "email": f"u{i}@example.com",
                "password": "testpassword123",
            },
        ).status_code
        for i in range(6)
    ]
    assert codes == [201] * 5 + [429]


def test_disabled_by_default_in_tests(client):
    assert all(_login(client).status_code == 401 for _ in range(15))
