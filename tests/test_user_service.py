from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import verify_password
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user_dto import UserCreateDTO, UserUpdateDTO
from app.services.user_service import UserService

PASSWORD = "Passw0rd!x"


def _create(service, email="a@example.com", name="A"):
    return service.create_user(UserCreateDTO(name=name, email=email, password=PASSWORD))


@pytest.fixture
def service(db_session):
    return UserService(db_session)


def test_create_user_hashes_the_password(service):
    user = _create(service)
    assert user.hashed_password != PASSWORD
    assert verify_password(PASSWORD, user.hashed_password)
    assert user.role == "user"
    assert user.is_active is True


def test_create_user_rejects_duplicate_email(service):
    _create(service)
    with pytest.raises(ValueError, match="already exists"):
        _create(service)


def test_authenticate_user(service):
    user = _create(service)
    assert service.authenticate_user("A@Example.com ", PASSWORD).id == user.id


@pytest.mark.parametrize(
    ("email", "password"),
    [("a@example.com", "wrong-password"), ("nobody@example.com", PASSWORD)],
)
def test_authenticate_user_rejects_bad_credentials(service, email, password):
    _create(service)
    assert service.authenticate_user(email, password) is None


def test_authenticate_user_rejects_inactive_account(service, db_session):
    user = _create(service)
    user.is_active = False
    db_session.commit()
    assert service.authenticate_user("a@example.com", PASSWORD) is None


def test_get_user_by_id(service):
    user = _create(service)
    assert service.get_user_by_id(user.id).email == "a@example.com"
    assert service.get_user_by_id(user.id + 1) is None


def test_update_user_changes_only_given_fields(service):
    user = _create(service)
    updated = service.update_user(user.id, UserUpdateDTO(name="Renamed"))
    assert updated.name == "Renamed"
    assert updated.email == "a@example.com"
    assert verify_password(PASSWORD, updated.hashed_password)


def test_update_user_rehashes_the_password(service):
    user = _create(service)
    updated = service.update_user(user.id, UserUpdateDTO(password="N3w-Passw0rd"))
    assert verify_password("N3w-Passw0rd", updated.hashed_password)
    assert not verify_password(PASSWORD, updated.hashed_password)


def test_update_unknown_user_returns_none(service):
    assert service.update_user(999, UserUpdateDTO(name="x")) is None


def test_delete_user_removes_its_refresh_tokens(service, db_session):
    user = _create(service)
    RefreshTokenRepository(db_session).create(
        user.id, "hash", datetime.now(UTC) + timedelta(days=1), "family"
    )

    assert service.delete_user(user.id) is True

    assert db_session.query(User).count() == 0
    assert db_session.query(RefreshToken).count() == 0


def test_delete_unknown_user_returns_false(service):
    assert service.delete_user(999) is False


def test_list_users_is_paginated(service):
    for i in range(3):
        _create(service, email=f"u{i}@example.com")
    assert [u.email for u in service.list_users(skip=1, limit=1)] == ["u1@example.com"]
