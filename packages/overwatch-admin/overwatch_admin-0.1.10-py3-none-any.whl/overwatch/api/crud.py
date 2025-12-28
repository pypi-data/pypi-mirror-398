"""
Dynamic CRUD API endpoints for SQLAlchemy models.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.core.database import get_db_session
from overwatch.models.admin import Admin
from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.schemas.crud import (
    BulkCreateRequest,
    BulkDeleteRequest,
    BulkUpdateRequest,
    PaginatedResponse,
    create_response_schema,
)
from overwatch.services.crud_service import CRUDService
from overwatch.services.introspection import ModelInfo
from overwatch.services.permission_service import PermissionService
from overwatch.utils.export import export_data

from .auth import get_current_admin_required


def create_crud_router(
    model_class: type,
    model_info: ModelInfo,
    prefix: str = "",
) -> APIRouter:
    """
    Create CRUD router for a specific model.

    Args:
        model_class: SQLAlchemy model class
        model_info: Model information
        prefix: URL prefix for routes

    Returns:
        FastAPI router with CRUD endpoints
    """
    router = APIRouter(prefix=prefix, tags=[model_info.name])

    # Create response schema for this model
    ResponseSchema = create_response_schema(model_class, model_info)

    def _serialize_item(item):
        """Helper function to serialize item with datetime conversion."""
        item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith("_")}
        # Convert datetime objects to ISO strings
        for key, value in item_dict.items():
            if hasattr(value, "isoformat"):  # Check if it's a datetime-like object
                item_dict[key] = value.isoformat()
        return item_dict

    def _get_fields_data_excluding_auto_timestamps():
        """Helper function to get fields data excluding datetime fields with defaults."""
        fields_data = model_info.to_dict()

        # Filter out datetime fields with default values (auto-timestamps)
        filtered_fields = {}
        for field_name, field_info in fields_data["fields"].items():
            # Skip datetime fields that have default values (typically created_at, updated_at)
            if (
                field_info["type"] == "datetime"
                and field_info["default"] is not None
                and "now" in str(field_info["default"]).lower()
            ):
                continue
            filtered_fields[field_name] = field_info

        fields_data["fields"] = filtered_fields
        return fields_data

    @router.get("", response_model=PaginatedResponse[ResponseSchema])
    async def list_items(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(25, ge=1, le=100),
        search: str | None = Query(None),
        sort_by: str | None = Query(None),
        sort_direction: str = Query("asc", regex="^(asc|desc)$"),
        filters: dict[str, Any] = Depends(lambda: {}),
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ) -> dict[str, Any]:
        """
        Get list of items with pagination and filtering.
        """
        # Check permissions
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, f"read:{model_info.name.lower()}"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to read {model_info.name}",
            )

        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        # Parse filters from query parameters
        query_filters = {}
        for key, value in request.query_params.items():
            if key not in ["page", "per_page", "search", "sort_by", "sort_direction"]:
                query_filters[key] = value

        # Get items
        items, total = await crud_service.get_list(
            page=page,
            per_page=per_page,
            search=search,
            sort_by=sort_by,
            sort_direction=sort_direction,
            filters=query_filters,
        )

        # Convert to response schemas
        items_response = [
            ResponseSchema.model_validate(_serialize_item(item)) for item in items
        ]

        # Calculate pagination info
        pages = (total + per_page - 1) // per_page

        # Get model fields information (excluding auto-timestamps)
        fields_data = _get_fields_data_excluding_auto_timestamps()

        # Add endpoint information for foreign key fields
        for field_name, field_info in fields_data["fields"].items():
            # Handle choices and defaults
            if field_info["choices"]:
                if field_info["default"]:
                    if "." in field_info["default"]:
                        parts = field_info["default"].split(".")
                        if len(parts) > 1:
                            field_info["default"] = parts[-1]

            # Add endpoint for foreign key fields
            if field_info["foreign_key"]:
                # Extract table name from foreign key field name (remove _id suffix)
                if field_name.endswith("_id"):
                    table_name = field_name[:-3]  # Remove "_id" suffix
                    # Convert to kebab-case for URL (handle both underscores and camelCase)
                    import re

                    # First replace underscores with hyphens, then handle camelCase
                    model_name = table_name.replace("_", "-")
                    model_name = re.sub("(?<!^)(?=[A-Z])", "-", model_name).lower()
                    field_info["model_name"] = model_name

        return {
            "items": items_response,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
            "metadata": fields_data,
        }

    @router.get("/fields")
    async def get_fields(
        current_admin: Admin = Depends(get_current_admin_required),
    ) -> dict[str, Any]:
        """
        Get model field information.
        """
        # Get model fields information (excluding auto-timestamps)
        fields_data = _get_fields_data_excluding_auto_timestamps()

        for field_name, field_info in fields_data["fields"].items():
            if field_info["choices"]:  # Check if field has choices (regardless of type)
                # Update default to use the value instead of enum class name
                if field_info["default"]:
                    # Check if default contains enum class notation
                    if "." in field_info["default"]:
                        # Extract the value part after the last dot
                        parts = field_info["default"].split(".")
                        if len(parts) > 1:
                            field_info["default"] = parts[-1]

            # Add endpoint for foreign key fields
            if field_info["foreign_key"]:
                # Extract table name from foreign key field name (remove _id suffix)
                if field_name.endswith("_id"):
                    table_name = field_name[:-3]  # Remove "_id" suffix
                    # Convert to kebab-case for URL (handle both underscores and camelCase)
                    import re

                    # First replace underscores with hyphens, then handle camelCase
                    endpoint = table_name.replace("_", "-")
                    endpoint = re.sub("(?<!^)(?=[A-Z])", "-", endpoint).lower()
                    field_info["endpoint"] = f"/{endpoint}"

        return fields_data

    @router.post("/bulk", response_model=list[ResponseSchema])
    async def bulk_create_items(
        request: BulkCreateRequest,
        http_request: Request,
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ) -> list[Any]:
        """
        Create multiple items.
        """
        # Check permissions
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, f"write:{model_info.name.lower()}"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to create {model_info.name}",
            )

        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        try:
            # Create items
            items = await crud_service.bulk_create(
                items_data=request.items,
                admin_id=getattr(current_admin, "id", None),
                ip_address=admin_service._get_client_ip(http_request),
                user_agent=http_request.headers.get("user-agent"),
            )

            return [
                ResponseSchema.model_validate(_serialize_item(item)) for item in items
            ]
        except ValueError as e:
            # Handle validation errors from CRUD service
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            ) from e

    @router.put("/bulk", response_model=list[ResponseSchema])
    async def bulk_update_items(
        request: BulkUpdateRequest,
        http_request: Request,
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ) -> list[Any]:
        """
        Update multiple items.
        """
        # Check permissions
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, f"write:{model_info.name.lower()}"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to update {model_info.name}",
            )

        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        try:
            # Update items
            items = await crud_service.bulk_update(
                item_ids=request.item_ids,
                data=request.updates,
                admin_id=getattr(current_admin, "id", None),
                ip_address=admin_service._get_client_ip(http_request),
                user_agent=http_request.headers.get("user-agent"),
            )

            return [
                ResponseSchema.model_validate(_serialize_item(item)) for item in items
            ]
        except ValueError as e:
            # Handle validation errors from CRUD service
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            ) from e

    @router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
    async def bulk_delete_items(
        request: BulkDeleteRequest,
        http_request: Request,
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ) -> None:
        """
        Delete multiple items.
        """
        # Check permissions
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, f"delete:{model_info.name.lower()}"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to delete {model_info.name}",
            )

        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        # Delete items
        deleted_count = await crud_service.bulk_delete(
            item_ids=request.item_ids,
            admin_id=getattr(current_admin, "id", None),
            ip_address=admin_service._get_client_ip(http_request),
            user_agent=http_request.headers.get("user-agent"),
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No items found to delete",
            )

    @router.get("/{item_id}", response_model=ResponseSchema)
    async def get_item(
        item_id: str,
        request: Request,
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ) -> Any:
        """
        Get single item by ID.
        """
        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        # Get item
        item = await crud_service.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model_info.name} not found",
            )

        # Log read action if audit is enabled
        audit_enabled = False
        log_reads = False
        if hasattr(model_info, "config") and hasattr(model_info.config, "audit"):
            audit_enabled = getattr(model_info.config.audit, "enabled", False)
            log_reads = getattr(model_info.config.audit, "log_reads", False)

        if audit_enabled and log_reads:
            # Convert string ID to int if possible, otherwise keep as None
            try:
                resource_id = int(item_id)
            except (ValueError, TypeError):
                resource_id = None

            await admin_service.log_admin_action(
                admin_id=getattr(current_admin, "id", None),
                action=OverwatchAuditAction.READ,
                resource_type=model_info.name,
                resource_id=resource_id,
                ip_address=admin_service._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )

        return ResponseSchema.model_validate(_serialize_item(item))

    @router.post("", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
    async def create_item(
        item_data: dict[str, Any],
        request: Request,
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ) -> Any:
        """
        Create new item.
        """
        # Check permissions
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, f"write:{model_info.name.lower()}"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to create {model_info.name}",
            )

        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        try:
            # Create item
            item = await crud_service.create(
                data=item_data,
                admin_id=getattr(current_admin, "id", None),
                ip_address=admin_service._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )

            return ResponseSchema.model_validate(_serialize_item(item))
        except ValueError as e:
            # Handle validation errors from CRUD service
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            ) from e

    @router.put("/{item_id}", response_model=ResponseSchema)
    async def update_item(
        item_id: str,
        item_data: dict[str, Any],
        request: Request,
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ) -> Any:
        """
        Update existing item.
        """
        # Check permissions
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, f"write:{model_info.name.lower()}"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to update {model_info.name}",
            )

        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        # Convert string ID to int if possible
        try:
            item_id_int = int(item_id)
        except (ValueError, TypeError):
            item_id_int = item_id

        try:
            # Update item
            item = await crud_service.update(
                item_id=item_id_int,
                data=item_data,
                admin_id=getattr(current_admin, "id", None),
                ip_address=admin_service._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{model_info.name} not found",
                )

            return ResponseSchema.model_validate(_serialize_item(item))
        except ValueError as e:
            # Handle validation errors from CRUD service
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            ) from e

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_item(
        item_id: str,
        request: Request,
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ) -> None:
        """
        Delete item.
        """
        # Check permissions
        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            current_admin, f"delete:{model_info.name.lower()}"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to delete {model_info.name}",
            )

        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        # Convert string ID to int if possible
        try:
            item_id_int = int(item_id)
        except (ValueError, TypeError):
            item_id_int = item_id

        # Delete item
        deleted = await crud_service.delete(
            item_id=item_id_int,
            admin_id=getattr(current_admin, "id", None),
            ip_address=admin_service._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model_info.name} not found",
            )

    @router.get("/export")
    async def export_items(
        request: Request,
        format: str = Query("csv", regex="^(csv|json|xlsx)$"),
        current_admin: Admin = Depends(get_current_admin_required),
        db: AsyncSession = Depends(get_db_session),
    ):
        """
        Export items in various formats.
        """
        # Get CRUD service
        from overwatch.services.admin_service import AdminService

        admin_service = AdminService(db)
        crud_service = CRUDService(db, model_class, model_info, admin_service)

        # Get all items (no pagination for export)
        items, _ = await crud_service.get_list(per_page=10000)  # Large limit for export

        # Export data
        file_path = await export_data(items, format, model_info)

        # Log export action
        await admin_service.log_admin_action(
            admin_id=getattr(current_admin, "id", None),
            action=OverwatchAuditAction.EXPORT,
            resource_type=model_info.name,
            new_values={"format": format, "count": len(items)},
            ip_address=admin_service._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )

        # Return file
        from fastapi.responses import FileResponse

        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=f"{model_info.name}_export.{format}",
        )

    return router
