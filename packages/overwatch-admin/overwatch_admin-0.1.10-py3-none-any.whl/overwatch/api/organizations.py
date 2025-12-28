"""
Organization management API endpoints.
"""

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin
from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.schemas.organization import (
    BulkOrganizationCreate,
    BulkOrganizationDelete,
    BulkOrganizationUpdate,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationStats,
    OrganizationUpdate,
    PaginatedOrganizations,
)
from overwatch.services.organization_service import OrganizationService
from overwatch.services.permission_service import PermissionService

from .auth import get_current_admin_required

router = APIRouter(tags=["Overwatch Organizations"])


@router.get("", response_model=PaginatedOrganizations)
async def list_organizations(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=1000),
    search: str | None = Query(None),
    org_status: str | None = Query(None),
    is_active: bool | None = Query(None),
    level: int | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_direction: str = Query("desc", pattern="^(asc|desc)$"),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get list of organizations with pagination and filtering.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "read:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view organizations",
        )

    # Use service layer
    organization_service = OrganizationService(db)
    organizations, total = await organization_service.get_organizations_paginated(
        page=page,
        per_page=per_page,
        search=search,
        org_status=org_status,
        is_active=is_active,
        level=level,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )

    # Convert to response schemas using custom serialization
    organizations_response = [
        OrganizationResponse(**organization_service._serialize_organization_to_dict(org))
        for org in organizations
    ]

    # Calculate pagination info
    pages = (total + per_page - 1) // per_page if total > 0 else 0

    return {
        "items": organizations_response,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "metadata": organization_service._get_metadata(),
    }


@router.get("/stats", response_model=OrganizationStats)
async def get_organization_stats(
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get organization statistics.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "read:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view organization stats",
        )

    # Use service layer for optimized stats
    organization_service = OrganizationService(db)
    return await organization_service.get_organization_stats()


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationResponse:
    """
    Get organization by ID.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "read:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view organization details",
        )

    # Use service layer
    organization_service = OrganizationService(db)
    organization = await organization_service.get_organization_by_id(organization_id)

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Log read action
    await organization_service.log_organization_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.READ,
        resource_type="Organization",
        resource_id=organization_id,
        ip_address=organization_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return OrganizationResponse(**organization_service._serialize_organization_to_dict(organization))


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=OrganizationResponse
)
async def create_organization(
    organization_data: OrganizationCreate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationResponse:
    """
    Create new organization.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "write:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create organizations",
        )

    # Use service layer
    organization_service = OrganizationService(db)

    try:
        organization = await organization_service.create_organization(
            organization_data=organization_data,
            created_by=getattr(current_admin, "id", None),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log creation
    await organization_service.log_organization_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.CREATE,
        resource_type="Organization",
        resource_id=cast(int, organization.id),
        new_values={
            "name": organization_data.name,
            "slug": organization_data.slug,
            "level": organization_data.level,
            "is_active": organization_data.is_active,
        },
        ip_address=organization_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return OrganizationResponse(**organization_service._serialize_organization_to_dict(organization))


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    organization_data: OrganizationUpdate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationResponse:
    """
    Update organization.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "write:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update organizations",
        )

    # Use service layer
    organization_service = OrganizationService(db)

    try:
        organization = await organization_service.update_organization(
            organization_id=organization_id,
            organization_data=organization_data,
            updated_by=getattr(current_admin, "id", None),
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

    # Log update
    await organization_service.log_organization_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.UPDATE,
        resource_type="Organization",
        resource_id=organization_id,
        new_values=organization_data.model_dump(exclude_unset=True),
        ip_address=organization_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return OrganizationResponse(**organization_service._serialize_organization_to_dict(organization))


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete organization.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "delete:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete organizations",
        )

    # Use service layer
    organization_service = OrganizationService(db)

    # Get organization first for logging
    organization = await organization_service.get_organization_by_id(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Delete organization
    deleted = await organization_service.delete_organization(organization_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Log deletion
    await organization_service.log_organization_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.DELETE,
        resource_type="Organization",
        resource_id=organization_id,
        old_values={"name": organization.name},
        ip_address=organization_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=list[OrganizationResponse],
)
async def bulk_create_organizations(
    request: BulkOrganizationCreate,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[OrganizationResponse]:
    """
    Create multiple organizations.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "write:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create organizations",
        )

    # Use service layer
    organization_service = OrganizationService(db)

    try:
        organizations = await organization_service.bulk_create_organizations(
            organizations_data=request.organizations,
            created_by=getattr(current_admin, "id", None),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log bulk creation
    await organization_service.log_organization_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_CREATE,
        resource_type="Organization",
        new_values={"count": len(organizations)},
        ip_address=organization_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )

    # Return created organizations using custom serialization
    return [OrganizationResponse(**organization_service._serialize_organization_to_dict(org)) for org in organizations]


@router.put("/bulk", response_model=list[OrganizationResponse])
async def bulk_update_organizations(
    request: BulkOrganizationUpdate,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[OrganizationResponse]:
    """
    Update multiple organizations.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "write:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update organizations",
        )

    # Use service layer
    organization_service = OrganizationService(db)

    try:
        organizations = await organization_service.bulk_update_organizations(
            organization_ids=request.organization_ids,
            updates=request.updates,
            updated_by=getattr(current_admin, "id", None),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log bulk update
    await organization_service.log_organization_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_UPDATE,
        resource_type="Organization",
        new_values={"count": len(organizations)},
        ip_address=organization_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )

    # Return updated organizations using custom serialization
    return [OrganizationResponse(**organization_service._serialize_organization_to_dict(org)) for org in organizations]


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_organizations(
    request: BulkOrganizationDelete,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete multiple organizations.
    """
    # Check permissions
    permission_service = PermissionService(db)
    has_permission = await permission_service.check_permission(
        current_admin, "delete:organization"
    )
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete organizations",
        )

    # Use service layer
    organization_service = OrganizationService(db)

    try:
        deleted_count = await organization_service.bulk_delete_organizations(
            organization_ids=request.organization_ids
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log bulk deletion
    await organization_service.log_organization_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_DELETE,
        resource_type="Organization",
        new_values={"count": deleted_count},
        ip_address=organization_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )
