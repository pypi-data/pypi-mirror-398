"""
Model introspection service for discovering SQLAlchemy models and their properties.
"""

from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    inspect,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapper, RelationshipProperty
from sqlalchemy.sql import sqltypes


class FieldInfo:
    """Information about a model field."""

    def __init__(self, name: str, column, mapper: Mapper):
        """
        Initialize field information.

        Args:
            name: Field name
            column: SQLAlchemy column
            mapper: SQLAlchemy mapper
        """
        self.name = name
        self.column = column
        self.mapper = mapper

        # Field type information
        self.type_name = self._get_type_name(column.type)
        self.python_type = self._get_python_type(column.type)
        self.is_nullable = column.nullable
        self.is_primary_key = column.primary_key
        self.is_foreign_key = bool(column.foreign_keys)
        self.is_unique = column.unique
        self.default = column.default
        self.server_default = column.server_default
        self.max_length = getattr(column.type, "length", None)

        # Enum-specific information
        if isinstance(column.type, Enum):
            self.choices = (
                list(column.type.enums) if hasattr(column.type, "enums") else []
            )
        else:
            self.choices = []

    def _get_type_name(self, column_type) -> str:
        """Get human-readable type name."""
        if isinstance(column_type, String):
            return "string"
        elif isinstance(column_type, Text):
            return "text"
        elif isinstance(column_type, Integer):
            return "integer"
        elif isinstance(column_type, (Float, Numeric)):
            return "number"
        elif isinstance(column_type, Boolean):
            return "boolean"
        elif isinstance(column_type, DateTime):
            return "datetime"
        elif isinstance(column_type, Date):
            return "date"
        elif isinstance(column_type, Time):
            return "time"
        elif isinstance(column_type, Enum):
            return "enum"
        elif isinstance(column_type, sqltypes.JSON):
            return "json"
        else:
            return "unknown"

    def _get_python_type(self, column_type) -> type:
        """Get Python type for column."""
        if isinstance(column_type, String):
            return str
        elif isinstance(column_type, Text):
            return str
        elif isinstance(column_type, Integer):
            return int
        elif isinstance(column_type, (Float, Numeric)):
            return float
        elif isinstance(column_type, Boolean):
            return bool
        elif isinstance(column_type, DateTime):
            return str  # Will be serialized as ISO string
        elif isinstance(column_type, Date):
            return str  # Will be serialized as ISO string
        elif isinstance(column_type, Time):
            return str  # Will be serialized as ISO string
        elif isinstance(column_type, Enum):
            return str
        else:
            return str

    def _extract_default_value(self) -> str | None:
        """Extract default value from both default and server_default."""
        # Check server_default first (for func.now() etc.)
        if self.server_default:
            if hasattr(self.server_default, 'arg'):
                return str(self.server_default.arg)
            elif hasattr(self.server_default, 'text'):
                return str(self.server_default.text)
            else:
                return str(self.server_default)

        # Check regular default
        if self.default:
            if hasattr(self.default, 'arg'):
                return str(self.default.arg)
            else:
                return str(self.default)

        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.type_name,
            "python_type": self.python_type.__name__,
            "nullable": self.is_nullable,
            "primary_key": self.is_primary_key,
            "foreign_key": self.is_foreign_key,
            "unique": self.is_unique,
            "default": self._extract_default_value(),
            "max_length": self.max_length,
            "choices": self.choices,
        }


class RelationshipInfo:
    """Information about a model relationship."""

    def __init__(
        self, name: str, relationship_prop: RelationshipProperty, mapper: Mapper
    ):
        """
        Initialize relationship information.

        Args:
            name: Relationship name
            relationship_prop: SQLAlchemy relationship property
            mapper: SQLAlchemy mapper
        """
        self.name = name
        self.relationship_prop = relationship_prop
        self.mapper = mapper

        # Relationship type
        self.direction = relationship_prop.direction.name
        self.is_collection = relationship_prop.uselist
        self.target_model = relationship_prop.mapper.class_.__name__
        self.back_populates = getattr(relationship_prop, "back_populates", None)

        # Foreign key information
        self.foreign_keys = []
        if relationship_prop.local_columns:
            self.foreign_keys = [col.key for col in relationship_prop.local_columns]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "direction": self.direction,
            "is_collection": self.is_collection,
            "target_model": self.target_model,
            "back_populates": self.back_populates,
            "foreign_keys": self.foreign_keys,
        }


