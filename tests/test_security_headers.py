from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security_headers import SecurityHeadersMiddleware


def test_baseline_headers_on_api_response(client):
    response = client.get("/health/live")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "Strict-Transport-Security" not in response.headers


def test_auth_responses_not_cacheable(client):
    response = client.post("/auth/refresh", json={"refresh_token": "nope"})
    assert response.headers["Cache-Control"] == "no-store"


def test_strict_mode_adds_hsts_and_csp():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, strict=True)

    @app.get("/x")
    def x():
        return {}

    response = TestClient(app).get("/x")
    assert "max-age=" in response.headers["Strict-Transport-Security"]
    assert response.headers["Content-Security-Policy"].startswith("default-src 'none'")


def test_does_not_override_existing_header():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, strict=False)

    @app.get("/x")
    def x():
        from fastapi import Response

        return Response("{}", headers={"X-Frame-Options": "SAMEORIGIN"})

    assert TestClient(app).get("/x").headers["X-Frame-Options"] == "SAMEORIGIN"
