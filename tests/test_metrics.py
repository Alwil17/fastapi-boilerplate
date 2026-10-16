import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.metrics import install_metrics


@pytest.fixture
def metrics_client():
    app = FastAPI()

    @app.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"id": item_id}

    @app.get("/explode")
    def explode():
        raise RuntimeError("boom")

    install_metrics(app)
    return TestClient(app, raise_server_exceptions=False)


def _sample(text: str, name: str, **labels) -> float:
    for line in text.splitlines():
        if line.startswith(name + "{") and all(
            f'{k}="{v}"' in line for k, v in labels.items()
        ):
            return float(line.rsplit(" ", 1)[1])
    return 0.0


def _count(client, **labels) -> float:
    return _sample(client.get("/metrics").text, "http_requests_total", **labels)


def test_metrics_endpoint_exposes_prometheus_format(metrics_client):
    response = metrics_client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text


def test_requests_are_labelled_by_route_template(metrics_client):
    labels = {"method": "GET", "path": "/items/{item_id}", "status": "200"}
    before = _count(metrics_client, **labels)
    for item_id in (1, 2, 3):
        metrics_client.get(f"/items/{item_id}")
    assert _count(metrics_client, **labels) == before + 3
    assert 'path="/items/1"' not in metrics_client.get("/metrics").text


def test_unknown_urls_share_one_label(metrics_client):
    labels = {"method": "GET", "path": "unmatched", "status": "404"}
    before = _count(metrics_client, **labels)
    metrics_client.get("/wp-admin.php")
    metrics_client.get("/.env")
    text = metrics_client.get("/metrics").text
    assert _sample(text, "http_requests_total", **labels) == before + 2
    assert "wp-admin" not in text


def test_unhandled_exception_counted_as_500(metrics_client):
    labels = {"method": "GET", "path": "/explode", "status": "500"}
    before = _count(metrics_client, **labels)
    assert metrics_client.get("/explode").status_code == 500
    assert _count(metrics_client, **labels) == before + 1


def test_latency_histogram_recorded(metrics_client):
    metrics_client.get("/items/1")
    text = metrics_client.get("/metrics").text
    assert _sample(text, "http_request_duration_seconds_count", path="/items/{item_id}")


def test_metrics_scrapes_are_not_counted(metrics_client):
    metrics_client.get("/metrics")
    assert 'path="/metrics"' not in metrics_client.get("/metrics").text


def test_metrics_token_is_enforced_when_configured(metrics_client, monkeypatch):
    monkeypatch.setattr(settings, "METRICS_TOKEN", "s3cret-token")
    assert metrics_client.get("/metrics").status_code == 401
    bad = metrics_client.get("/metrics", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401
    ok = metrics_client.get(
        "/metrics", headers={"Authorization": "Bearer s3cret-token"}
    )
    assert ok.status_code == 200


def test_metrics_not_exposed_unless_enabled(client):
    assert settings.PROMETHEUS_ENABLED is False
    assert client.get("/metrics").status_code == 404
