import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_refresh_token, hash_refresh_token
from app.db.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class InvalidRefreshToken(Exception):
    """Refresh token unknown, revoked, or its user is gone/inactive."""


class RefreshTokenExpired(InvalidRefreshToken):
    pass


def _new_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


class TokenService:
    def __init__(self, db: Session):
        self.db = db
        self.tokens = RefreshTokenRepository(db)
        self.users = UserRepository(db)

    def issue(self, user_id: int) -> str:
        """Start a new token family (a login) and return the raw refresh token."""
        raw = generate_refresh_token()
        self.tokens.create(
            user_id, hash_refresh_token(raw), _new_expiry(), uuid.uuid4().hex
        )
        return raw

    def rotate(self, raw_token: str) -> tuple[User, str]:
        """Exchange a refresh token for a new one; the old one is single-use.

        Presenting a token that was already used (or revoked) means it may have been
        stolen, so its whole family is revoked and the holder must log in again.
        Revoking the old token and storing the new one commit as one transaction.
        """
        token_hash = hash_refresh_token(raw_token)
        stored = self.tokens.consume(token_hash, datetime.now(UTC))

        if stored is None:
            self._reject(token_hash)

        user = self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            self.tokens.revoke_family(stored.family_id)
            raise InvalidRefreshToken("Invalid refresh token")

        new_raw = generate_refresh_token()
        self.tokens.create(
            user.id,
            hash_refresh_token(new_raw),
            _new_expiry(),
            stored.family_id,
            commit=False,
        )
        self.db.commit()
        return user, new_raw

    def revoke(self, raw_token: str) -> None:
        """Logout: revoke the token's whole family. Unknown tokens are ignored."""
        existing = self.tokens.get_by_hash(hash_refresh_token(raw_token))
        if existing:
            self.tokens.revoke_family(existing.family_id)

    def revoke_all(self, user_id: int) -> int:
        return self.tokens.revoke_all_for_user(user_id)

    def _reject(self, token_hash: str):
        existing = self.tokens.get_by_hash(token_hash)
        if existing is None:
            raise InvalidRefreshToken("Invalid refresh token")
        if existing.revoked:
            logger.warning(
                "Refresh token reuse detected, revoking family",
                extra={"user_id": existing.user_id, "family_id": existing.family_id},
            )
            self.tokens.revoke_family(existing.family_id)
            raise InvalidRefreshToken("Invalid refresh token")
        raise RefreshTokenExpired("Refresh token expired")
