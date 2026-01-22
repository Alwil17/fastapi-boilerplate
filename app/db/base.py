from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models.base import Base
import app.db.models
from app.core.config import settings
import os

is_test = os.environ.get("APP_ENV") == "test"

if is_test:
    from app.core.config_test import test_settings
    SQLALCHEMY_DATABASE_URL = test_settings.DATABASE_URL
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    if settings.DB_ENGINE == "postgresql":
        url = URL.create(
            drivername="postgresql",
            username=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            database=settings.DB_NAME,
        )
        engine = create_engine(url, connect_args={"sslmode": "require"})
    else:
        DATABASE_URL = f"{settings.DB_ENGINE}://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    if settings.APP_DEBUG:
        Base.metadata.drop_all(bind=engine)
        print("DEBUG: flushing db")
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

init_db()