class ModelInfo:
    """Information about a SQLAlchemy model."""

    def __init__(self, model_class: type[DeclarativeBase]):
        """
        Initialize model information.

        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
        self.name = model_class.__name__
        self.table_name = model_class.__tablename__
        self.mapper = inspect(model_class)

        # Extract field information
        self.fields: dict[str, FieldInfo] = {}
        for column_name, column in self.mapper.columns.items():
            self.fields[column_name] = FieldInfo(column_name, column, self.mapper)

        # Extract relationship information
        self.relationships: dict[str, RelationshipInfo] = {}
        for name, relationship_prop in self.mapper.relationships.items():
            self.relationships[name] = RelationshipInfo(
                name, relationship_prop, self.mapper
            )

    def get_primary_key_fields(self) -> list[str]:
        """Get list of primary key field names."""
        return [name for name, field in self.fields.items() if field.is_primary_key]

    def get_foreign_key_fields(self) -> list[str]:
        """Get list of foreign key field names."""
        return [name for name, field in self.fields.items() if field.is_foreign_key]

    def get_simple_fields(self) -> list[str]:
        """Get list of simple (non-relationship) field names."""
        return list(self.fields.keys())

    def get_listable_fields(self) -> list[str]:
        """Get list of fields suitable for list display."""
        # Exclude large text fields and relationships by default
        excluded_types = ["text", "json"]
        return [
            name
            for name, field in self.fields.items()
            if not (field.is_primary_key and name == "id")
            and field.type_name not in excluded_types
        ]

    def get_searchable_fields(self) -> list[str]:
        """Get list of fields suitable for search."""
        searchable_types = ["string", "text"]
        return [
            name
            for name, field in self.fields.items()
            if field.type_name in searchable_types
            and not isinstance(field.column.type, Enum)
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "table_name": self.table_name,
            "fields": {name: field.to_dict() for name, field in self.fields.items()},
            "relationships": {
                name: rel.to_dict() for name, rel in self.relationships.items()
            },
            "primary_key_fields": self.get_primary_key_fields(),
            "foreign_key_fields": self.get_foreign_key_fields(),
            "listable_fields": self.get_listable_fields(),
            "searchable_fields": self.get_searchable_fields(),
        }


class ModelIntrospector:
    """Service for introspecting SQLAlchemy models."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize model introspector.

        Args:
            db_session: Database session
        """
        self.db_session = db_session

    async def inspect_model(self, model_class: type[DeclarativeBase]) -> ModelInfo:
        """
        Inspect a SQLAlchemy model.

        Args:
            model_class: SQLAlchemy model class

        Returns:
            Model information
        """
        return ModelInfo(model_class)

    async def inspect_models(
        self, model_classes: list[type[DeclarativeBase]]
    ) -> dict[str, ModelInfo]:
        """
        Inspect multiple SQLAlchemy models.

        Args:
            model_classes: List of SQLAlchemy model classes

        Returns:
            Dictionary mapping model names to model information
        """
        models_info: dict[str, ModelInfo] = {}
        for model_class in model_classes:
            models_info[model_class.__name__] = await self.inspect_model(model_class)
        return models_info

    def get_model_field_names(self, model_class: type[DeclarativeBase]) -> list[str]:
        """
        Get field names for a model.

        Args:
            model_class: SQLAlchemy model class

        Returns:
            List of field names
        """
        mapper = inspect(model_class)
        return list(mapper.columns.keys())

    def get_model_relationship_names(
        self, model_class: type[DeclarativeBase]
    ) -> list[str]:
        """
        Get relationship names for a model.

        Args:
            model_class: SQLAlchemy model class

        Returns:
            List of relationship names
        """
        mapper = inspect(model_class)
        return list(mapper.relationships.keys())

    def is_overwatch_model(self, model_class: type[DeclarativeBase]) -> bool:
        """
        Check if a model is an Overwatch internal model.

        Args:
            model_class: SQLAlchemy model class

        Returns:
            True if it's an Overwatch model
        """
        return hasattr(
            model_class, "__tablename__"
        ) and model_class.__tablename__.startswith("overwatch_")
