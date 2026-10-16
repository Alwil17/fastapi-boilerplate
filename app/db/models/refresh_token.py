from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    false,
    func,
)
from sqlalchemy.orm import relationship

from app.db.models.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    # SHA-256 hex of the opaque token handed to the client; the raw token is never stored.
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    # All tokens descending from one login share a family, so a replayed (already
    # rotated) token can revoke the whole chain.
    family_id = Column(String(32), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False, server_default=false())
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Add the back-reference to User
    user = relationship("User", back_populates="refresh_tokens")

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
