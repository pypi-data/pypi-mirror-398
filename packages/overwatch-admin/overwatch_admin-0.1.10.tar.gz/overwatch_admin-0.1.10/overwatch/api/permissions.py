"""
Permission management API endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin, OverwatchAdminRole
from overwatch.services.permission_service import PermissionService

from .auth import get_current_admin_required

router = APIRouter(tags=["Permissions"])


@router.get("/check")
async def check_permission(
    permission: str,
    resource_id: int | None = Query(None),
    organization_id: int | None = Query(None),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Check if current admin has a specific permission.

    Args:
        permission: Permission string (e.g., "read:user", "write:product")
        resource_id: Optional specific resource ID for fine-grained control
        organization_id: Optional organization ID for organization-scoped permissions

    Returns:
        Dictionary with permission check result
    """
    permission_service = PermissionService(db)

    has_permission = await permission_service.check_permission(
        current_admin, permission, resource_id, organization_id
    )

    return {
        "has_permission": has_permission,
        "permission": permission,
        "resource_id": resource_id,
        "organization_id": organization_id,
        "admin_id": current_admin.id,
        "admin_role": current_admin.role.value,
    }


@router.get("/admin/{admin_id}/permissions")
async def get_admin_permissions(
    admin_id: int,
    resource: str | None = Query(None),
    include_expired: bool = Query(False),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get all permissions for a specific admin.

    Args:
        admin_id: Admin ID to get permissions for
        resource: Optional resource type filter
        include_expired: Whether to include expired permissions

    Returns:
        Dictionary with admin permissions
    """
    # Check permissions - only super admins or admins with permission to read admin permissions
    if current_admin.role != OverwatchAdminRole.SUPER_ADMIN:
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, "read:admin_permissions"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view admin permissions",
            )

    permission_service = PermissionService(db)

    # Get explicit permissions
    permissions = await permission_service.get_admin_permissions(
        admin_id, resource, include_expired
    )

    # Get permission hierarchy
    hierarchy = await permission_service.get_permission_hierarchy(admin_id)

    return {
        "admin_id": admin_id,
        "permissions": [
            {
                "id": perm.id,
                "resource": perm.resource,
                "action": perm.action,
                "resource_id": perm.resource_id,
                "is_granted": perm.is_granted,
                "expires_at": perm.expires_at.isoformat() if perm.expires_at else None,
                "created_at": perm.created_at.isoformat() if perm.created_at else None,
                "granted_by": perm.granted_by,
            }
            for perm in permissions
        ],
        "hierarchy": hierarchy,
        "total_count": len(permissions),
    }


@router.post("/admin/{admin_id}/permissions")
async def grant_permission(
    admin_id: int,
    resource: str,
    action: str,
    resource_id: int | None = None,
    expires_at: Any = None,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Grant a permission to an admin.

    Args:
        admin_id: Admin ID to grant permission to
        resource: Resource type (e.g., "user", "product")
        action: Action (e.g., "read", "write", "delete")
        resource_id: Optional specific resource ID
        expires_at: Optional expiration datetime

    Returns:
        Dictionary with granted permission details
    """
    # Check permissions - only super admins or admins with permission to grant permissions
    if current_admin.role != OverwatchAdminRole.SUPER_ADMIN:
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, "write:admin_permissions"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to grant admin permissions",
            )

    permission_service = PermissionService(db)

    # Grant permission
    permission = await permission_service.grant_permission(
        admin_id=admin_id,
        resource=resource,
        action=action,
        resource_id=resource_id,
        expires_at=expires_at,
        granted_by=getattr(current_admin, "id", None),
    )

    return {
        "id": permission.id,
        "admin_id": permission.admin_id,
        "resource": permission.resource,
        "action": permission.action,
        "resource_id": permission.resource_id,
        "is_granted": permission.is_granted,
        "expires_at": permission.expires_at.isoformat()
        if permission.expires_at
        else None,
        "created_at": permission.created_at.isoformat()
        if permission.created_at
        else None,
        "granted_by": permission.granted_by,
        "message": "Permission granted successfully",
    }


@router.delete("/admin/{admin_id}/permissions")
async def revoke_permission(
    admin_id: int,
    resource: str,
    action: str,
    resource_id: int | None = None,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Revoke a permission from an admin.

    Args:
        admin_id: Admin ID to revoke permission from
        resource: Resource type
        action: Action
        resource_id: Optional specific resource ID

    Returns:
        Dictionary with revocation result
    """
    # Check permissions - only super admins or admins with permission to revoke permissions
    if current_admin.role != OverwatchAdminRole.SUPER_ADMIN:
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, "write:admin_permissions"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to revoke admin permissions",
            )

    permission_service = PermissionService(db)

    # Revoke permission
    revoked = await permission_service.revoke_permission(
        admin_id=admin_id,
        resource=resource,
        action=action,
        resource_id=resource_id,
    )

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    return {
        "admin_id": admin_id,
        "resource": resource,
        "action": action,
        "resource_id": resource_id,
        "message": "Permission revoked successfully",
    }


@router.get("/organizations/{organization_id}/admins")
async def get_organization_admins(
    organization_id: int,
    role: OverwatchAdminRole | None = Query(None),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get all admins in an organization.

    Args:
        organization_id: Organization ID
        role: Optional role filter

    Returns:
        Dictionary with organization admins
    """
    # Check if current admin can access this organization
    permission_service = PermissionService(db)
    can_access = await permission_service.can_access_organization(
        current_admin, organization_id
    )
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this organization",
        )

    # Get organization admins
    admins = await permission_service.get_organization_admins(organization_id, role)

    return {
        "organization_id": organization_id,
        "admins": [
            {
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "first_name": admin.first_name,
                "last_name": admin.last_name,
                "role": admin.role.value,
                "is_active": admin.is_active,
                "created_at": admin.created_at.isoformat()
                if admin.created_at
                else None,
                "last_login": admin.last_login.isoformat()
                if admin.last_login
                else None,
            }
            for admin in admins
        ],
        "total_count": len(admins),
        "role_filter": role.value if role else None,
    }


