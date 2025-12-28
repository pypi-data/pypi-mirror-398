"""
Organization service for organization management.
"""

from typing import Any

from fastapi import Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.models.organization import Organization
from overwatch.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)


class OrganizationService:
    """Service for organization management."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize organization service.

        Args:
            db_session: Database session
        """
        self.db_session = db_session

    async def get_organizations_paginated(
        self,
        page: int = 1,
        per_page: int = 25,
        search: str | None = None,
        org_status: str | None = None,
        is_active: bool | None = None,
        level: int | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> tuple[list[Organization], int]:
        """
        Get organizations with pagination and filtering.

        Args:
            page: Page number
            per_page: Items per page
            search: Search query
            org_status: Filter by status
            is_active: Filter by active status
            level: Filter by level
            sort_by: Sort field
            sort_direction: Sort direction

        Returns:
            Tuple of (organizations list, total count)
        """
        query = select(Organization)

        # Apply filters
        conditions = []
        if search:
            search_condition = or_(
                Organization.name.ilike(f"%{search}%"),
                Organization.slug.ilike(f"%{search}%"),
                Organization.description.ilike(f"%{search}%"),
            )
            conditions.append(search_condition)

        if org_status:
            conditions.append(Organization.status == org_status)

        if is_active is not None:
            conditions.append(Organization.is_active == is_active)

        if level is not None:
            conditions.append(Organization.level == level)

        if conditions:
            from sqlalchemy import and_

            query = query.where(and_(*conditions))

        # Get total count with same filters
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db_session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if hasattr(Organization, sort_by):
            sort_column = getattr(Organization, sort_by)
            if sort_direction == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column)
        else:
            # Fallback to created_at if invalid sort field
            if sort_direction == "desc":
                query = query.order_by(Organization.created_at.desc())
            else:
                query = query.order_by(Organization.created_at.asc())

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await self.db_session.execute(query)
        organizations = result.scalars().all()

        return list(organizations), total

    async def get_organization_stats(self) -> dict[str, Any]:
        """
        Get organization statistics optimized with single query.

        Returns:
            Dictionary with organization statistics
        """
        # Use a single query with conditional aggregation for better performance
        stats_query = select(
            func.count(Organization.id).label("total"),
            func.sum(func.case((Organization.status == "active", 1), else_=0)).label(
                "active"
            ),
            func.sum(func.case((Organization.status == "inactive", 1), else_=0)).label(
                "inactive"
            ),
            func.sum(func.case((Organization.status == "suspended", 1), else_=0)).label(
                "suspended"
            ),
        )

        result = await self.db_session.execute(stats_query)
        stats_row = result.first()

        # Get organizations by level in a single query
        level_query = (
            select(Organization.level, func.count(Organization.id).label("count"))
            .group_by(Organization.level)
            .order_by(Organization.level)
        )

        level_result = await self.db_session.execute(level_query)
        organizations_by_level = {row.level: row.count for row in level_result.all()}

        return {
            "total_organizations": (stats_row.total if stats_row else 0) or 0,
            "active_organizations": (stats_row.active if stats_row else 0) or 0,
            "inactive_organizations": (stats_row.inactive if stats_row else 0) or 0,
            "suspended_organizations": (stats_row.suspended if stats_row else 0) or 0,
            "organizations_by_level": organizations_by_level,
        }

    async def get_organization_by_id(self, organization_id: int) -> Organization | None:
        """
        Get organization by ID.

        Args:
            organization_id: Organization ID

        Returns:
            Organization object or None
        """
        result = await self.db_session.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        return result.scalar_one_or_none()

    async def create_organization(
        self,
        organization_data: OrganizationCreate,
        created_by: int | None = None,
    ) -> Organization:
        """
        Create new organization.

        Args:
            organization_data: Organization creation data
            created_by: ID of admin who created this organization

        Returns:
            Created organization object
        """
        # Check if slug already exists
        existing = await self.db_session.execute(
            select(Organization).where(Organization.slug == organization_data.slug)
        )
        if existing.scalar_one_or_none():
            raise ValueError(
                f"Organization with slug '{organization_data.slug}' already exists"
            )

        # Create organization
        organization = Organization(
            name=organization_data.name,
            slug=organization_data.slug,
            description=organization_data.description,
            level=organization_data.level,
            is_active=organization_data.is_active,
            parent_id=organization_data.parent_id,
            created_by=created_by,
        )

        self.db_session.add(organization)
        await self.db_session.commit()
        await self.db_session.refresh(organization)

        return organization

    async def update_organization(
        self,
        organization_id: int,
        organization_data: OrganizationUpdate,
        updated_by: int | None = None,
    ) -> Organization:
        """
        Update organization.

        Args:
            organization_id: Organization ID
            organization_data: Organization update data
            updated_by: ID of admin who made the update

        Returns:
            Updated organization object
        """
        organization = await self.get_organization_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Update fields
        updates = organization_data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(organization, field, value)

        organization.updated_by = updated_by

        await self.db_session.commit()
        await self.db_session.refresh(organization)

        return organization

    async def delete_organization(self, organization_id: int) -> bool:
        """
        Delete organization.

        Args:
            organization_id: Organization ID

        Returns:
            True if deleted, False if not found
        """
        organization = await self.get_organization_by_id(organization_id)
        if not organization:
            return False

        await self.db_session.delete(organization)
        await self.db_session.commit()

        return True

    async def bulk_create_organizations(
        self,
        organizations_data: list[OrganizationCreate],
        created_by: int | None = None,
    ) -> list[Organization]:
        """
        Create multiple organizations.

        Args:
            organizations_data: List of organization creation data
            created_by: ID of admin who created these organizations

        Returns:
            List of created organization objects
        """
        organizations = []

        # Check for duplicate slugs first
        slugs = [org.slug for org in organizations_data]
        existing_result = await self.db_session.execute(
            select(Organization.slug).where(Organization.slug.in_(slugs))
        )
        existing_slugs = {row.slug for row in existing_result.all()}

        duplicate_slugs = [slug for slug in slugs if slug in existing_slugs]
        if duplicate_slugs:
            raise ValueError(
                f"Organizations with slugs already exist: {duplicate_slugs}"
            )

        try:
            for org_data in organizations_data:
                organization = Organization(
                    name=org_data.name,
                    slug=org_data.slug,
                    description=org_data.description,
                    level=org_data.level,
                    is_active=org_data.is_active,
                    parent_id=org_data.parent_id,
                    created_by=created_by,
                )
                self.db_session.add(organization)
                organizations.append(organization)

            await self.db_session.commit()

            # Refresh all organizations
            for org in organizations:
                await self.db_session.refresh(org)

        except Exception as e:
            await self.db_session.rollback()
            raise ValueError(f"Failed to create organizations: {str(e)}") from e

        return organizations

    async def bulk_update_organizations(
        self,
        organization_ids: list[int],
        updates: OrganizationUpdate,
        updated_by: int | None = None,
    ) -> list[Organization]:
        """
        Update multiple organizations.

        Args:
            organization_ids: List of organization IDs
            updates: Update data to apply to all organizations
            updated_by: ID of admin who made the update

        Returns:
            List of updated organization objects
        """
        # Get all organizations first
        result = await self.db_session.execute(
            select(Organization).where(Organization.id.in_(organization_ids))
        )
        organizations = result.scalars().all()

        if not organizations:
            return []

        # Apply updates to all organizations
        update_data = updates.model_dump(exclude_unset=True)
        for organization in organizations:
            for field, value in update_data.items():
                setattr(organization, field, value)
            organization.updated_by = updated_by

        try:
            await self.db_session.commit()

            # Refresh all organizations
            for org in organizations:
                await self.db_session.refresh(org)

        except Exception as e:
            await self.db_session.rollback()
            raise ValueError(f"Failed to update organizations: {str(e)}") from e

        return list(organizations)

    async def bulk_delete_organizations(self, organization_ids: list[int]) -> int:
        """
        Delete multiple organizations.

        Args:
            organization_ids: List of organization IDs

        Returns:
            Number of deleted organizations
        """
        # Get organizations to delete first for counting
        result = await self.db_session.execute(
            select(Organization).where(Organization.id.in_(organization_ids))
        )
        organizations = result.scalars().all()

        if not organizations:
            return 0

        deleted_count = len(organizations)

        try:
            for organization in organizations:
                await self.db_session.delete(organization)

            await self.db_session.commit()

        except Exception as e:
            await self.db_session.rollback()
            raise ValueError(f"Failed to delete organizations: {str(e)}") from e

        return deleted_count

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for forwarded IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to client IP
        return request.client.host if request.client else "unknown"

    def _serialize_values(self, values: dict[str, Any] | None) -> str | None:
        """
        Serialize values to JSON, handling datetime objects.

        Args:
            values: Dictionary of values to serialize

        Returns:
            JSON string or None
        """
        import json
        from datetime import date, datetime, time

        if not values:
            return None

        def datetime_converter(obj):
            """Convert datetime objects to ISO format strings."""
            if isinstance(obj, (datetime, date, time)):
                return obj.isoformat()
            raise TypeError(
                f"Object of type {type(obj).__name__} is not JSON serializable"
            )

        return json.dumps(values, default=datetime_converter)

    def _serialize_organization_to_dict(self, organization: Organization) -> dict[str, Any]:
        """
        Serialize organization to dictionary with proper datetime formatting.

        Args:
            organization: Organization object

        Returns:
            Dictionary with formatted datetime fields
        """
        return {
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug,
            "description": organization.description,
            "level": organization.level,
            "status": organization.status.value if hasattr(organization.status, 'value') else str(organization.status),
            "is_active": organization.is_active,
            "parent_id": organization.parent_id,
            "created_at": organization.created_at.isoformat() if organization.created_at else None,
            "updated_at": organization.updated_at.isoformat() if organization.updated_at else None,
            "email": organization.email,
            "phone": organization.phone,
            "website": organization.website,
            "address_line1": organization.address_line1,
            "address_line2": organization.address_line2,
            "city": organization.city,
            "state": organization.state,
            "country": organization.country,
            "postal_code": organization.postal_code,
            "settings": organization.settings,
            "allowed_domains": organization.allowed_domains,
            "created_by": organization.created_by,
            "updated_by": organization.updated_by,
        }

    async def log_organization_action(
        self,
        admin_id: int | None,
        action: OverwatchAuditAction,
        resource_type: str,
        resource_id: int | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """
        Log organization action to audit trail using AdminService.

        Args:
            admin_id: Admin ID
            action: Action performed
            resource_type: Type of resource
            resource_id: ID of specific resource
            old_values: Previous values (for updates)
            new_values: New values
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether action was successful
            error_message: Error message if failed
        """
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(self.db_session)
        await admin_service.log_admin_action(
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )

    def _get_metadata(self) -> dict[str, Any]:
        """
        Get metadata for organization fields.

        Returns:
            Dictionary with field metadata
        """
        return {
            "fields": {
                "id": {"type": "integer", "nullable": False},
                "name": {"type": "string", "nullable": False},
                "slug": {"type": "string", "nullable": False},
                "description": {"type": "string", "nullable": True},
                "level": {"type": "integer", "nullable": False},
                "status": {"type": "string", "nullable": False},
                "is_active": {"type": "boolean", "nullable": False},
                "parent_id": {"type": "integer", "nullable": True},
                "email": {"type": "string", "nullable": True},
                "phone": {"type": "string", "nullable": True},
                "website": {"type": "string", "nullable": True},
                "address_line1": {"type": "string", "nullable": True},
                "address_line2": {"type": "string", "nullable": True},
                "city": {"type": "string", "nullable": True},
                "state": {"type": "string", "nullable": True},
                "country": {"type": "string", "nullable": True},
                "postal_code": {"type": "string", "nullable": True},
                "settings": {"type": "string", "nullable": True},
                "allowed_domains": {"type": "string", "nullable": True},
                "created_at": {"type": "datetime", "nullable": False},
                "updated_at": {"type": "datetime", "nullable": False},
                "created_by": {"type": "integer", "nullable": True},
                "updated_by": {"type": "integer", "nullable": True},
            },
            "sortable_fields": [
                "id",
                "name",
                "slug",
                "level",
                "status",
                "is_active",
                "created_at",
                "updated_at",
            ],
            "filterable_fields": ["status", "is_active", "level"],
        }
