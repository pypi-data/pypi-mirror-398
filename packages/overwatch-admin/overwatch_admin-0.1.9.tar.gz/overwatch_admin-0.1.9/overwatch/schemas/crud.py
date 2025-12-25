"""
Pydantic schemas for CRUD operations.
"""

from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel, Field, create_model
from pydantic.config import ConfigDict
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    metadata: dict[str, Any] = Field(
        ..., description="Model metadata including field information"
    )


class BulkCreateRequest(BaseModel):
    """Bulk create request schema."""

    items: list[dict[str, Any]] = Field(..., min_length=1, max_length=100)


class BulkUpdateRequest(BaseModel):
    """Bulk update request schema."""

    item_ids: list[int] = Field(..., min_length=1, max_length=100)
    updates: dict[str, Any] = Field(...)


class BulkDeleteRequest(BaseModel):
    """Bulk delete request schema."""

    item_ids: list[int] = Field(..., min_length=1, max_length=100)


class ExportRequest(BaseModel):
    """Export request schema."""

    format: str = Field("csv", pattern="^(csv|json|xlsx)$")
    filters: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    """Search request schema."""

    search: str | None = Field(None, min_length=1)
    filters: dict[str, Any] = Field(default_factory=dict)
    page: int = Field(1, ge=1)
    per_page: int = Field(25, ge=1, le=100)
    sort_by: str | None = None
    sort_direction: str = Field("asc", pattern="^(asc|desc)$")


def create_response_schema(
    model_class: type[DeclarativeBase], model_info
) -> type[BaseModel]:
    """
    Create a response schema for a SQLAlchemy model.

    Args:
        model_class: SQLAlchemy model class
        model_info: Model information with field details

    Returns:
        Pydantic model class for response
    """
    fields: dict[str, tuple[Any, Any]] = {}

    if hasattr(model_info, "fields"):
        model_fields = {
            name: field.to_dict() for name, field in model_info.fields.items()
        }
    else:
        model_fields = {}
        for column in model_class.__table__.columns:
            model_fields[column.name] = {
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
            }

    for field_name, field_info in model_fields.items():
        # if field_name in ["password_hash", "password"]:
        #     continue

        field_type = str(field_info.get("type", "string")).lower()
        nullable = field_info.get("nullable", False)

        if "int" in field_type or field_name == "id":
            pydantic_type = int | None if nullable else int
        elif "bool" in field_type:
            pydantic_type = bool | None if nullable else bool
        elif "float" in field_type or "decimal" in field_type:
            pydantic_type = float | None if nullable else float
        elif "datetime" in field_type or "timestamp" in field_type:
            pydantic_type = str | None if nullable else str
        elif "json" in field_type:
            pydantic_type = dict[str, Any] | None if nullable else dict[str, Any]
        else:
            pydantic_type = str | None if nullable else str

        fields[field_name] = (pydantic_type, None if nullable else ...)

    schema = create_model(
        f"{model_class.__name__}Response",
        __base__=BaseModel,
        **cast(dict[str, Any], fields),
    )

    # Configure to allow creation from ORM objects
    schema.model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )
    return schema


def create_create_schema(
    model_class: type[DeclarativeBase], model_info
) -> type[BaseModel]:
    """
    Create a creation schema for a SQLAlchemy model.

    Args:
        model_class: SQLAlchemy model class
        model_info: Model information with field details

    Returns:
        Pydantic model class for creation
    """
    fields: dict[str, tuple[Any, Any]] = {}

    if hasattr(model_info, "fields"):
        model_fields = {
            name: field.to_dict() for name, field in model_info.fields.items()
        }
    else:
        model_fields = {}
        for column in model_class.__table__.columns:
            model_fields[column.name] = {
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "autoincrement": getattr(column, "autoincrement", False),
            }

    # Create field definitions
    for field_name, field_info in model_fields.items():
        # Skip auto-increment primary keys and sensitive fields
        # if field_info.get("autoincrement") or field_name in [
        #     "password_hash",
        #     "password",
        # ]:
        #     continue

        # Determine field type
        field_type = str(field_info.get("type", "string")).lower()
        nullable = field_info.get("nullable", False)

        if "int" in field_type:
            pydantic_type = int | None if nullable else int
        elif "bool" in field_type:
            pydantic_type = bool | None if nullable else bool
        elif "float" in field_type or "decimal" in field_type:
            pydantic_type = float | None if nullable else float
        elif "datetime" in field_type or "timestamp" in field_type:
            pydantic_type = str | None if nullable else str
        elif "json" in field_type:
            pydantic_type = dict[str, Any] | None if nullable else dict[str, Any]
        else:
            pydantic_type = str | None if nullable else str

        default = None if nullable or field_info.get("default") is not None else ...
        fields[field_name] = (pydantic_type, default)

    schema = create_model(
        f"{model_class.__name__}Create",
        __base__=BaseModel,
        **cast(dict[str, Any], fields),
    )

    return schema


def create_update_schema(
    model_class: type[DeclarativeBase], model_info
) -> type[BaseModel]:
    """
    Create an update schema for a SQLAlchemy model.

    Args:
        model_class: SQLAlchemy model class
        model_info: Model information with field details

    Returns:
        Pydantic model class for updates
    """
    fields: dict[str, tuple[type, Any]] = {}

    # Get model fields
    if hasattr(model_info, "fields"):
        model_fields = {
            name: field.to_dict() for name, field in model_info.fields.items()
        }
    else:
        model_fields = {}
        for column in model_class.__table__.columns:
            model_fields[column.name] = {
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "autoincrement": getattr(column, "autoincrement", False),
            }

    # Create field definitions (all optional for updates)
    for field_name, field_info in model_fields.items():
        # Skip primary keys and sensitive fields
        if field_info.get("primary_key") or field_name in ["password_hash", "password"]:
            continue

        # Determine field type
        field_type = str(field_info.get("type", "string")).lower()

        if "int" in field_type:
            pydantic_type = int | None
        elif "bool" in field_type:
            pydantic_type = bool | None
        elif "float" in field_type or "decimal" in field_type:
            pydantic_type = float | None
        elif "datetime" in field_type or "timestamp" in field_type:
            pydantic_type = str | None
        elif "json" in field_type:
            pydantic_type = dict[str, Any] | None
        else:
            pydantic_type = str | None

        # Add field to schema (all optional)
        fields[field_name] = (pydantic_type, None)

    # Create the model
    schema = create_model(
        f"{model_class.__name__}Update",
        __base__=BaseModel,
        **cast(dict[str, Any], fields),
    )

    return schema


class ModelInfoResponse(BaseModel):
    """Model information response schema."""

    name: str = Field(..., description="Model name")
    table_name: str = Field(..., description="Database table name")
    fields: dict[str, dict[str, Any]] = Field(..., description="Field information")
    primary_keys: list[str] = Field(..., description="Primary key fields")
    searchable_fields: list[str] = Field(..., description="Fields that can be searched")
    sortable_fields: list[str] = Field(..., description="Fields that can be sorted")


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response schema."""

    total_models: int = Field(..., description="Total number of models")
    total_records: dict[str, int] = Field(..., description="Total records per model")
    system_stats: dict[str, Any] = Field(..., description="System statistics")


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Health status")
    database: str = Field(..., description="Database status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Overwatch version")
