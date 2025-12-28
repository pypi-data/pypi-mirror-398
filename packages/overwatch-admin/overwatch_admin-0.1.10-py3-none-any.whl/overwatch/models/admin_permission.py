"""
Overwatch Admin Permission model for fine-grained permissions.
"""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from overwatch.models.admin import Admin

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from overwatch.core.database import Base


class AdminPermission(Base):
    """
    Admin permission model for fine-grained permissions.
    """

    __tablename__ = "overwatch_admin_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id: Mapped[int] = mapped_column(
        ForeignKey("overwatch_admins.id"), nullable=False, index=True
    )

    # Permission details
    resource: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "User", "Product"
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., "read", "write", "delete"
    resource_id: Mapped[int | None] = mapped_column(
        Integer
    )  # Specific resource ID, null for global

    # Permission status
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    granted_by: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    admin: Mapped["Admin"] = relationship("Admin", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<AdminPermission(admin_id={self.admin_id}, resource='{self.resource}', action='{self.action}')>"
