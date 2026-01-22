from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.models.base import Base

CASCADE_ALL_DELETE_ORPHAN = "all, delete-orphan"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    # Add the relationship to RefreshToken
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade=CASCADE_ALL_DELETE_ORPHAN
    )

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
