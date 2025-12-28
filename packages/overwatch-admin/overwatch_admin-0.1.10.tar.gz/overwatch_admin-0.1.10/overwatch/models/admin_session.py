"""
Overwatch Admin Session model for tracking active sessions.
"""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from overwatch.models.admin import Admin

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from overwatch.core.database import Base


class AdminSession(Base):
    """
    Admin session model for tracking active sessions.
    """

    __tablename__ = "overwatch_admin_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id: Mapped[int] = mapped_column(
        ForeignKey("overwatch_admins.id"), nullable=False, index=True
    )

    # Session information
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Request information
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv6 compatible
    user_agent: Mapped[str | None] = mapped_column(Text)

    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    admin: Mapped["Admin"] = relationship("Admin", back_populates="sessions")

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return bool(datetime.now(self.expires_at.tzinfo) > self.expires_at)

    def __repr__(self) -> str:
        return f"<AdminSession(id={self.id}, admin_id={self.admin_id}, active={self.is_active})>"
