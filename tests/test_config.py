import pytest
from pydantic import ValidationError

from app.core.config import Settings

GOOD_SECRET = "x" * 48


def make(**overrides):
    base = {
        "APP_ENV": "production",
        "APP_DEBUG": False,
        "APP_SECRET_KEY": GOOD_SECRET,
        "DB_PASSWORD": "a-real-password",
        "CORS_ORIGINS": ["https://app.example.com"],
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def test_production_with_safe_config_boots():
    s = make()
    assert s.is_production
    assert not s.docs_enabled


@pytest.mark.parametrize(
    "overrides",
    [
        {"APP_SECRET_KEY": "change-me"},
        {"APP_SECRET_KEY": "too-short"},
        {"APP_DEBUG": True},
        {"CORS_ORIGINS": ["*"]},
        {"DB_PASSWORD": "password"},
    ],
)
def test_production_refuses_unsafe_config(overrides):
    with pytest.raises(ValidationError):
        make(**overrides)


def test_development_allows_defaults():
    s = Settings(_env_file=None, APP_ENV="development")
    assert not s.is_production
    assert s.docs_enabled


def test_csv_lists_are_parsed():
    s = Settings(
        _env_file=None,
        CORS_ORIGINS="https://a.com, https://b.com",
        ALLOWED_HOSTS="a.com,b.com",
    )
    assert s.CORS_ORIGINS == ["https://a.com", "https://b.com"]
    assert s.ALLOWED_HOSTS == ["a.com", "b.com"]


def test_database_url_escapes_special_characters():
    s = Settings(_env_file=None, DB_PASSWORD="p@ss/word:1", DB_HOST="db")
    url = s.build_database_url()
    assert url.password == "p@ss/word:1"
    assert url.query["sslmode"] == "prefer"
    assert "p@ss/word" not in url.render_as_string(hide_password=False).split("@")[0]


def test_default_access_token_is_short_lived():
    assert Settings(_env_file=None).ACCESS_TOKEN_EXPIRE_MINUTES == 15