@router.get("/organizations")
async def get_accessible_organizations(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get list of organizations the current admin can access.

    Returns:
        Dictionary with accessible organizations
    """
    permission_service = PermissionService(db)

    organizations = await permission_service.get_accessible_organizations(current_admin)

    return {
        "admin_id": current_admin.id,
        "organizations": [
            {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "level": org.level,
                "is_active": org.is_active,
                "created_at": org.created_at.isoformat() if org.created_at else None,
            }
            for org in organizations
        ],
        "total_count": len(organizations),
    }


@router.get("/resource/{resource_type}/summary")
async def get_resource_permissions_summary(
    resource_type: str,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get a summary of permissions for a resource type.

    Args:
        resource_type: Type of resource

    Returns:
        Dictionary with permission statistics
    """
    # Check permissions - only super admins or admins with permission to view permission statistics
    if current_admin.role != OverwatchAdminRole.SUPER_ADMIN:
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, "read:permission_summary"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view permission summary",
            )

    permission_service = PermissionService(db)

    summary = await permission_service.get_resource_permissions_summary(resource_type)

    return summary


@router.post("/cleanup-expired")
async def cleanup_expired_permissions(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Clean up expired permissions.

    Returns:
        Dictionary with cleanup results
    """
    # Only super admins can clean up permissions
    if current_admin.role != OverwatchAdminRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can clean up expired permissions",
        )

    permission_service = PermissionService(db)

    cleaned_count = await permission_service.cleanup_expired_permissions()

    return {
        "cleaned_count": cleaned_count,
        "message": f"Cleaned up {cleaned_count} expired permissions",
    }


@router.post("/bulk/grant")
async def bulk_grant_permissions(
    permissions: list[dict[str, Any]],
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Grant multiple permissions to admins in bulk.

    Args:
        permissions: List of permission dictionaries with keys:
            - admin_id: Admin ID to grant permission to
            - resource: Resource type (e.g., "user", "product")
            - action: Action (e.g., "read", "write", "delete")
            - resource_id: Optional specific resource ID
            - expires_at: Optional expiration datetime

    Returns:
        Dictionary with bulk grant results
    """
    # Check permissions - only super admins or admins with permission to grant permissions
    if current_admin.role != OverwatchAdminRole.SUPER_ADMIN:
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, "write:admin_permissions"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to grant admin permissions",
            )

    permission_service = PermissionService(db)

    # Validate input
    if not permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permissions list cannot be empty",
        )

    # Grant permissions in bulk
    created_permissions = await permission_service.bulk_grant_permissions(
        permissions=permissions,
        granted_by=getattr(current_admin, "id", None),
    )

    return {
        "granted_count": len(created_permissions),
        "permissions": [
            {
                "id": perm.id,
                "admin_id": perm.admin_id,
                "resource": perm.resource,
                "action": perm.action,
                "resource_id": perm.resource_id,
                "is_granted": perm.is_granted,
                "expires_at": perm.expires_at.isoformat()
                if perm.expires_at
                else None,
                "created_at": perm.created_at.isoformat()
                if perm.created_at
                else None,
                "granted_by": perm.granted_by,
            }
            for perm in created_permissions
        ],
        "message": f"Successfully granted {len(created_permissions)} permissions",
    }


@router.post("/bulk/revoke")
async def bulk_revoke_permissions(
    permissions: list[dict[str, Any]],
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Revoke multiple permissions from admins in bulk.

    Args:
        permissions: List of permission dictionaries with keys:
            - admin_id: Admin ID to revoke permission from
            - resource: Resource type
            - action: Action
            - resource_id: Optional specific resource ID

    Returns:
        Dictionary with bulk revocation results
    """
    # Check permissions - only super admins or admins with permission to revoke permissions
    if current_admin.role != OverwatchAdminRole.SUPER_ADMIN:
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, "write:admin_permissions"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to revoke admin permissions",
            )

    permission_service = PermissionService(db)

    # Validate input
    if not permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permissions list cannot be empty",
        )

    # Revoke permissions in bulk
    result = await permission_service.bulk_revoke_permissions(permissions)

    return {
        "revoked_count": result["revoked_count"],
        "failed_count": result["failed_count"],
        "failed_revocations": result["failed_revocations"],
        "message": f"Successfully revoked {result['revoked_count']} permissions",
    }
