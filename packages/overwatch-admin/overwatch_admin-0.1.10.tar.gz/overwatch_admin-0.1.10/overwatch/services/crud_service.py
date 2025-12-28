"""
Dynamic CRUD service for SQLAlchemy models.
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.services.admin_service import AdminService
from overwatch.services.introspection import ModelInfo
from overwatch.utils.datetime_utils import convert_datetimes_in_data


class CRUDService:
    """Dynamic CRUD service for any SQLAlchemy model."""

    def __init__(
        self,
        db_session: AsyncSession,
        model_class: type[DeclarativeBase],
        model_info: ModelInfo,
        admin_service: AdminService,
    ):
        """
        Initialize CRUD service.

        Args:
            db_session: Database session
            model_class: SQLAlchemy model class
            model_info: Model information
            admin_service: Admin service for audit logging
        """
        self.db_session = db_session
        self.model_class = model_class
        self.model_info = model_info
        self.admin_service = admin_service

    async def get_list(
        self,
        page: int = 1,
        per_page: int = 25,
        search: str | None = None,
        sort_by: str | None = None,
        sort_direction: str = "asc",
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[DeclarativeBase], int]:
        """
        Get list of model instances with pagination and filtering.

        Args:
            page: Page number
            per_page: Items per page
            search: Search query
            sort_by: Field to sort by
            sort_direction: Sort direction (asc/desc)
            filters: Dictionary of filters

        Returns:
            Tuple of (items list, total count)
        """
        query = select(self.model_class)

        # Apply search
        if search:
            search_conditions = []
            searchable_fields = self.model_info.get_searchable_fields()

            for field_name in searchable_fields:
                field = self.model_info.fields.get(field_name)

                if field and field.type_name in [
                    "string",
                    "text",
                ]:  # Double-check field types
                    field_attr = getattr(self.model_class, field_name)
                    search_conditions.append(field_attr.ilike(f"%{search}%"))

            if search_conditions:
                from sqlalchemy import or_

                query = query.where(or_(*search_conditions))

        # Apply filters
        if filters:
            for field_name, value in filters.items():
                if hasattr(self.model_class, field_name):
                    field_attr = getattr(self.model_class, field_name)
                    if isinstance(value, list):
                        query = query.where(field_attr.in_(value))
                    else:
                        query = query.where(field_attr == value)

        # Get total count - use the same query conditions without offset/limit
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db_session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if sort_by and hasattr(self.model_class, sort_by):
            sort_attr = getattr(self.model_class, sort_by)
            if sort_direction.lower() == "desc":
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        else:
            # Default sort by primary key
            pk_fields = self.model_info.get_primary_key_fields()
            if pk_fields:
                pk_attr = getattr(self.model_class, pk_fields[0])
                query = query.order_by(pk_attr.asc())

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Execute query
        result = await self.db_session.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def get_by_id(self, item_id: int | str) -> DeclarativeBase | None:
        """
        Get model instance by ID.

        Args:
            item_id: Item ID

        Returns:
            Model instance or None
        """
        pk_fields = self.model_info.get_primary_key_fields()
        if not pk_fields:
            return None

        query = select(self.model_class)
        # Use only the first primary key field for simplicity
        pk_field = pk_fields[0]
        pk_attr = getattr(self.model_class, pk_field)

        # Cast item_id to the correct type based on the field type
        field_info = self.model_info.fields[pk_field]
        if field_info.type_name in ["integer", "bigint"]:
            try:
                casted_id = int(item_id)
            except (ValueError, TypeError):
                return None
        else:
            casted_id = item_id

        query = query.where(pk_attr == casted_id)

        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        data: dict[str, Any],
        admin_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> DeclarativeBase:
        """
        Create new model instance.

        Args:
            data: Dictionary of field values
            admin_id: Admin ID for audit logging
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created model instance
        """
        # Filter out non-model fields
        filtered_data = {}
        for field_name, value in data.items():
            if hasattr(self.model_class, field_name):
                filtered_data[field_name] = value

        # Validate foreign key fields
        await self._validate_foreign_keys(filtered_data)

        # Convert datetime strings to datetime objects
        datetime_fields = self._get_datetime_fields()
        filtered_data = convert_datetimes_in_data(filtered_data, datetime_fields)

        # Create instance
        instance = self.model_class(**filtered_data)

        try:
            self.db_session.add(instance)
            await self.db_session.commit()
            await self.db_session.refresh(instance)

            # Log to audit trail
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.CREATE,
                resource_type=self.model_info.name,
                resource_id=getattr(instance, "id", None),
                new_values=filtered_data,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return instance
        except IntegrityError as e:
            await self.db_session.rollback()

            # Parse the integrity error to provide more specific error messages
            error_message = str(e)
            if (
                "duplicate key" in error_message.lower()
                or "unique constraint" in error_message.lower()
            ):
                # Extract field name from error message if possible
                field_name = "unknown"
                if "nik" in error_message:
                    field_name = "nik"
                elif "username" in error_message:
                    field_name = "username"
                elif "email" in error_message:
                    field_name = "email"

                # Extract the duplicate value
                duplicate_value = "unknown"
                for key, value in filtered_data.items():
                    if key.lower() in error_message.lower():
                        duplicate_value = str(value)
                        break

                raise ValueError(
                    f"A {self.model_info.name.lower()} with {field_name} '{duplicate_value}' already exists."
                ) from e
            elif "foreign key constraint" in error_message.lower():
                raise ValueError(f"Referenced record does not exist: {error_message}") from e
            else:
                # Re-raise the original integrity error for other types
                raise
        except Exception as e:
            await self.db_session.rollback()

            # Log failed action
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.CREATE,
                resource_type=self.model_info.name,
                new_values=filtered_data,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e),
            )
            raise

    async def update(
        self,
        item_id: int | str,
        data: dict[str, Any],
        admin_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> DeclarativeBase | None:
        """
        Update model instance.

        Args:
            item_id: Item ID
            data: Dictionary of field values to update
            admin_id: Admin ID for audit logging
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Updated model instance or None if not found
        """
        # Get existing instance
        instance = await self.get_by_id(item_id)
        if not instance:
            return None

        # Store old values for audit
        old_values = {}
        for field_name in self.model_info.get_simple_fields():
            if hasattr(instance, field_name):
                old_values[field_name] = getattr(instance, field_name)

        # Filter out non-model fields
        filtered_data = {}
        for field_name, value in data.items():
            if hasattr(instance, field_name):
                filtered_data[field_name] = value

        # Validate foreign key fields
        await self._validate_foreign_keys(filtered_data)

        # Convert datetime strings to datetime objects
        datetime_fields = self._get_datetime_fields()
        filtered_data = convert_datetimes_in_data(filtered_data, datetime_fields)

        try:
            # Update fields
            for field_name, value in filtered_data.items():
                setattr(instance, field_name, value)

            await self.db_session.commit()
            await self.db_session.refresh(instance)

            # Log to audit trail
            # Convert string ID to int if possible for audit logging
            try:
                resource_id = int(item_id) if isinstance(item_id, str) else item_id
            except (ValueError, TypeError):
                resource_id = None

            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.UPDATE,
                resource_type=self.model_info.name,
                resource_id=resource_id,
                old_values=old_values,
                new_values=filtered_data,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return instance
        except IntegrityError as e:
            await self.db_session.rollback()

            # Parse the integrity error to provide more specific error messages
            error_message = str(e)
            if (
                "duplicate key" in error_message.lower()
                or "unique constraint" in error_message.lower()
            ):
                # Extract field name from error message if possible
                field_name = "unknown"
                if "nik" in error_message:
                    field_name = "nik"
                elif "username" in error_message:
                    field_name = "username"
                elif "email" in error_message:
                    field_name = "email"

                # Extract the duplicate value
                duplicate_value = "unknown"
                for key, value in filtered_data.items():
                    if key.lower() in error_message.lower():
                        duplicate_value = str(value)
                        break

                raise ValueError(
                    f"A {self.model_info.name.lower()} with {field_name} '{duplicate_value}' already exists."
                ) from e
            elif "foreign key constraint" in error_message.lower():
                raise ValueError(f"Referenced record does not exist: {error_message}") from e
            else:
                # Re-raise the original integrity error for other types
                raise
        except Exception as e:
            await self.db_session.rollback()

            # Log failed action
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.UPDATE,
                resource_type=self.model_info.name,
                resource_id=int(item_id),
                old_values=old_values,
                new_values=filtered_data,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e),
            )
            raise

    async def delete(
        self,
        item_id: int | str,
        admin_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """
        Delete model instance.

        Args:
            item_id: Item ID
            admin_id: Admin ID for audit logging
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            True if deleted, False if not found
        """
        # Get existing instance
        instance = await self.get_by_id(item_id)
        if not instance:
            return False

        # Store old values for audit
        old_values = {}
        for field_name in self.model_info.get_simple_fields():
            if hasattr(instance, field_name):
                old_values[field_name] = getattr(instance, field_name)

        try:
            await self.db_session.delete(instance)
            await self.db_session.commit()

            # Log to audit trail
            # Convert string ID to int if possible for audit logging
            try:
                resource_id = int(item_id) if isinstance(item_id, str) else item_id
            except (ValueError, TypeError):
                resource_id = None

            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.DELETE,
                resource_type=self.model_info.name,
                resource_id=resource_id,
                old_values=old_values,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return True
        except Exception as e:
            await self.db_session.rollback()

            # Log failed action
            # Convert string ID to int if possible for audit logging
            try:
                resource_id = int(item_id) if isinstance(item_id, str) else item_id
            except (ValueError, TypeError):
                resource_id = None

            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.DELETE,
                resource_type=self.model_info.name,
                resource_id=resource_id,
                old_values=old_values,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e),
            )
            raise

    async def bulk_create(
        self,
        items_data: list[dict[str, Any]],
        admin_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> list[DeclarativeBase]:
        """
        Create multiple model instances.

        Args:
            items_data: List of dictionaries with field values
            admin_id: Admin ID for audit logging
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            List of created model instances
        """
        instances = []

        # Get datetime fields for conversion
        datetime_fields = self._get_datetime_fields()

        try:
            for data in items_data:
                # Filter out non-model fields
                filtered_data = {}
                for field_name, value in data.items():
                    if hasattr(self.model_class, field_name):
                        filtered_data[field_name] = value

                # Validate foreign key fields
                await self._validate_foreign_keys(filtered_data)

                # Convert datetime strings to datetime objects
                filtered_data = convert_datetimes_in_data(
                    filtered_data, datetime_fields
                )

                instance = self.model_class(**filtered_data)
                instances.append(instance)
                self.db_session.add(instance)

            await self.db_session.commit()

            # Refresh all instances
            for instance in instances:
                await self.db_session.refresh(instance)

            # Log to audit trail
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.BULK_CREATE,
                resource_type=self.model_info.name,
                new_values={"count": len(instances), "items": items_data},
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return instances
        except IntegrityError as e:
            await self.db_session.rollback()

            # Parse the integrity error to provide more specific error messages
            error_message = str(e)
            if (
                "duplicate key" in error_message.lower()
                or "unique constraint" in error_message.lower()
            ):
                # Extract field name from error message if possible
                field_name = "unknown"
                if "nik" in error_message:
                    field_name = "nik"
                elif "username" in error_message:
                    field_name = "username"
                elif "email" in error_message:
                    field_name = "email"

                # Extract the duplicate value from the first item that caused the error
                duplicate_value = "unknown"
                if items_data:
                    for key, value in items_data[0].items():
                        if key.lower() in error_message.lower():
                            duplicate_value = str(value)
                            break

                raise ValueError(
                    f"A {self.model_info.name.lower()} with {field_name} '{duplicate_value}' already exists."
                ) from e
            elif "foreign key constraint" in error_message.lower():
                raise ValueError(f"Referenced record does not exist: {error_message}") from e
            else:
                # Re-raise the original integrity error for other types
                raise
        except Exception as e:
            await self.db_session.rollback()

            # Log failed action
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.BULK_CREATE,
                resource_type=self.model_info.name,
                new_values={"count": len(items_data), "items": items_data},
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e),
            )
            raise

    async def bulk_update(
        self,
        item_ids: list[int],
        data: dict[str, Any],
        admin_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> list[DeclarativeBase]:
        """
        Update multiple model instances.

        Args:
            item_ids: List of item IDs
            data: Dictionary of field values to update
            admin_id: Admin ID for audit logging
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            List of updated model instances
        """
        pk_fields = self.model_info.get_primary_key_fields()
        if not pk_fields:
            return []

        # Filter out non-model fields
        filtered_data = {}
        for field_name, value in data.items():
            if hasattr(self.model_class, field_name):
                filtered_data[field_name] = value

        # Validate foreign key fields
        await self._validate_foreign_keys(filtered_data)

        # Convert datetime strings to datetime objects
        datetime_fields = self._get_datetime_fields()
        filtered_data = convert_datetimes_in_data(filtered_data, datetime_fields)

        try:
            # Get existing instances
            pk_field = pk_fields[0]
            pk_attr = getattr(self.model_class, pk_field)

            # Cast item_ids to the correct type based on the field type
            field_info = self.model_info.fields[pk_field]
            if field_info.type_name in ["integer", "bigint"]:
                try:
                    casted_ids = [int(item_id) for item_id in item_ids]
                except (ValueError, TypeError):
                    return []
            else:
                casted_ids = item_ids

            query = select(self.model_class).where(pk_attr.in_(casted_ids))
            result = await self.db_session.execute(query)
            instances = result.scalars().all()

            # Update instances
            for instance in instances:
                for field_name, value in filtered_data.items():
                    setattr(instance, field_name, value)

            await self.db_session.commit()

            # Refresh all instances
            for instance in instances:
                await self.db_session.refresh(instance)

            # Log to audit trail
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.BULK_UPDATE,
                resource_type=self.model_info.name,
                new_values={
                    "count": len(instances),
                    "item_ids": item_ids,
                    "updates": filtered_data,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return list(instances)
        except IntegrityError as e:
            await self.db_session.rollback()

            # Parse the integrity error to provide more specific error messages
            error_message = str(e)
            if (
                "duplicate key" in error_message.lower()
                or "unique constraint" in error_message.lower()
            ):
                # Extract field name from error message if possible
                field_name = "unknown"
                if "nik" in error_message:
                    field_name = "nik"
                elif "username" in error_message:
                    field_name = "username"
                elif "email" in error_message:
                    field_name = "email"

                # Extract the duplicate value from the data
                duplicate_value = "unknown"
                for key, value in filtered_data.items():
                    if key.lower() in error_message.lower():
                        duplicate_value = str(value)
                        break

                raise ValueError(
                    f"A {self.model_info.name.lower()} with {field_name} '{duplicate_value}' already exists."
                ) from e
            elif "foreign key constraint" in error_message.lower():
                raise ValueError(f"Referenced record does not exist: {error_message}") from e
            else:
                # Re-raise the original integrity error for other types
                raise
        except Exception as e:
            await self.db_session.rollback()

            # Log failed action
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.BULK_UPDATE,
                resource_type=self.model_info.name,
                new_values={
                    "count": len(item_ids),
                    "item_ids": item_ids,
                    "updates": filtered_data,
                },
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e),
            )
            raise

    async def bulk_delete(
        self,
        item_ids: list[int],
        admin_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> int:
        """
        Delete multiple model instances.

        Args:
            item_ids: List of item IDs
            admin_id: Admin ID for audit logging
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Number of deleted instances
        """
        pk_fields = self.model_info.get_primary_key_fields()
        if not pk_fields:
            return 0

        # Get existing instances before deletion
        pk_field = pk_fields[0]
        pk_attr = getattr(self.model_class, pk_field)

        # Cast item_ids to the correct type based on the field type
        field_info = self.model_info.fields[pk_field]
        if field_info.type_name in ["integer", "bigint"]:
            try:
                casted_ids = [int(item_id) for item_id in item_ids]
            except (ValueError, TypeError):
                return 0
        else:
            casted_ids = item_ids

        query = select(self.model_class).where(pk_attr.in_(casted_ids))
        result = await self.db_session.execute(query)
        instances = result.scalars().all()

        if not instances:
            return 0

        try:
            # Delete instances
            for instance in instances:
                await self.db_session.delete(instance)

            await self.db_session.commit()

            # Log to audit trail
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.BULK_DELETE,
                resource_type=self.model_info.name,
                new_values={"count": len(instances), "item_ids": item_ids},
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return len(instances)
        except Exception as e:
            await self.db_session.rollback()

            # Log failed action
            await self.admin_service.log_admin_action(
                admin_id=admin_id,
                action=OverwatchAuditAction.BULK_DELETE,
                resource_type=self.model_info.name,
                new_values={"count": len(item_ids), "item_ids": item_ids},
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e),
            )
            raise

    async def _validate_foreign_keys(self, data: dict[str, Any]) -> None:
        """
        Validate foreign key fields to ensure they reference existing records.

        Args:
            data: Dictionary of field values to validate

        Raises:
            ValueError: If a foreign key references a non-existent record
        """
        from sqlalchemy import select

        foreign_key_fields = self.model_info.get_foreign_key_fields()

        for field_name in foreign_key_fields:
            if field_name in data and data[field_name] is not None:
                # Skip validation for 0 values as they typically indicate "no reference"
                if data[field_name] == 0:
                    if self.model_info.fields[field_name].is_nullable:
                        # Set to None instead of 0 if the field is nullable
                        data[field_name] = None
                    else:
                        raise ValueError(
                            f"Invalid foreign key value 0 for field '{field_name}'. "
                            f"Field is not nullable and must reference a valid record."
                        )
                    continue

                # Get the foreign key information
                field_info = self.model_info.fields[field_name]
                if field_info.column.foreign_keys:
                    # Get the target table and column from the foreign key
                    fk = list(field_info.column.foreign_keys)[0]
                    target_table = fk.column.table.name
                    target_column = fk.column.name

                    # Check if the referenced record exists
                    try:
                        # Import the Base class to get the metadata
                        from overwatch.core.database import Base

                        # Find the target model class by table name
                        target_model = None
                        for model_class in Base.registry._class_registry.values():
                            if (
                                hasattr(model_class, "__tablename__")
                                and model_class.__tablename__ == target_table
                            ):
                                target_model = model_class
                                break

                        if target_model:
                            # Query to check if the referenced record exists
                            query = select(target_model).where(
                                getattr(target_model, target_column) == data[field_name]
                            )
                            result = await self.db_session.execute(query)
                            exists = result.scalar_one_or_none()

                            if not exists:
                                raise ValueError(
                                    f"Foreign key constraint violation: {field_name}={data[field_name]} "
                                    f"references {target_table}.{target_column} which does not exist"
                                )
                    except Exception as e:
                        # If we can't validate, at least log it and continue
                        # This prevents breaking the application if the model discovery fails
                        logger = logging.getLogger(__name__)
                        logger.warning(
                            f"Could not validate foreign key {field_name}: {e}"
                        )

    def _get_datetime_fields(self) -> list[str]:
        """Get list of datetime field names for the model."""
        datetime_fields = []
        for field_name, field_info in self.model_info.fields.items():
            if field_info.type_name in ["datetime", "date"]:
                datetime_fields.append(field_name)
        return datetime_fields

    def get_model_info(self) -> ModelInfo:
        """Get model information."""
        return self.model_info
