from app.core.roles import Role
from app.db.models.user import User
from app.jobs.create_admin import create_admin


def _login(client, email, password="testpassword123"):
    client.post(
        "/auth/register", json={"name": "N", "email": email, "password": password}
    )
    token = client.post(
        "/auth/token", data={"username": email, "password": password}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _promote(db_session, email):
    db_session.query(User).filter_by(email=email).one().role = Role.ADMIN
    db_session.commit()


def test_list_users_requires_auth(client):
    assert client.get("/users").status_code == 401


def test_list_users_forbidden_for_regular_user(client):
    headers = _login(client, "user@example.com")
    assert client.get("/users", headers=headers).status_code == 403


def test_list_users_allowed_for_admin_and_paginated(client, db_session):
    for i in range(3):
        _login(client, f"u{i}@example.com")
    headers = _login(client, "boss@example.com")
    _promote(db_session, "boss@example.com")

    page = client.get("/users", params={"skip": 1, "limit": 2}, headers=headers)
    assert page.status_code == 200
    assert [u["email"] for u in page.json()] == ["u1@example.com", "u2@example.com"]


def test_list_users_rejects_bad_pagination(client, db_session):
    headers = _login(client, "boss@example.com")
    _promote(db_session, "boss@example.com")
    assert client.get("/users?limit=0", headers=headers).status_code == 422
    assert client.get("/users?limit=1000", headers=headers).status_code == 422
    assert client.get("/users?skip=-1", headers=headers).status_code == 422


def test_role_is_read_from_db_not_token(client, db_session):
    """Demoting a user takes effect immediately, even with an old admin token."""
    headers = _login(client, "boss@example.com")
    _promote(db_session, "boss@example.com")
    assert client.get("/users", headers=headers).status_code == 200
    db_session.query(User).one().role = Role.USER
    db_session.commit()
    assert client.get("/users", headers=headers).status_code == 403


def test_create_admin_job(db_session, monkeypatch):
    import app.jobs.create_admin as job

    monkeypatch.setattr(job, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)
    create_admin("Root@Example.com", "testpassword123")
    create_admin("root@example.com", "testpassword123")  # idempotent
    user = db_session.query(User).one()
    assert user.email == "root@example.com"
    assert user.role == Role.ADMIN
