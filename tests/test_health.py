import pytest

from app.core.config import settings


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert "timestamp" in data


def test_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_liveness(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


class _BrokenSession:
    def execute(self, *_, **__):
        raise RuntimeError("database down")


@pytest.fixture
def db_down(client):
    from app.db.base import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: _BrokenSession()
    yield


def test_health_reports_degraded_when_database_is_down(client, db_down):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unhealthy"


def test_readiness_returns_503_when_database_is_down(client, db_down):
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "database down" not in response.text


def test_liveness_does_not_touch_the_database(client, db_down):
    assert client.get("/health/live").status_code == 200


def test_root_links_to_docs_outside_production(client):
    assert client.get("/").json()["docs"] == "/docs"


def test_root_hides_docs_link_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    assert "docs" not in client.get("/").json()
