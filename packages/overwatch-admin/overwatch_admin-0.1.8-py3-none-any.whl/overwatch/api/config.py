"""
Configuration management API endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin
from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.schemas.config import (
    ConfigBulkCreate,
    ConfigBulkDelete,
    ConfigBulkUpdate,
    ConfigCreate,
    ConfigListResponse,
    ConfigResponse,
    ConfigUpdate,
    PublicConfigResponse,
)
from overwatch.services.config_service import ConfigService

from .auth import get_current_admin_required

router = APIRouter(tags=["Overwatch Config"])


@router.get("/public", response_model=PublicConfigResponse)
async def get_public_config(
    db: AsyncSession = Depends(get_db_session),
) -> PublicConfigResponse:
    """
    Get public configuration for frontend consumption.
    """
    config_service = ConfigService(db)
    public_configs = await config_service.get_public_configs()

    return PublicConfigResponse(
        admin_title=public_configs.get("admin_title", "Overwatch Admin"),
        logo_url=public_configs.get("logo_url"),
        favicon_url=public_configs.get("favicon_url"),
        overwatch_theme_primary_color=public_configs.get("overwatch_theme_primary_color"),
        overwatch_theme_secondary_color=public_configs.get("overwatch_theme_secondary_color"),
        overwatch_theme_mode=public_configs.get("overwatch_theme_mode"),
    )


@router.get("", response_model=ConfigListResponse)
async def list_configs(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=1000),
    search: str | None = Query(None),
    category: str | None = Query(None),
    is_public: bool | None = Query(None),
    sort_by: str = Query("key"),
    sort_direction: str = Query("asc", regex="^(asc|desc)$"),
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get list of configurations with pagination and filtering.
    """
    config_service = ConfigService(db)

    # Check permissions
    if not current_admin.has_permission("read:config"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view configurations",
        )

    # Get configs
    configs, total = await config_service.get_config_list(
        page=page,
        per_page=per_page,
        search=search,
        category=category,
        is_public=is_public,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )

    # Convert to response schemas
    configs_response = [ConfigResponse.model_validate(config) for config in configs]

    # Calculate pagination info
    pages = (total + per_page - 1) // per_page

    # Add metadata about the config fields
    metadata = {
        "fields": {
            "id": {"type": "integer", "nullable": False},
            "key": {"type": "string", "nullable": False},
            "value": {"type": "string", "nullable": True},
            "description": {"type": "string", "nullable": True},
            "is_public": {"type": "boolean", "nullable": False},
            "category": {"type": "string", "nullable": True},
            "data_type": {"type": "string", "nullable": False},
            "created_at": {"type": "datetime", "nullable": False},
            "updated_at": {"type": "datetime", "nullable": False},
            "updated_by": {"type": "integer", "nullable": True},
        },
        "sortable_fields": [
            "id",
            "key",
            "value",
            "is_public",
            "category",
            "data_type",
            "created_at",
            "updated_at",
        ],
        "filterable_fields": ["category", "is_public"],
        "categories": ["ui", "security", "features", "system"],
    }

    return {
        "items": configs_response,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "metadata": metadata,
    }


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Get configuration by key.
    """
    config_service = ConfigService(db)

    # Check permissions
    if not current_admin.has_permission("read:config"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view configuration",
        )

    # Get config
    config = await config_service.get_config_by_key(key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    # Log read action
    await config_service.log_config_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.READ,
        resource_type="Config",
        resource_id=getattr(config, "id", None),
        ip_address=config_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return config


@router.post("", response_model=ConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    config_data: ConfigCreate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Create new configuration.
    """
    config_service = ConfigService(db)

    # Check permissions
    if not current_admin.has_permission("write:config"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create configurations",
        )

    try:
        # Create config
        config = await config_service.create_config(
            key=config_data.key,
            value=config_data.value,
            description=config_data.description,
            is_public=config_data.is_public,
            category=config_data.category,
            data_type=config_data.data_type,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log creation
    await config_service.log_config_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.CREATE,
        resource_type="Config",
        resource_id=getattr(config, "id", None),
        new_values={
            "key": config_data.key,
            "value": config_data.value,
            "is_public": config_data.is_public,
            "category": config_data.category,
        },
        ip_address=config_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return config


@router.put("/{key}", response_model=ConfigResponse)
async def update_config(
    key: str,
    config_data: ConfigUpdate,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Update configuration.
    """
    config_service = ConfigService(db)

    # Check permissions
    if not current_admin.has_permission("write:config"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update configurations",
        )

    # Get existing config
    existing_config = await config_service.get_config_by_key(key)
    if not existing_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    # Update config
    try:
        config = await config_service.update_config(
            key=key,
            updates=config_data,
            updated_by=getattr(current_admin, "id", None),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Log update
    await config_service.log_config_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.UPDATE,
        resource_type="Config",
        resource_id=getattr(config, "id", None),
        new_values=config_data.model_dump(exclude_unset=True),
        ip_address=config_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return config


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    key: str,
    request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete configuration.
    """
    config_service = ConfigService(db)

    # Check permissions
    if not current_admin.has_permission("delete:config"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete configurations",
        )

    # Get existing config
    existing_config = await config_service.get_config_by_key(key)
    if not existing_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    # Delete config
    await config_service.delete_config(key)

    # Log deletion
    await config_service.log_config_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.DELETE,
        resource_type="Config",
        resource_id=getattr(existing_config, "id", None),
        old_values={"key": getattr(existing_config, "key", None)},
        ip_address=config_service._get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/bulk", response_model=list[ConfigResponse])
async def bulk_create_configs(
    request: ConfigBulkCreate,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[Any]:
    """
    Create multiple configurations.
    """
    config_service = ConfigService(db)

    # Check permissions
    if not current_admin.has_permission("write:config"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create configurations",
        )

    # Create configs
    configs = await config_service.bulk_create_configs(request.configs)

    # Log bulk creation
    await config_service.log_config_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_CREATE,
        resource_type="Config",
        new_values={"count": len(configs)},
        ip_address=config_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )

    return configs


@router.put("/bulk", response_model=list[ConfigResponse])
async def bulk_update_configs(
    request: ConfigBulkUpdate,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> list[Any]:
    """
    Update multiple configurations.
    """
    config_service = ConfigService(db)

    # Check permissions
    if not current_admin.has_permission("write:config"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update configurations",
        )

    # Update configs
    configs = await config_service.bulk_update_configs(
        keys=request.keys,
        updates=request.updates,
        updated_by=getattr(current_admin, "id", None),
    )

    # Log bulk update
    await config_service.log_config_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_UPDATE,
        resource_type="Config",
        new_values={"count": len(configs)},
        ip_address=config_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )

    return configs


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_configs(
    request: ConfigBulkDelete,
    http_request: Request,
    current_admin: Admin = Depends(get_current_admin_required),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete multiple configurations.
    """
    config_service = ConfigService(db)

    # Check permissions
    if not current_admin.has_permission("delete:config"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete configurations",
        )

    # Delete configs
    deleted_count = await config_service.bulk_delete_configs(request.keys)

    # Log bulk deletion
    await config_service.log_config_action(
        admin_id=getattr(current_admin, "id", None),
        action=OverwatchAuditAction.BULK_DELETE,
        resource_type="Config",
        new_values={"count": deleted_count},
        ip_address=config_service._get_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )
