"""
Permission service for comprehensive RBAC management.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.models.admin import Admin, OverwatchAdminRole
from overwatch.models.admin_permission import AdminPermission
from overwatch.models.organization import Organization


class PermissionService:
    """Service for managing permissions and RBAC."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize permission service.

        Args:
            db_session: Database session
        """
        self.db_session = db_session

    async def check_permission(
        self,
        admin: Admin,
        permission: str,
        resource_id: int | None = None,
        organization_id: int | None = None,
    ) -> bool:
        """
        Check if admin has a specific permission.

        Args:
            admin: Admin object
            permission: Permission string (e.g., "read:user", "write:product")
            resource_id: Optional specific resource ID for fine-grained control
            organization_id: Optional organization ID for organization-scoped permissions

        Returns:
            True if admin has permission, False otherwise
        """
        # Use the model's has_permission method as base
        if admin.has_permission(permission, resource_id, organization_id):
            return True

        # Check database permissions for more granular control
        admin_id = getattr(admin, "id", None)
        if admin_id is None:
            return False
        return await self._check_database_permission(
            admin_id, permission, resource_id, organization_id
        )

    async def _check_database_permission(
        self,
        admin_id: int,
        permission: str,
        resource_id: int | None = None,
        organization_id: int | None = None,
    ) -> bool:
        """
        Check database-stored permissions.

        Args:
            admin_id: Admin ID
            permission: Permission string
            resource_id: Optional resource ID
            organization_id: Optional organization ID

        Returns:
            True if permission exists in database, False otherwise
        """
        # Parse permission
        parts = permission.split(":")
        if len(parts) != 2:
            return False

        action, resource = parts

        # Query for explicit permissions
        query = select(AdminPermission).where(
            AdminPermission.admin_id == admin_id,
            AdminPermission.resource == resource,
            AdminPermission.action == action,
            AdminPermission.is_granted.is_(True),
        )

        # Add resource ID filter if specified
        if resource_id is not None:
            query = query.where(
                (AdminPermission.resource_id == resource_id)
                | (AdminPermission.resource_id.is_(None))  # Global permission
            )
        else:
            query = query.where(AdminPermission.resource_id.is_(None))

        result = await self.db_session.execute(query)
        permissions = result.scalars().all()

        if not permissions:
            return False

        # Check if any permission is valid (not expired)
        for perm in permissions:
            if perm.expires_at is None or perm.expires_at > perm.expires_at.now(
                perm.expires_at.tzinfo
            ):
                return True

        return False

    async def grant_permission(
        self,
        admin_id: int,
        resource: str,
        action: str,
        resource_id: int | None = None,
        expires_at: Any = None,
        granted_by: int | None = None,
    ) -> AdminPermission:
        """
        Grant a permission to an admin.

        Args:
            admin_id: Admin ID to grant permission to
            resource: Resource type (e.g., "user", "product")
            action: Action (e.g., "read", "write", "delete")
            resource_id: Optional specific resource ID
            expires_at: Optional expiration datetime
            granted_by: Admin ID who granted the permission

        Returns:
            Created AdminPermission object
        """
        permission = AdminPermission(
            admin_id=admin_id,
            resource=resource,
            action=action,
            resource_id=resource_id,
            expires_at=expires_at,
            granted_by=granted_by,
        )

        self.db_session.add(permission)
        await self.db_session.commit()
        await self.db_session.refresh(permission)

        return permission

    async def revoke_permission(
        self,
        admin_id: int,
        resource: str,
        action: str,
        resource_id: int | None = None,
    ) -> bool:
        """
        Revoke a permission from an admin.

        Args:
            admin_id: Admin ID to revoke permission from
            resource: Resource type
            action: Action
            resource_id: Optional specific resource ID

        Returns:
            True if permission was revoked, False if not found
        """
        query = select(AdminPermission).where(
            AdminPermission.admin_id == admin_id,
            AdminPermission.resource == resource,
            AdminPermission.action == action,
        )

        if resource_id is not None:
            query = query.where(AdminPermission.resource_id == resource_id)
        else:
            query = query.where(AdminPermission.resource_id.is_(None))

        result = await self.db_session.execute(query)
        permission = result.scalar_one_or_none()

        if permission:
            await self.db_session.delete(permission)
            await self.db_session.commit()
            return True

        return False

    async def get_admin_permissions(
        self,
        admin_id: int,
        resource: str | None = None,
        include_expired: bool = False,
    ) -> list[AdminPermission]:
        """
        Get all permissions for an admin.

        Args:
            admin_id: Admin ID
            resource: Optional resource filter
            include_expired: Whether to include expired permissions

        Returns:
            List of AdminPermission objects
        """
        query = select(AdminPermission).where(AdminPermission.admin_id == admin_id)

        if resource:
            query = query.where(AdminPermission.resource == resource)

        if not include_expired:
            from datetime import UTC, datetime

            query = query.where(
                (AdminPermission.expires_at.is_(None))
                | (AdminPermission.expires_at > datetime.now(UTC))
            )

        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_organization_admins(
        self, organization_id: int, role: OverwatchAdminRole | None = None
    ) -> list[Admin]:
        """
        Get all admins in an organization.

        Args:
            organization_id: Organization ID
            role: Optional role filter

        Returns:
            List of Admin objects
        """
        query = select(Admin).where(Admin.organization_id == organization_id)

        if role:
            query = query.where(Admin.role == role)

        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def can_access_organization(self, admin: Admin, organization_id: int) -> bool:
        """
        Check if admin can access an organization.

        Args:
            admin: Admin object
            organization_id: Organization ID to check

        Returns:
            True if admin can access organization, False otherwise
        """
        # Super admins can access all organizations
        if admin.role == OverwatchAdminRole.SUPER_ADMIN:
            return True

        # Check if organization exists and is active
        org_query = select(Organization).where(
            Organization.id == organization_id,
            Organization.is_active.is_(True),
        )
        org_result = await self.db_session.execute(org_query)
        organization = org_result.scalar_one_or_none()

        if not organization:
            return False

        # Check if admin is assigned to this organization
        if admin.organization_id == organization_id:
            return True

        # Check organization permissions
        return admin.can_access_organization(organization_id)

    async def get_accessible_organizations(self, admin: Admin) -> list[Organization]:
        """
        Get list of organizations an admin can access.

        Args:
            admin: Admin object

        Returns:
            List of Organization objects
        """
        # Super admins can access all organizations
        if admin.role == OverwatchAdminRole.SUPER_ADMIN:
            query = select(Organization).where(Organization.is_active.is_(True))
            result = await self.db_session.execute(query)
            return list(result.scalars().all())

        # Other admins can only access their assigned organization
        if admin.organization_id:
            query = select(Organization).where(
                Organization.id == admin.organization_id,
                Organization.is_active.is_(True),
            )
            result = await self.db_session.execute(query)
            return list(result.scalars().all())

        return []

    async def get_resource_permissions_summary(
        self, resource_type: str
    ) -> dict[str, Any]:
        """
        Get a summary of permissions for a resource type.

        Args:
            resource_type: Type of resource

        Returns:
            Dictionary with permission statistics
        """
        from sqlalchemy import func

        # Count permissions by action
        action_counts_query = (
            select(
                AdminPermission.action,
                func.count(AdminPermission.id).label("count"),
            )
            .where(
                AdminPermission.resource == resource_type,
                AdminPermission.is_granted.is_(True),
            )
            .group_by(AdminPermission.action)
        )
        action_result = await self.db_session.execute(action_counts_query)
        action_counts = {row.action: row.count for row in action_result.all()}

        # Count permissions by admin role
        role_counts_query = (
            select(
                Admin.role,
                func.count(AdminPermission.id).label("count"),
            )
            .join(AdminPermission, Admin.id == AdminPermission.admin_id)
            .where(
                AdminPermission.resource == resource_type,
                AdminPermission.is_granted.is_(True),
            )
            .group_by(Admin.role)
        )
        role_result = await self.db_session.execute(role_counts_query)
        role_counts = {row.role.value: row.count for row in role_result.all()}

        # Count expired vs active permissions
        from datetime import UTC, datetime

        active_query = select(func.count(AdminPermission.id)).where(
            AdminPermission.resource == resource_type,
            AdminPermission.is_granted.is_(True),
            (
                AdminPermission.expires_at.is_(None)
                | (AdminPermission.expires_at > datetime.now(UTC))
            ),
        )
        active_result = await self.db_session.execute(active_query)
        active_count = active_result.scalar() or 0

        expired_query = select(func.count(AdminPermission.id)).where(
            AdminPermission.resource == resource_type,
            AdminPermission.is_granted.is_(True),
            AdminPermission.expires_at < datetime.now(UTC),
        )
        expired_result = await self.db_session.execute(expired_query)
        expired_count = expired_result.scalar() or 0

        return {
            "resource_type": resource_type,
            "total_permissions": active_count + expired_count,
            "active_permissions": active_count,
            "expired_permissions": expired_count,
            "permissions_by_action": action_counts,
            "permissions_by_role": role_counts,
        }

    async def cleanup_expired_permissions(self) -> int:
        """
        Clean up expired permissions.

        Returns:
            Number of permissions cleaned up
        """
        from datetime import UTC, datetime

        from sqlalchemy import delete

        # Delete expired permissions
        delete_stmt = delete(AdminPermission).where(
            AdminPermission.expires_at < datetime.now(UTC)
        )
        result = await self.db_session.execute(delete_stmt)
        await self.db_session.commit()

        return result.rowcount if hasattr(result, "rowcount") else 0

    async def get_permission_hierarchy(self, admin_id: int) -> dict[str, Any]:
        """
        Get the full permission hierarchy for an admin.

        Args:
            admin_id: Admin ID

        Returns:
            Dictionary with detailed permission information
        """
        # Get admin info
        admin_query = select(Admin).where(Admin.id == admin_id)
        admin_result = await self.db_session.execute(admin_query)
        admin = admin_result.scalar_one_or_none()

        if not admin:
            return {}

        # Get organization info
        organization = None
        if admin.organization_id:
            org_query = select(Organization).where(
                Organization.id == admin.organization_id
            )
            org_result = await self.db_session.execute(org_query)
            organization = org_result.scalar_one_or_none()

        # Get explicit permissions
        permissions = await self.get_admin_permissions(admin_id, include_expired=False)

        # Parse custom permissions
        custom_permissions = {}
        if admin.custom_permissions:
            import json

            try:
                custom_permissions = json.loads(str(admin.custom_permissions))
            except (json.JSONDecodeError, TypeError):
                pass

        # Parse organization permissions
        organization_permissions = {}
        if admin.organization_permissions:
            import json

            try:
                organization_permissions = json.loads(
                    str(admin.organization_permissions)
                )
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "admin": {
                "id": admin.id,
                "username": admin.username,
                "role": admin.role.value,
                "organization_id": admin.organization_id,
            },
            "organization": {
                "id": organization.id if organization else None,
                "name": organization.name if organization else None,
                "slug": organization.slug if organization else None,
                "level": organization.level if organization else None,
            }
            if organization
            else None,
            "role_based_permissions": self._get_role_permissions(
                getattr(admin, "role", None)
            ),
            "custom_permissions": custom_permissions,
            "organization_permissions": organization_permissions,
            "explicit_permissions": [
                {
                    "id": perm.id,
                    "resource": perm.resource,
                    "action": perm.action,
                    "resource_id": perm.resource_id,
                    "expires_at": perm.expires_at.isoformat()
                    if perm.expires_at
                    else None,
                }
                for perm in permissions
            ],
        }

    async def bulk_grant_permissions(
        self,
        permissions: list[dict[str, Any]],
        granted_by: int | None = None,
    ) -> list[AdminPermission]:
        """
        Grant multiple permissions to admins.

        Args:
            permissions: List of permission dictionaries with keys:
                - admin_id: Admin ID to grant permission to
                - resource: Resource type (e.g., "user", "product")
                - action: Action (e.g., "read", "write", "delete")
                - resource_id: Optional specific resource ID
                - expires_at: Optional expiration datetime
            granted_by: Admin ID who granted the permissions

        Returns:
            List of created AdminPermission objects
        """
        created_permissions = []

        for perm_data in permissions:
            permission = AdminPermission(
                admin_id=perm_data["admin_id"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                resource_id=perm_data.get("resource_id"),
                expires_at=perm_data.get("expires_at"),
                granted_by=granted_by,
            )
            self.db_session.add(permission)
            created_permissions.append(permission)

        await self.db_session.commit()

        # Refresh all permissions to get their IDs
        for permission in created_permissions:
            await self.db_session.refresh(permission)

        return created_permissions

    async def bulk_revoke_permissions(
        self,
        permissions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Revoke multiple permissions from admins.

        Args:
            permissions: List of permission dictionaries with keys:
                - admin_id: Admin ID to revoke permission from
                - resource: Resource type
                - action: Action
                - resource_id: Optional specific resource ID

        Returns:
            Dictionary with revocation results
        """
        revoked_count = 0
        failed_revocations = []

        for perm_data in permissions:
            try:
                revoked = await self.revoke_permission(
                    admin_id=perm_data["admin_id"],
                    resource=perm_data["resource"],
                    action=perm_data["action"],
                    resource_id=perm_data.get("resource_id"),
                )
                if revoked:
                    revoked_count += 1
                else:
                    failed_revocations.append(perm_data)
            except Exception as e:
                failed_revocations.append({**perm_data, "error": str(e)})

        return {
            "revoked_count": revoked_count,
            "failed_count": len(failed_revocations),
            "failed_revocations": failed_revocations,
        }

    def _get_role_permissions(self, role: OverwatchAdminRole | None) -> list[str]:
        """Get default permissions for a role."""
        if role is None:
            return []
        if role == OverwatchAdminRole.SUPER_ADMIN:
            return ["*"]  # All permissions
        elif role == OverwatchAdminRole.ADMIN:
            return [
                "read:admin",
                "write:admin",
                "read:audit",
                "read:config",
                "write:config",
                "read:dashboard",
            ]
        elif role == OverwatchAdminRole.READ_ONLY:
            return [
                "read:admin",
                "read:audit",
                "read:config",
                "read:dashboard",
            ]
        return []
