from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
)

MIN_PASSWORD_LENGTH = 8
BCRYPT_MAX_BYTES = 72  # bcrypt cannot hash more; reject instead of silently truncating


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _check_password(value: str) -> str:
    if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError(f"Password must be at most {BCRYPT_MAX_BYTES} bytes")
    if not value.strip():
        raise ValueError("Password must not be blank")
    return value


Email = Annotated[EmailStr, Field(max_length=100), AfterValidator(_normalize_email)]
Password = Annotated[
    str,
    StringConstraints(min_length=MIN_PASSWORD_LENGTH, max_length=BCRYPT_MAX_BYTES),
    AfterValidator(_check_password),
]
Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class UserCreateDTO(BaseModel):
    name: Name
    email: Email
    password: Password


class UserUpdateDTO(BaseModel):
    name: Name | None = None
    email: Email | None = None
    password: Password | None = None


class UserResponse(BaseModel):
    id: int
    name: str | None = None
    email: EmailStr
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
