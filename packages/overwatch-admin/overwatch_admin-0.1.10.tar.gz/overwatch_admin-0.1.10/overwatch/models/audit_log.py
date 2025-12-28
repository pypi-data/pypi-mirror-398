"""
Overwatch Audit Log model for tracking admin actions.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from overwatch.models.admin import Admin

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from overwatch.core.database import Base


class OverwatchAuditAction(str, enum.Enum):
    """Overwatch audit action enumeration."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    BULK_CREATE = "bulk_create"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"
    EXPORT = "export"
    IMPORT = "import"


class AuditLog(Base):
    """
    Audit log model for tracking all admin actions.
    """

    __tablename__ = "overwatch_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("overwatch_admins.id"), index=True
    )

    # Action details
    action: Mapped[OverwatchAuditAction] = mapped_column(
        Enum(OverwatchAuditAction), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "User", "Product"
    resource_id: Mapped[int | None] = mapped_column(
        Integer
    )  # ID of the affected resource

    # Request information
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv6 compatible
    user_agent: Mapped[str | None] = mapped_column(Text)

    # Change details
    old_values: Mapped[str | None] = mapped_column(Text)  # JSON string of old values
    new_values: Mapped[str | None] = mapped_column(Text)  # JSON string of new values
    changes_summary: Mapped[str | None] = mapped_column(Text)  # Human-readable summary

    # Status and metadata
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Additional metadata (JSON string for flexibility)
    extra_metadata: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    admin: Mapped["Admin"] = relationship("Admin", back_populates="audit_logs")

    @property
    def action_display(self) -> str:
        """Get human-readable action display."""
        action_names = {
            OverwatchAuditAction.CREATE: "Created",
            OverwatchAuditAction.READ: "Viewed",
            OverwatchAuditAction.UPDATE: "Updated",
            OverwatchAuditAction.DELETE: "Deleted",
            OverwatchAuditAction.LOGIN: "Logged In",
            OverwatchAuditAction.LOGOUT: "Logged Out",
            OverwatchAuditAction.BULK_CREATE: "Bulk Created",
            OverwatchAuditAction.BULK_UPDATE: "Bulk Updated",
            OverwatchAuditAction.BULK_DELETE: "Bulk Deleted",
            OverwatchAuditAction.EXPORT: "Exported",
            OverwatchAuditAction.IMPORT: "Imported",
        }
        # Cast to OverwatchAuditAction to satisfy type checker
        action_value = cast(OverwatchAuditAction, self.action)
        return action_names.get(action_value, str(action_value))

    @property
    def resource_display(self) -> str:
        """Get human-readable resource display."""
        if self.resource_id:
            resource_type_value = cast(str, self.resource_type)
            return f"{resource_type_value} #{self.resource_id}"
        resource_type_value = cast(str, self.resource_type)
        return resource_type_value

    def get_changes_summary(self) -> str:
        """Get a human-readable summary of changes."""
        changes_summary_value = cast(str | None, self.changes_summary)
        if changes_summary_value:
            return changes_summary_value

        # Generate summary from old and new values
        import json

        try:
            old_values_value = cast(str | None, self.old_values)
            new_values_value = cast(str | None, self.new_values)

            old_data = json.loads(old_values_value) if old_values_value else {}
            new_data = json.loads(new_values_value) if new_values_value else {}

            changes = []
            for key, new_value in new_data.items():
                old_value = old_data.get(key)
                if old_value != new_value:
                    changes.append(f"{key}: {old_value} → {new_value}")

            return "; ".join(changes) if changes else "No changes detected"
        except (json.JSONDecodeError, TypeError):
            return "Unable to parse changes"

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', resource='{self.resource_type}')>"
