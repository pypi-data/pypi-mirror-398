"""
Admin management API endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin, OverwatchAdminRole
from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.schemas.admin import (
    AdminBulkCreate,
    AdminBulkDelete,
    AdminBulkUpdate,
    AdminCreate,
    AdminListResponse,
    AdminPasswordChange,
    AdminPermissionCheck,
    AdminPermissionResponse,
    AdminResponse,
    AdminStatsResponse,
    AdminUpdate,
)
from overwatch.services.admin_service import AdminService

from .auth import get_current_admin_required

router = APIRouter(tags=["Overwatch Admins"])


@router.get("", response_model=AdminListResponse)
async def list_admins(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=1000),
    search: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    organization_id: int | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_direction: str = Query("desc", regex="^(asc|desc)$"),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get list of admin users with pagination and filtering.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view admins",
        )

    # Convert role string to enum if provided
    role_enum = None
    if role:
        try:
            role_enum = OverwatchAdminRole(role.lower())
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Must be one of: {[r.value for r in OverwatchAdminRole]}",
            ) from e

    # Get admins
    admins, total = await admin_service.get_admin_list(
        page=page,
        per_page=per_page,
        search=search,
        role=role_enum,
        is_active=is_active,
        organization_id=organization_id,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )

    # Convert to response schemas
    admins_response = [AdminResponse.model_validate(admin) for admin in admins]

    # Calculate pagination info
    pages = (total + per_page - 1) // per_page

    # Add metadata about the admin fields
    metadata = {
        "fields": {
            "id": {"type": "integer", "nullable": False},
            "username": {"type": "string", "nullable": False},
            "email": {"type": "string", "nullable": True},
            "first_name": {"type": "string", "nullable": True},
            "last_name": {"type": "string", "nullable": True},
            "role": {"type": "string", "nullable": False},
            "is_active": {"type": "boolean", "nullable": False},
            "last_login": {"type": "datetime", "nullable": True},
            "created_at": {"type": "datetime", "nullable": False},
            "updated_at": {"type": "datetime", "nullable": False},
            "organization": {"type": "object", "nullable": True},
        },
        "sortable_fields": [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "last_login",
            "created_at",
            "updated_at",
        ],
        "filterable_fields": ["role", "is_active"],
    }

    return {
        "items": admins_response,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "metadata": metadata,
    }


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get admin statistics.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view admin stats",
        )

    stats = await admin_service.get_admin_stats()

    return {
        "total_admins": stats["total"],
        "active_admins": stats["active"],
        "inactive_admins": stats["inactive"],
        "suspended_admins": stats["suspended"],
        "super_admins": stats["super_admin"],
        "admins": stats["admin"],
        "read_only_admins": stats["read_only"],
    }


@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> Admin:
    """
    Get admin user by ID.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view admin details",
        )

    # Get admin
    admin = await admin_service.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    # Log read action
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.READ,
        resource_type="Admin",
        resource_id=admin_id,
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return admin


@router.post("", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_data: AdminCreate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> Admin:
    """
    Create new admin user.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("write:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create admins",
        )

    try:
        # Create admin
        admin = await admin_service.create_admin(
            username=admin_data.username,
            password=admin_data.password.get_secret_value(),
            email=admin_data.email,
            first_name=admin_data.first_name,
            last_name=admin_data.last_name,
            role=admin_data.role,
            is_active=admin_data.is_active,
            organization_id=admin_data.organization_id,
            created_by=getattr(current_admin, "id", None),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log creation
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.CREATE,
        resource_type="Admin",
        resource_id=getattr(admin, "id", None),
        new_values={
            "username": admin_data.username,
            "email": admin_data.email,
            "role": admin_data.role,
        },
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return admin


@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> Admin:
    """
    Update admin user.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("write:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update admins",
        )

    # Get existing admin
    existing_admin = await admin_service.get_admin_by_id(admin_id)
    if not existing_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    # Don't allow users to modify themselves in certain ways
    if admin_id == current_admin.id:
        if admin_data.role is not None and admin_data.role != current_admin.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role",
            )
        if admin_data.is_active is not None and not admin_data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself",
            )

    # Update admin
    updates = admin_data.model_dump(exclude_unset=True)
    if "password" in updates:
        updates["password"] = updates["password"].get_secret_value()

    try:
        admin = await admin_service.update_admin(
            admin_id=admin_id,
            updates=updates,
            updated_by=getattr(current_admin, "id", None),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log update
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.UPDATE,
        resource_type="Admin",
        resource_id=admin_id,
        new_values=updates,
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return admin


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete admin user.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("delete:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete admins",
        )

    # Don't allow users to delete themselves
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    # Get existing admin
    existing_admin = await admin_service.get_admin_by_id(admin_id)
    if not existing_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    # Delete admin
    await admin_service.delete_admin(admin_id)

    # Log deletion
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.DELETE,
        resource_type="Admin",
        resource_id=admin_id,
        old_values={"username": existing_admin.username},
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/bulk", response_model=list[AdminResponse])
async def bulk_create_admins(
    request: AdminBulkCreate,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[Admin]:
    """
    Create multiple admin users.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("write:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create admins",
        )

    # Create admins
    admins = []
    for admin_data in request.admins:
        try:
            admin = await admin_service.create_admin(
                username=admin_data.username,
                password=admin_data.password.get_secret_value(),
                email=admin_data.email,
                first_name=admin_data.first_name,
                last_name=admin_data.last_name,
                role=admin_data.role,
                is_active=admin_data.is_active,
                created_by=getattr(current_admin, "id", None),
            )
            admins.append(admin)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

    # Log bulk creation
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_CREATE,
        resource_type="Admin",
        new_values={"count": len(admins)},
        ip_address=admin_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )

    return admins


@router.put("/bulk", response_model=list[AdminResponse])
async def bulk_update_admins(
    request: AdminBulkUpdate,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[Admin]:
    """
    Update multiple admin users.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("write:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update admins",
        )

    # Update admins
    admins = []
    for admin_id in request.admin_ids:
        # Don't allow users to modify themselves
        if admin_id == current_admin.id:
            continue

        try:
            admin = await admin_service.update_admin(
                admin_id=admin_id,
                updates=request.updates.model_dump(exclude_unset=True),
                updated_by=getattr(current_admin, "id", None),
            )
            if admin:
                admins.append(admin)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

    # Log bulk update
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_UPDATE,
        resource_type="Admin",
        new_values={"count": len(admins)},
        ip_address=admin_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )

    return admins


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_admins(
    request: AdminBulkDelete,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete multiple admin users.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("delete:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete admins",
        )

    # Don't allow users to delete themselves
    if current_admin.id in request.admin_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    # Delete admins
    deleted_count = 0
    for admin_id in request.admin_ids:
        if await admin_service.delete_admin(admin_id):
            deleted_count += 1

    # Log bulk deletion
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_DELETE,
        resource_type="Admin",
        new_values={"count": deleted_count},
        ip_address=admin_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )


@router.post("/{admin_id}/change-password")
async def change_admin_password(
    admin_id: int,
    password_data: AdminPasswordChange,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """
    Change admin user password.
    """
    admin_service = AdminService(db)

    # Check permissions (users can change their own password, or admins can change others')
    if admin_id != current_admin.id and not current_admin.has_permission("write:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to change password",
        )

    # Get admin
    admin = await admin_service.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    try:
        # For self password changes, validate current password
        # For admin-forced password changes on others, skip validation
        skip_current_password_validation = admin_id != current_admin.id

        await admin_service.change_admin_password(
            admin_id=admin_id,
            current_password=password_data.current_password.get_secret_value() if not skip_current_password_validation else None,
            new_password=password_data.new_password.get_secret_value(),
            updated_by=getattr(current_admin, "id", None),
            skip_current_password_validation=skip_current_password_validation,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log password change
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.UPDATE,
        resource_type="Admin",
        resource_id=admin_id,
        new_values={"password_changed": True},
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {"message": "Password changed successfully"}


@router.post("/{admin_id}/check-permission", response_model=AdminPermissionResponse)
async def check_admin_permission(
    admin_id: int,
    permission_check: AdminPermissionCheck,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Check if admin has a specific permission.
    """
    admin_service = AdminService(db)

    # Check permissions
    if not current_admin.has_permission("read:admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to check admin permissions",
        )

    # Get admin
    admin = await admin_service.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    # Check permission
    has_permission = admin.has_permission(permission_check.permission)

    return {
        "has_permission": has_permission,
        "permission": permission_check.permission,
        "reason": None if has_permission else "Permission not granted",
    }
