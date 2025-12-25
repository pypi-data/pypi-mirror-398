"""
Organization management API endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin
from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.models.organization import Organization
from overwatch.schemas.organization import (
    BulkOrganizationCreate,
    BulkOrganizationDelete,
    BulkOrganizationUpdate,
    OrganizationCreate,
    OrganizationStats,
    OrganizationUpdate,
    PaginatedOrganizations,
)
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

    # Build base query
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

    if status:
        conditions.append(Organization.status == status)

    if is_active is not None:
        conditions.append(Organization.is_active == is_active)

    if level is not None:
        conditions.append(Organization.level == level)

    if conditions:
        from sqlalchemy import and_

        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply sorting
    sort_column = getattr(Organization, sort_by)
    if sort_direction == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column)

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    organizations = result.scalars().all()

    # Calculate pagination info
    total = total or 0
    pages = (total + per_page - 1) // per_page if total > 0 else 0

    # Convert to response schemas
    organizations_response = []
    for org in organizations:
        organizations_response.append(
            {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "level": org.level,
                "status": org.status,
                "is_active": org.is_active,
                "parent_id": org.parent_id,
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "updated_at": org.updated_at.isoformat() if org.updated_at else None,
                "email": org.email,
                "phone": org.phone,
                "website": org.website,
                "address_line1": org.address_line1,
                "address_line2": org.address_line2,
                "city": org.city,
                "state": org.state,
                "country": org.country,
                "postal_code": org.postal_code,
                "settings": org.settings,
                "allowed_domains": org.allowed_domains,
                "created_by": org.created_by,
                "updated_by": org.updated_by,
            }
        )

    # Add metadata about the organization fields
    metadata = {
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

    return {
        "items": organizations_response,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "metadata": metadata,
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

    # Get stats from database
    total_query = select(func.count()).select_from(Organization)
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    active_query = (
        select(func.count())
        .select_from(Organization)
        .where(Organization.status == "active")
    )
    active_result = await db.execute(active_query)
    active = active_result.scalar()

    inactive_query = (
        select(func.count())
        .select_from(Organization)
        .where(Organization.status == "inactive")
    )
    inactive_result = await db.execute(inactive_query)
    inactive = inactive_result.scalar()

    suspended_query = (
        select(func.count())
        .select_from(Organization)
        .where(Organization.status == "suspended")
    )
    suspended_result = await db.execute(suspended_query)
    suspended = suspended_result.scalar()

    # Get organizations by level
    organizations_by_level = {}
    for level in range(1, 11):  # Levels 1-10
        level_query = (
            select(func.count())
            .select_from(Organization)
            .where(Organization.level == level)
        )
        level_result = await db.execute(level_query)
        level_count = level_result.scalar() or 0
        if level_count > 0:
            organizations_by_level[level] = level_count

    return {
        "total_organizations": total,
        "active_organizations": active,
        "inactive_organizations": inactive,
        "suspended_organizations": suspended,
        "organizations_by_level": organizations_by_level,
    }


@router.get("/{organization_id}")
async def get_organization(
    organization_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
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

    # Get organization
    query = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(query)
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Log read action
    from overwatch.services.admin_service import AdminService

    admin_service = AdminService(db)
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.READ,
        resource_type="Organization",
        resource_id=organization_id,
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "description": organization.description,
        "level": organization.level,
        "status": organization.status,
        "is_active": organization.is_active,
        "parent_id": organization.parent_id,
        "created_at": organization.created_at.isoformat()
        if organization.created_at
        else None,
        "updated_at": organization.updated_at.isoformat()
        if organization.updated_at
        else None,
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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_data: OrganizationCreate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
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

    try:
        # Create organization
        organization = Organization(
            name=organization_data.name,
            slug=organization_data.slug,
            description=organization_data.description,
            level=organization_data.level,
            is_active=organization_data.is_active,
            parent_id=organization_data.parent_id,
            created_by=getattr(current_admin, "id", None),
        )

        db.add(organization)
        await db.commit()
        await db.refresh(organization)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log creation
    from overwatch.services.admin_service import AdminService

    admin_service = AdminService(db)
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.CREATE,
        resource_type="Organization",
        resource_id=getattr(organization, "id", None),
        new_values={
            "name": organization_data.name,
            "slug": organization_data.slug,
            "level": organization_data.level,
            "is_active": organization_data.is_active,
        },
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "description": organization.description,
        "level": organization.level,
        "status": organization.status,
        "is_active": organization.is_active,
        "parent_id": organization.parent_id,
        "created_at": organization.created_at.isoformat()
        if organization.created_at
        else None,
        "updated_at": organization.updated_at.isoformat()
        if organization.updated_at
        else None,
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


@router.put("/{organization_id}")
async def update_organization(
    organization_id: int,
    organization_data: OrganizationUpdate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
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

    # Get existing organization
    query = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(query)
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Update organization
    updates = organization_data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(organization, field, value)

    organization.updated_by = getattr(current_admin, "id", None)

    try:
        await db.commit()
        await db.refresh(organization)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log update
    from overwatch.services.admin_service import AdminService

    admin_service = AdminService(db)
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.UPDATE,
        resource_type="Organization",
        resource_id=organization_id,
        new_values=updates,
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "description": organization.description,
        "level": organization.level,
        "status": organization.status,
        "is_active": organization.is_active,
        "parent_id": organization.parent_id,
        "created_at": organization.created_at.isoformat()
        if organization.created_at
        else None,
        "updated_at": organization.updated_at.isoformat()
        if organization.updated_at
        else None,
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

    # Get existing organization
    query = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(query)
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Delete organization
    await db.delete(organization)
    await db.commit()

    # Log deletion
    from overwatch.services.admin_service import AdminService

    admin_service = AdminService(db)
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.DELETE,
        resource_type="Organization",
        resource_id=organization_id,
        old_values={"name": organization.name},
        ip_address=admin_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_organizations(
    request: BulkOrganizationCreate,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict[str, Any]]:
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

    # Create organizations
    organizations = []
    for org_data in request.organizations:
        try:
            organization = Organization(
                name=org_data.name,
                slug=org_data.slug,
                description=org_data.description,
                level=org_data.level,
                is_active=org_data.is_active,
                parent_id=org_data.parent_id,
                created_by=getattr(current_admin, "id", None),
            )

            db.add(organization)
            await db.flush()
            organizations.append(organization)

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

    await db.commit()

    # Log bulk creation
    from overwatch.services.admin_service import AdminService

    admin_service = AdminService(db)
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_CREATE,
        resource_type="Organization",
        new_values={"count": len(organizations)},
        ip_address=admin_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )

    # Return created organizations
    result = []
    for organization in organizations:
        result.append(
            {
                "id": organization.id,
                "name": organization.name,
                "slug": organization.slug,
                "description": organization.description,
                "level": organization.level,
                "status": organization.status,
                "is_active": organization.is_active,
                "parent_id": organization.parent_id,
                "created_at": organization.created_at.isoformat()
                if organization.created_at
                else None,
                "updated_at": organization.updated_at.isoformat()
                if organization.updated_at
                else None,
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
        )

    return result


@router.put("/bulk")
async def bulk_update_organizations(
    request: BulkOrganizationUpdate,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict[str, Any]]:
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

    # Update organizations
    organizations = []
    updates = request.updates.model_dump(exclude_unset=True)

    for organization_id in request.organization_ids:
        query = select(Organization).where(Organization.id == organization_id)
        result = await db.execute(query)
        organization = result.scalar_one_or_none()

        if organization:
            for field, value in updates.items():
                setattr(organization, field, value)
            organization.updated_by = getattr(current_admin, "id", None)
            organizations.append(organization)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log bulk update
    from overwatch.services.admin_service import AdminService

    admin_service = AdminService(db)
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_UPDATE,
        resource_type="Organization",
        new_values={"count": len(organizations)},
        ip_address=admin_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )

    # Return updated organizations
    result = []
    for organization in organizations:
        result.append(
            {
                "id": organization.id,
                "name": organization.name,
                "slug": organization.slug,
                "description": organization.description,
                "level": organization.level,
                "status": organization.status,
                "is_active": organization.is_active,
                "parent_id": organization.parent_id,
                "created_at": organization.created_at.isoformat()
                if organization.created_at
                else None,
                "updated_at": organization.updated_at.isoformat()
                if organization.updated_at
                else None,
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
        )

    return result


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

    # Delete organizations
    deleted_count = 0
    for organization_id in request.organization_ids:
        query = select(Organization).where(Organization.id == organization_id)
        result = await db.execute(query)
        organization = result.scalar_one_or_none()

        if organization:
            await db.delete(organization)
            deleted_count += 1

    await db.commit()

    # Log bulk deletion
    from overwatch.services.admin_service import AdminService

    admin_service = AdminService(db)
    await admin_service.log_admin_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_DELETE,
        resource_type="Organization",
        new_values={"count": deleted_count},
        ip_address=admin_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )
