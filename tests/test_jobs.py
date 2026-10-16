from datetime import UTC, datetime, timedelta

import pytest

from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.jobs import create_admin, purge_refresh_tokens
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user_dto import UserCreateDTO
from app.services.user_service import UserService
from tests.conftest import TestingSessionLocal


@pytest.fixture
def job_db(db_session, monkeypatch):
    """Point the jobs' own session factory at the per-test database."""
    monkeypatch.setattr(create_admin, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(purge_refresh_tokens, "SessionLocal", TestingSessionLocal)
    return db_session


def test_purge_job_deletes_only_expired_tokens(job_db, capsys):
    user = UserService(job_db).create_user(
        UserCreateDTO(name="U", email="u@example.com", password="Passw0rd!x")
    )
    repo = RefreshTokenRepository(job_db)
    now = datetime.now(UTC)
    repo.create(user.id, "old", now - timedelta(days=1), "fam")
    repo.create(user.id, "new", now + timedelta(days=1), "fam")

    assert purge_refresh_tokens.main() == 1

    assert [t.token_hash for t in job_db.query(RefreshToken)] == ["new"]
    assert "Deleted 1 expired refresh token(s)" in capsys.readouterr().out


def test_create_admin_creates_the_account(job_db, monkeypatch, capsys):
    monkeypatch.setenv("ADMIN_PASSWORD", "Passw0rd!x")

    assert create_admin.main(["Boss@Example.com"]) == 0

    job_db.expire_all()
    boss = job_db.query(User).one()
    assert (boss.email, boss.role, boss.name) == ("boss@example.com", "admin", "Admin")
    assert "Admin ready: boss@example.com" in capsys.readouterr().out


def test_create_admin_promotes_an_existing_user(job_db, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "Passw0rd!x")
    create_admin.create_admin("user@example.com", "Passw0rd!x", name="Regular")
    job_db.query(User).one().role = "user"
    job_db.commit()

    create_admin.main(["user@example.com"])

    job_db.expire_all()
    assert job_db.query(User).count() == 1
    assert job_db.query(User).one().role == "admin"


def test_create_admin_prompts_when_no_password_in_env(job_db, monkeypatch):
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.setattr(create_admin.getpass, "getpass", lambda _: "Passw0rd!x")

    create_admin.main(["prompted@example.com", "--name", "Prompted"])

    job_db.expire_all()
    assert job_db.query(User).one().name == "Prompted"
