from datetime import UTC

import pytest


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data


def test_login(client):
    """Test user login."""
    # First register a user
    client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Then login
    response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client):
    """Test getting current user info."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    login_response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def _register_and_login(client, email="test@example.com", password="testpassword123"):
    client.post(
        "/auth/register",
        json={"name": "Test User", "email": email, "password": password},
    )
    return client.post(
        "/auth/token", data={"username": email, "password": password}
    ).json()


def test_register_admin_email_gets_user_role(client):
    """An email containing 'admin' must never grant the admin role."""
    response = client.post(
        "/auth/register",
        json={
            "name": "Sneaky",
            "email": "admin@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"


def test_login_wrong_password(client):
    _register_and_login(client)
    response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_register_duplicate_email(client):
    _register_and_login(client)
    response = client.post(
        "/auth/register",
        json={
            "name": "Dup",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 400


def test_refresh_token_rotates(client):
    tokens = _register_and_login(client)
    response = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


def test_refresh_token_replay_rejected(client):
    tokens = _register_and_login(client)
    client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    replay = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert replay.status_code == 401


def test_refresh_token_expired(client, db_session):
    from datetime import datetime, timedelta

    from app.db.models.refresh_token import RefreshToken

    tokens = _register_and_login(client)
    stored = (
        db_session.query(RefreshToken).filter_by(token=tokens["refresh_token"]).one()
    )
    stored.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token expired"


def test_refresh_token_unknown(client):
    response = client.post("/auth/refresh", json={"refresh_token": "nope"})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "password",
    ["short", " " * 12, "é" * 40],  # too short, blank, over 72 bytes
)
def test_register_rejects_bad_password(client, password):
    response = client.post(
        "/auth/register",
        json={"name": "Bad", "email": "bad@example.com", "password": password},
    )
    assert response.status_code == 422


def test_register_rejects_empty_name(client):
    response = client.post(
        "/auth/register",
        json={"name": "  ", "email": "n@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 422


def test_email_is_case_insensitive(client):
    _register_and_login(client, email="Mixed@Example.com")
    response = client.post(
        "/auth/token",
        data={"username": "MIXED@example.COM", "password": "testpassword123"},
    )
    assert response.status_code == 200
    duplicate = client.post(
        "/auth/register",
        json={
            "name": "Dup",
            "email": "mixed@example.com",
            "password": "testpassword123",
        },
    )
    assert duplicate.status_code == 400


def _deactivate(db_session, email="test@example.com"):
    from app.db.models.user import User

    db_session.query(User).filter_by(email=email).one().is_active = False
    db_session.commit()


def test_inactive_user_cannot_login(client, db_session):
    _register_and_login(client)
    _deactivate(db_session)
    response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401


def test_inactive_user_existing_token_rejected(client, db_session):
    tokens = _register_and_login(client)
    _deactivate(db_session)
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 401


def test_login_unknown_email_same_response_as_wrong_password(client):
    _register_and_login(client)
    unknown = client.post(
        "/auth/token", data={"username": "nobody@example.com", "password": "whatever1"}
    )
    wrong = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "whatever1"},
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()
