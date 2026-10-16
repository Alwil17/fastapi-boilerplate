from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def _encode(**overrides):
    now = datetime.now(UTC)
    payload = {
        "sub": "1",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "jti": "abc",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    payload.update(overrides)
    payload = {k: v for k, v in payload.items() if v is not None}
    return jwt.encode(
        payload, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def test_access_token_roundtrip():
    assert decode_access_token(create_access_token("42")) == 42


def test_access_token_has_unique_jti():
    def jti(token):
        return jwt.decode(token, options={"verify_signature": False})["jti"]

    assert jti(create_access_token("1")) != jti(create_access_token("1"))


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": datetime.now(UTC) - timedelta(seconds=5)},
        {"type": "refresh"},
        {"aud": "someone-else"},
        {"iss": "someone-else"},
        {"sub": "not-an-int"},
        {"sub": None},
        {"jti": None},
    ],
)
def test_invalid_access_tokens_rejected(overrides):
    with pytest.raises(HTTPException) as exc:
        decode_access_token(_encode(**overrides))
    assert exc.value.status_code == 401


def test_token_signed_with_other_key_rejected():
    forged = jwt.encode({"sub": "1"}, "x" * 40, algorithm="HS256")
    with pytest.raises(HTTPException):
        decode_access_token(forged)


def test_alg_none_token_rejected():
    forged = jwt.encode({"sub": "1"}, None, algorithm="none")
    with pytest.raises(HTTPException):
        decode_access_token(forged)


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("other", hashed)


def test_verify_password_rejects_a_malformed_hash():
    assert verify_password("whatever", "not-a-bcrypt-hash") is False
