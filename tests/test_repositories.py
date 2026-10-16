from datetime import UTC, datetime, timedelta

from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_dto import UserCreateDTO


def _make_users(db, count):
    repo = UserRepository(db)
    return [
        repo.create(
            UserCreateDTO(
                name=f"u{i}", email=f"u{i}@example.com", password="Passw0rd!x"
            )
        )
        for i in range(count)
    ]


def test_list_users_is_paginated_and_ordered(db_session):
    users = _make_users(db_session, 5)
    repo = UserRepository(db_session)

    page = repo.list(skip=1, limit=2)

    assert [u.id for u in page] == [users[1].id, users[2].id]
    assert len(repo.list()) == 5


def test_delete_expired_removes_only_expired_tokens(db_session):
    user = _make_users(db_session, 1)[0]
    repo = RefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    repo.create(user.id, "expired", now - timedelta(days=1))
    repo.create(user.id, "valid", now + timedelta(days=1))

    deleted = repo.delete_expired(now)

    assert deleted == 1
    assert repo.get_by_token("expired") is None
    assert repo.get_by_token("valid") is not None
