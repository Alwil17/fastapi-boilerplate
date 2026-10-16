import os
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL, make_url

from app import __version__

PRODUCTION_ENVS = {"production", "prod", "staging"}
INSECURE_SECRET_KEYS = {
    "",
    "your-secret-key-here",
    "your-secret-key-change-this",
    "change-me",
    "secret",
    "test_secret_key",
}
MIN_SECRET_KEY_LENGTH = 32

# Chosen once at import: APP_ENV=test (set by pytest) reads .env.test instead of .env.
ENV_FILE = ".env.test" if os.getenv("APP_ENV") == "test" else ".env"


def _split_csv(value):
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("["):
            return value  # let pydantic parse it as JSON
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    # Application
    APP_NAME: str = "FastAPI Boilerplate"
    APP_DESCRIPTION: str = "FastAPI Boilerplate with clean architecture"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"
    APP_DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # HTTP (comma-separated lists, e.g. CORS_ORIGINS=https://a.com,https://b.com)
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    ALLOWED_HOSTS: Annotated[list[str], NoDecode] = ["*"]

    # Database
    DATABASE_URL: str | None = None  # full URL override (used by tests)
    DB_ENGINE: str = "postgresql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mydb"
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_SSLMODE: str = "prefer"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "fastapi-boilerplate"
    JWT_AUDIENCE: str = "fastapi-boilerplate-api"

    # Rate limiting (per client IP). Use a redis:// URI when running several workers.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE_URI: str = "memory://"
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_REFRESH: str = "30/minute"

    # Logging (json for production/log aggregators, console for local development)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # Sentry (error reporting is off unless a DSN is set)
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.0, ge=0.0, le=1.0)

    # Prometheus
    PROMETHEUS_ENABLED: bool = False
    # If set, GET /metrics requires 'Authorization: Bearer <token>'.
    METRICS_TOKEN: str | None = None

    @field_validator("LOG_LEVEL", "LOG_FORMAT", mode="before")
    @classmethod
    def _normalize_log_option(cls, value, info):
        if not isinstance(value, str):
            return value
        return value.upper() if info.field_name == "LOG_LEVEL" else value.lower()

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def _parse_csv(cls, value):
        return _split_csv(value)

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        if not self.is_production:
            return self
        problems = []
        if (
            self.APP_SECRET_KEY in INSECURE_SECRET_KEYS
            or len(self.APP_SECRET_KEY) < MIN_SECRET_KEY_LENGTH
        ):
            problems.append(
                f"APP_SECRET_KEY must be set to a random value of at least "
                f"{MIN_SECRET_KEY_LENGTH} characters"
            )
        if self.APP_DEBUG:
            problems.append("APP_DEBUG must be False")
        if "*" in self.CORS_ORIGINS:
            problems.append("CORS_ORIGINS must not contain '*'")
        if self.DATABASE_URL is None and self.DB_PASSWORD == "password":
            problems.append("DB_PASSWORD must not be the default value")
        if problems:
            raise ValueError(
                f"Unsafe configuration for APP_ENV={self.APP_ENV}: "
                + "; ".join(problems)
            )
        return self

    @property
    def APP_VERSION(self) -> str:
        return __version__

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in PRODUCTION_ENVS

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production

    def build_database_url(self) -> URL:
        if self.DATABASE_URL:
            return make_url(self.DATABASE_URL)
        is_postgres = self.DB_ENGINE.startswith("postgres")
        # Pin the driver: SQLAlchemy may default bare "postgresql" to psycopg (v3).
        drivername = (
            "postgresql+psycopg2" if self.DB_ENGINE == "postgresql" else self.DB_ENGINE
        )
        query = {"sslmode": self.DB_SSLMODE} if is_postgres else {}
        return URL.create(
            drivername=drivername,
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            query=query,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
