from sqlalchemy import inspect
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db import base


def test_in_memory_sqlite_shares_one_connection(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite://")
    engine = base._create_engine()
    assert isinstance(engine.pool, StaticPool)


def test_file_sqlite_does_not_use_the_shared_connection(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 'app.db'}")
    engine = base._create_engine()
    assert not isinstance(engine.pool, StaticPool)


def test_postgres_engine_uses_the_configured_pool(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    monkeypatch.setattr(settings, "DB_POOL_SIZE", 3)
    monkeypatch.setattr(settings, "DB_MAX_OVERFLOW", 7)
    monkeypatch.setattr(settings, "DB_POOL_TIMEOUT", 11)
    engine = base._create_engine()  # lazy: opens no connection
    assert engine.pool.size() == 3
    assert engine.pool._max_overflow == 7
    assert engine.pool._timeout == 11
    assert engine.pool._pre_ping is True
    assert engine.dialect.driver == "psycopg2"


def test_init_db_creates_missing_tables_without_dropping_data(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 'app.db'}")
    engine = base._create_engine()
    monkeypatch.setattr(base, "engine", engine)

    base.init_db()
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO users (email, hashed_password) VALUES ('a@b.c', 'x')"
        )
    base.init_db()  # second run must keep the row

    assert {"users", "refresh_tokens"} <= set(inspect(engine).get_table_names())
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT count(*) FROM users").scalar() == 1


def test_get_db_closes_the_session(monkeypatch):
    closed = []

    class Session:
        def close(self):
            closed.append(True)

    monkeypatch.setattr(base, "SessionLocal", Session)
    gen = base.get_db()
    assert isinstance(next(gen), Session)
    gen.close()
    assert closed == [True]
