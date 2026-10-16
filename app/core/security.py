import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.user_dto import UserResponse

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
ACCESS_TOKEN_TYPE = "access"
BCRYPT_MAX_BYTES = 72  # bcrypt ignores/rejects anything beyond 72 bytes


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserResponse:
    user_id = decode_access_token(token)
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return UserResponse.model_validate(user)


def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return bcrypt.hashpw(
        password.encode("utf-8")[:BCRYPT_MAX_BYTES], bcrypt.gensalt()
    ).decode("utf-8")


# Verified against when the account does not exist, so login timing does not reveal it.
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES],
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def generate_refresh_token() -> str:
    """Opaque, high-entropy refresh token. Only its hash is persisted."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    # Plain SHA-256 is enough: the input is 384 random bits, not a guessable password.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token for `subject` (the user id)."""
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now
        + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        "jti": uuid.uuid4().hex,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    return jwt.encode(
        payload, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> int:
    """Validate an access token and return the user id it was issued for."""
    try:
        payload = jwt.decode(
            token,
            settings.APP_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "jti", "iss", "aud"]},
        )
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            raise credentials_exception
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError) as e:
        raise credentials_exception from e
