"""
Overwatch Organization model for multi-tenant admin support.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

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
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from overwatch.core.database import Base


class OrganizationStatus(str, enum.Enum):
    """Organization status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Organization(Base):
    """
    Organization model for multi-tenant admin support.

    Allows segmentation of admin access by organization with hierarchical permissions.
    """

    __tablename__ = "overwatch_organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Organization details
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text)

    # Contact information
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(255))

    # Address information
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))

    # Organization settings
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Hierarchical organization support
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("overwatch_organizations.id"), index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=0)  # 0 = root level

    # Organization-specific settings
    settings: Mapped[str | None] = mapped_column(
        Text
    )  # JSON string for flexible settings
    allowed_domains: Mapped[str | None] = mapped_column(
        Text
    )  # JSON array of allowed email domains

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
    parent: Mapped["Organization"] = relationship(
        "Organization", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Organization"]] = relationship(
        "Organization", back_populates="parent", cascade="all, delete-orphan"
    )
    admins: Mapped[list["Admin"]] = relationship(
        "Admin", back_populates="organization", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get organization full name with parent hierarchy."""
        if self.parent:
            parent_name = str(self.parent.name) if self.parent.name else ""
            return f"{parent_name} > {self.name}"
        return str(self.name)

    @property
    def is_active_organization(self) -> bool:
        """Check if organization is active."""
        return bool(self.is_active and self.status == OrganizationStatus.ACTIVE)

    def has_domain_access(self, email: str) -> bool:
        """Check if email domain is allowed for this organization."""
        if not self.allowed_domains:
            return True  # No restrictions

        import json

        try:
            allowed_domains = json.loads(str(self.allowed_domains))
            email_domain = email.split("@")[-1].lower()
            return email_domain in allowed_domains
        except (json.JSONDecodeError, IndexError):
            return True  # If parsing fails, allow access

    def get_setting(self, key: str, default=None):
        """Get organization setting by key."""
        if not self.settings:
            return default

        import json

        try:
            settings = json.loads(str(self.settings))
            return settings.get(key, default)
        except json.JSONDecodeError:
            return default

    def set_setting(self, key: str, value) -> None:
        """Set organization setting by key."""
        import json

        settings = {}
        if self.settings:
            try:
                settings = json.loads(str(self.settings))
            except json.JSONDecodeError:
                settings = {}

        settings[key] = value
        self.settings = json.dumps(settings)

    def __repr__(self) -> str:
        return (
            f"<Organization(id={self.id}, name='{self.name}', status='{self.status}')>"
        )


# Event listeners for organization model
@event.listens_for(Organization, "before_insert")
def set_organization_defaults(mapper, connection, target):
    """Set default values for organization before insert."""
    if not target.slug:
        # Generate slug from name
        import re

        slug = re.sub(r"[^a-zA-Z0-9\s-]", "", target.name).strip()
        slug = re.sub(r"[-\s]+", "-", slug).lower()
        target.slug = slug

    if target.parent_id:
        # Set level based on parent
        from sqlalchemy import select

        result = connection.execute(
            select(Organization).where(Organization.id == target.parent_id)
        )
        parent = result.scalar_one_or_none()
        if parent:
            target.level = parent.level + 1


@event.listens_for(Organization, "before_update")
def update_organization_timestamp(mapper, connection, target):
    """Update timestamp when organization is modified."""
    target.updated_at = func.now()
