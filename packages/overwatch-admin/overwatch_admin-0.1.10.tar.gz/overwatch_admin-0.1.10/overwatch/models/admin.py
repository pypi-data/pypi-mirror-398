"""
Overwatch Admin model for authentication and authorization.
"""

import enum
import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from overwatch.models.admin_permission import AdminPermission
    from overwatch.models.admin_session import AdminSession
    from overwatch.models.audit_log import AuditLog
    from overwatch.models.organization import Organization

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from overwatch.core.database import Base


class OverwatchAdminRole(str, enum.Enum):
    """Overwatch admin role enumeration."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    READ_ONLY = "read_only"


class OverwatchAdminStatus(str, enum.Enum):
    """Overwatch admin status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Admin(Base):
    """
    Overwatch Admin model for authentication and authorization.

    This is completely separate from the host application's user system.
    """

    __tablename__ = "overwatch_admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Admin information
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))

    # Role and permissions
    role: Mapped[OverwatchAdminRole] = mapped_column(
        Enum(OverwatchAdminRole), default=OverwatchAdminRole.ADMIN
    )
    status: Mapped[OverwatchAdminStatus] = mapped_column(
        Enum(OverwatchAdminStatus), default=OverwatchAdminStatus.ACTIVE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Security fields
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Two-factor authentication
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    two_factor_secret: Mapped[str | None] = mapped_column(String(255))
    backup_codes: Mapped[str | None] = mapped_column(Text)  # JSON string

    # Session management
    session_token: Mapped[str | None] = mapped_column(String(255))  # Current session
    refresh_token: Mapped[str | None] = mapped_column(
        String(255)
    )  # Current refresh token

    # Organization assignment
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("overwatch_organizations.id"), index=True
    )

    # Permissions (JSON field for custom permissions)
    custom_permissions: Mapped[str | None] = mapped_column(Text)  # JSON string

    # Organization-scoped permissions (JSON field)
    organization_permissions: Mapped[str | None] = mapped_column(Text)  # JSON string

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(Integer)
    updated_by: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="admins"
    )
    sessions: Mapped[list["AdminSession"]] = relationship(
        "AdminSession", back_populates="admin", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="admin", cascade="all, delete-orphan"
    )
    permissions: Mapped[list["AdminPermission"]] = relationship(
        "AdminPermission", back_populates="admin", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get admin's full name."""
        if self.first_name and self.last_name:
            return str(f"{self.first_name} {self.last_name}")
        return str(self.username)

    @property
    def is_locked(self) -> bool:
        """Check if admin account is locked."""
        if self.locked_until is None:
            return False
        return bool(self.locked_until > datetime.now(self.locked_until.tzinfo))

    @property
    def can_login(self) -> bool:
        """Check if admin can login."""
        return bool(
            self.is_active
            and self.status == OverwatchAdminStatus.ACTIVE
            and not self.is_locked
        )

    def has_permission(
        self,
        permission: str,
        resource_id: int | None = None,
        organization_id: int | None = None,
    ) -> bool:
        """
        Check if admin has a specific permission.

        Args:
            permission: Permission string (e.g., "read:user", "write:product")
            resource_id: Optional specific resource ID for fine-grained control
            organization_id: Optional organization ID for organization-scoped permissions

        Returns:
            True if admin has permission, False otherwise
        """
        # Super admins have all permissions
        if self.role == OverwatchAdminRole.SUPER_ADMIN:
            return True

        # Parse permission string
        parts = permission.split(":")
        if len(parts) != 2:
            return False

        action, resource = parts

        # Check organization access first
        if (
            organization_id
            and self.organization_id
            and self.organization_id != organization_id
        ):
            # Admin can only access their own organization unless super admin
            return False

        # Read-only admins only have read permissions
        if self.role == OverwatchAdminRole.READ_ONLY and action != "read":
            return False

        # Check custom permissions if set
        if self.custom_permissions:
            try:
                custom_perms = json.loads(str(self.custom_permissions))
                allowed_permissions = custom_perms.get("allowed", [])
                if permission in allowed_permissions:
                    return True
            except (json.JSONDecodeError, AttributeError):
                pass

        # Check organization-scoped permissions
        if organization_id and self.organization_permissions:
            try:
                org_perms = json.loads(str(self.organization_permissions))
                org_specific_perms = org_perms.get(str(organization_id), {})
                allowed_org_permissions = org_specific_perms.get("allowed", [])
                if permission in allowed_org_permissions:
                    return True
            except (json.JSONDecodeError, AttributeError):
                pass

        # Check database permissions for this admin
        # This would need to be implemented with a database query in the service layer
        # For now, return default role-based permissions

        # Regular admins have standard permissions within their organization
        if self.role == OverwatchAdminRole.ADMIN:
            # Allow basic CRUD operations for common resources
            basic_resources = ["admin", "audit", "config", "dashboard"]
            if resource in basic_resources:
                return True

            # Allow read access to all resources
            if action == "read":
                return True

        return False

    def can_access_organization(self, organization_id: int) -> bool:
        """
        Check if admin can access a specific organization.

        Args:
            organization_id: Organization ID to check

        Returns:
            True if admin can access organization, False otherwise
        """
        # Super admins can access all organizations
        if self.role == OverwatchAdminRole.SUPER_ADMIN:
            return True

        # Admin can access their own organization
        if self.organization_id == organization_id:
            return True

        # Check if they have explicit organization permissions
        if self.organization_permissions:
            try:
                org_perms = json.loads(str(self.organization_permissions))
                return str(organization_id) in org_perms
            except (json.JSONDecodeError, AttributeError):
                pass

        return False

    def get_organization_permissions(self, organization_id: int) -> dict:
        """
        Get permissions for a specific organization.

        Args:
            organization_id: Organization ID

        Returns:
            Dictionary of organization-specific permissions
        """
        if not self.organization_permissions:
            return {}

        try:
            org_perms = json.loads(str(self.organization_permissions))
            return org_perms.get(str(organization_id), {})
        except (json.JSONDecodeError, AttributeError):
            return {}

    def set_organization_permission(
        self, organization_id: int, permissions: list[str]
    ) -> None:
        """
        Set permissions for a specific organization.

        Args:
            organization_id: Organization ID
            permissions: List of permission strings
        """
        import json

        org_perms = {}
        if self.organization_permissions:
            try:
                org_perms = json.loads(str(self.organization_permissions))
            except (json.JSONDecodeError, AttributeError):
                org_perms = {}

        org_perms[str(organization_id)] = {"allowed": permissions}
        self.organization_permissions = json.dumps(org_perms)

    def remove_organization_permission(self, organization_id: int) -> None:
        """
        Remove permissions for a specific organization.

        Args:
            organization_id: Organization ID
        """
        import json

        if not self.organization_permissions:
            return

        try:
            org_perms = json.loads(str(self.organization_permissions))
            if str(organization_id) in org_perms:
                del org_perms[str(organization_id)]
            self.organization_permissions = json.dumps(org_perms)
        except (json.JSONDecodeError, AttributeError):
            pass

    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, username='{self.username}', role='{self.role}')>"


# Event listeners for admin model
@event.listens_for(Admin, "before_insert")
def set_admin_defaults(mapper, connection, target):
    """Set default values for admin before insert."""
    if not target.first_name and not target.last_name:
        target.first_name = target.username


@event.listens_for(Admin, "before_update")
def update_admin_timestamp(mapper, connection, target):
    """Update timestamp when admin is modified."""
    target.updated_at = func.now()
