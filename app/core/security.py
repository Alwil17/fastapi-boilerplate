from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
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
BCRYPT_MAX_BYTES = 72  # bcrypt ignores/rejects anything beyond 72 bytes


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserResponse:
    try:
        payload = jwt.decode(
            token, settings.APP_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_exception
    return UserResponse.model_validate(user)


def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return bcrypt.hashpw(
        password.encode("utf-8")[:BCRYPT_MAX_BYTES], bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES],
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JSON Web Token (JWT) access token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str):
    """Verify a JWT token and return the username if valid."""
    try:
        payload = jwt.decode(
            token, settings.APP_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError as e:
        raise credentials_exception from e
