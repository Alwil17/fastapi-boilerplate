from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401  (register models on Base.metadata)
from app.core.config import settings
from app.db.models.base import Base


def _create_engine():
    url = settings.build_database_url()

    if url.get_backend_name() == "sqlite":
        kwargs = {"connect_args": {"check_same_thread": False}}
        if url.database in (None, "", ":memory:"):
            # One shared connection, otherwise every connection sees its own empty DB.
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)

    return create_engine(
        url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    # Non-destructive dev convenience only. Production schema is managed by Alembic.
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dev-only: create missing tables. Never drops data. Use Alembic migrations in production.
if settings.APP_DEBUG and settings.APP_ENV != "test" and not settings.is_production:
    init_db()
