import pytest
from pydantic import ValidationError

from app.core.config import Settings

GOOD_SECRET = "x" * 48


@pytest.fixture(autouse=True)
def _no_ambient_database_url(monkeypatch):
    # CI exports DATABASE_URL for the suite; Settings would read it and bypass the DB_* fields under test.
    monkeypatch.delenv("DATABASE_URL", raising=False)


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


def test_csv_settings_accept_a_json_list():
    s = make(CORS_ORIGINS='["https://a.example.com", "https://b.example.com"]')
    assert s.CORS_ORIGINS == ["https://a.example.com", "https://b.example.com"]


def test_csv_settings_accept_comma_separated_values():
    s = make(ALLOWED_HOSTS=" a.example.com , b.example.com ,")
    assert s.ALLOWED_HOSTS == ["a.example.com", "b.example.com"]


def test_log_options_are_normalised():
    s = make(LOG_LEVEL="warning", LOG_FORMAT="JSON")
    assert (s.LOG_LEVEL, s.LOG_FORMAT) == ("WARNING", "json")


def test_json_list_in_the_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://a.example.com"]')
    assert Settings(_env_file=None).CORS_ORIGINS == ["https://a.example.com"]
