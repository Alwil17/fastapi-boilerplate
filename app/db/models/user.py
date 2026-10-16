from sqlalchemy import Boolean, Column, DateTime, Integer, String, func, true
from sqlalchemy.orm import relationship

from app.db.models.base import Base

CASCADE_ALL_DELETE_ORPHAN = "all, delete-orphan"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role = Column(String(50), nullable=False, default="user", server_default="user")
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Add the relationship to RefreshToken
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade=CASCADE_ALL_DELETE_ORPHAN
    )

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
