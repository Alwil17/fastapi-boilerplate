from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Persistence for refresh tokens, addressed by the hash of the token.

    Mutations only flush; the caller owns the transaction (so a rotation is atomic)
    unless `commit=True` is requested.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        family_id: str,
        *,
        commit: bool = True,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            family_id=family_id,
        )
        self.db.add(refresh_token)
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(refresh_token)
        return refresh_token

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

    def consume(self, token_hash: str, now: datetime) -> RefreshToken | None:
        """Atomically revoke a token that is still valid and return it.

        One conditional UPDATE decides the winner, so two concurrent refreshes with the
        same token cannot both succeed. Returns None when the token is unknown,
        already revoked or expired. Does not commit.
        """
        result = self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
            .values(revoked=True)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            return None
        self.db.expire_all()
        return self.get_by_hash(token_hash)

    def revoke_family(self, family_id: str, *, commit: bool = True) -> int:
        return self._revoke(RefreshToken.family_id == family_id, commit)

    def revoke_all_for_user(self, user_id: int, *, commit: bool = True) -> int:
        return self._revoke(RefreshToken.user_id == user_id, commit)

    def _revoke(self, condition, commit: bool) -> int:
        result = self.db.execute(
            update(RefreshToken)
            .where(condition, RefreshToken.revoked.is_(False))
            .values(revoked=True)
            .execution_options(synchronize_session=False)
        )
        if commit:
            self.db.commit()
        return result.rowcount

    def delete_expired(self, now: datetime) -> int:
        """Delete every token (revoked or not) whose expiry is before `now`."""
        deleted = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.expires_at < now)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted
