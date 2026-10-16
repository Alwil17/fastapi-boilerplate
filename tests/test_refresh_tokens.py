from datetime import UTC, datetime

from app.core.security import hash_refresh_token
from app.db.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repository import RefreshTokenRepository

CREDS = {"name": "T", "email": "t@example.com", "password": "testpassword123"}


def _login(client):
    client.post("/auth/register", json=CREDS)
    return client.post(
        "/auth/token",
        data={"username": CREDS["email"], "password": CREDS["password"]},
    ).json()


def _refresh(client, token):
    return client.post("/auth/refresh", json={"refresh_token": token})


def test_refresh_token_stored_hashed_only(client, db_session):
    tokens = _login(client)
    stored = db_session.query(RefreshToken).one()
    assert stored.token_hash == hash_refresh_token(tokens["refresh_token"])
    assert tokens["refresh_token"] not in stored.token_hash


def test_rotation_keeps_family(client, db_session):
    tokens = _login(client)
    assert _refresh(client, tokens["refresh_token"]).status_code == 200
    rows = db_session.query(RefreshToken).order_by(RefreshToken.id).all()
    assert len(rows) == 2
    assert rows[0].family_id == rows[1].family_id
    assert [r.revoked for r in rows] == [True, False]


def test_reuse_revokes_whole_family(client):
    tokens = _login(client)
    rotated = _refresh(client, tokens["refresh_token"]).json()

    # Attacker (or buggy client) replays the already-rotated token.
    assert _refresh(client, tokens["refresh_token"]).status_code == 401

    # The legitimate newest token is now dead too.
    assert _refresh(client, rotated["refresh_token"]).status_code == 401


def test_reuse_does_not_affect_other_sessions(client):
    first = _login(client)
    second = _login(client)  # another device, separate family
    _refresh(client, first["refresh_token"])
    _refresh(client, first["refresh_token"])  # replay -> family 1 revoked
    assert _refresh(client, second["refresh_token"]).status_code == 200


def test_consume_is_single_use(db_session):
    from app.db.models.user import User

    user = User(name="u", email="u@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    repo = RefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    repo.create(user.id, "h", datetime(2999, 1, 1, tzinfo=UTC), "fam")

    assert repo.consume("h", now) is not None
    assert repo.consume("h", now) is None


def test_logout_revokes_family(client):
    tokens = _login(client)
    rotated = _refresh(client, tokens["refresh_token"]).json()
    response = client.post(
        "/auth/logout", json={"refresh_token": rotated["refresh_token"]}
    )
    assert response.status_code == 204
    assert _refresh(client, rotated["refresh_token"]).status_code == 401


def test_logout_unknown_token_is_noop(client):
    response = client.post("/auth/logout", json={"refresh_token": "nope"})
    assert response.status_code == 204


def test_logout_all_revokes_every_session(client):
    first = _login(client)
    second = _login(client)
    response = client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert response.status_code == 204
    assert _refresh(client, first["refresh_token"]).status_code == 401
    assert _refresh(client, second["refresh_token"]).status_code == 401


def test_logout_all_requires_auth(client):
    assert client.post("/auth/logout-all").status_code == 401


def test_refresh_rejected_for_inactive_user(client, db_session):
    from app.db.models.user import User

    tokens = _login(client)
    db_session.query(User).one().is_active = False
    db_session.commit()
    assert _refresh(client, tokens["refresh_token"]).status_code == 401
