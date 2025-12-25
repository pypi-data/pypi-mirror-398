"""
Service for managing Overwatch configuration.
"""

import json
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.models.audit_log import OverwatchAuditAction
from overwatch.models.config import Config
from overwatch.schemas.config import ConfigCreate, ConfigUpdate


class ConfigService:
    """Service for managing configuration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config_by_key(self, key: str) -> Config | None:
        """Get configuration by key."""
        stmt = select(Config).where(Config.key == key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_public_configs(self) -> dict[str, Any]:
        """Get all public configurations for frontend consumption."""
        stmt = select(Config).where(Config.is_public)
        result = await self.db.execute(stmt)
        configs = result.scalars().all()

        # Convert to dictionary with proper type conversion
        config_dict = {}
        for config in configs:
            if config.key in ["admin_title", "logo_url", "favicon_url", "overwatch_theme_primary_color", "overwatch_theme_secondary_color", "overwatch_theme_mode"]:
                value = self._convert_value(str(config.value), str(config.data_type))
                config_dict[config.key] = value

        return config_dict

    async def get_config_list(
        self,
        page: int = 1,
        per_page: int = 25,
        search: str | None = None,
        category: str | None = None,
        is_public: bool | None = None,
        sort_by: str = "key",
        sort_direction: str = "asc",
    ) -> tuple[list[Config], int]:
        """Get list of configurations with pagination and filtering."""

        # Build base query
        stmt = select(Config)

        # Apply filters
        filters = []
        if search:
            filters.append(
                or_(
                    Config.key.ilike(f"%{search}%"),
                    Config.description.ilike(f"%{search}%"),
                )
            )
        if category:
            filters.append(Config.category == category)
        if is_public is not None:
            filters.append(Config.is_public == is_public)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Apply sorting
        sort_column = getattr(Config, sort_by, Config.key)
        if sort_direction.lower() == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        result = await self.db.execute(stmt)
        configs = result.scalars().all()

        return list(configs), total

    async def create_config(
        self,
        key: str,
        value: str | None,
        description: str | None = None,
        is_public: bool = True,
        category: str | None = None,
        data_type: str = "string",
    ) -> Config:
        """Create a new configuration."""

        # Check if key already exists
        existing = await self.get_config_by_key(key)
        if existing:
            raise ValueError(f"Configuration key '{key}' already exists")

        config = Config(
            key=key,
            value=value,
            description=description,
            is_public=is_public,
            category=category,
            data_type=data_type,
        )

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)

        return config

    async def update_config(
        self,
        key: str,
        updates: ConfigUpdate,
        updated_by: int | None = None,
    ) -> Config:
        """Update an existing configuration."""

        config = await self.get_config_by_key(key)
        if not config:
            raise ValueError(f"Configuration key '{key}' not found")

        # Update fields
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(config)

        return config

    async def delete_config(self, key: str) -> bool:
        """Delete a configuration."""

        config = await self.get_config_by_key(key)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.commit()

        return True

    async def bulk_create_configs(
        self,
        configs: list[ConfigCreate],
    ) -> list[Config]:
        """Create multiple configurations."""

        created_configs = []
        for config_data in configs:
            try:
                config = await self.create_config(
                    key=config_data.key,
                    value=config_data.value,
                    description=config_data.description,
                    is_public=config_data.is_public,
                    category=config_data.category,
                    data_type=config_data.data_type,
                )
                created_configs.append(config)
            except ValueError:
                # Skip duplicate keys for bulk operations
                continue

        return created_configs

    async def bulk_update_configs(
        self,
        keys: list[str],
        updates: ConfigUpdate,
        updated_by: int | None = None,
    ) -> list[Config]:
        """Update multiple configurations."""

        updated_configs = []
        for key in keys:
            try:
                config = await self.update_config(key, updates, updated_by)
                updated_configs.append(config)
            except ValueError:
                # Skip non-existent keys for bulk operations
                continue

        return updated_configs

    async def bulk_delete_configs(self, keys: list[str]) -> int:
        """Delete multiple configurations."""

        deleted_count = 0
        for key in keys:
            if await self.delete_config(key):
                deleted_count += 1

        return deleted_count

    async def initialize_default_configs(self, overwatch_config) -> None:
        """Initialize default configuration values from OverwatchConfig."""

        # Initialize admin_title
        existing = await self.get_config_by_key("admin_title")
        if not existing:
            await self.create_config(
                key="admin_title",
                value=overwatch_config.admin_title,
                description="Admin panel title displayed in UI",
                is_public=True,
                category="ui",
                data_type="string",
            )

        # Initialize logo_url
        existing = await self.get_config_by_key("logo_url")
        if not existing:
            logo_url = overwatch_config.logo_url or "/assets/overwatch.png"
            await self.create_config(
                key="logo_url",
                value=logo_url,
                description="URL for admin panel logo",
                is_public=True,
                category="ui",
                data_type="string",
            )

        # Initialize favicon_url
        existing = await self.get_config_by_key("favicon_url")
        if not existing:
            favicon_url = overwatch_config.favicon_url or "/assets/favicon.ico"
            await self.create_config(
                key="favicon_url",
                value=favicon_url,
                description="URL for admin panel favicon",
                is_public=True,
                category="ui",
                data_type="string",
            )

        # Initialize theme settings
        existing = await self.get_config_by_key("overwatch_theme_primary_color")
        if not existing:
            await self.create_config(
                key="overwatch_theme_primary_color",
                value=overwatch_config.overwatch_theme_primary_color,
                description="Primary theme color for admin panel",
                is_public=True,
                category="ui",
                data_type="string",
            )

        existing = await self.get_config_by_key("overwatch_theme_secondary_color")
        if not existing:
            await self.create_config(
                key="overwatch_theme_secondary_color",
                value=overwatch_config.overwatch_theme_secondary_color,
                description="Secondary theme color for admin panel",
                is_public=True,
                category="ui",
                data_type="string",
            )

        existing = await self.get_config_by_key("overwatch_theme_mode")
        if not existing:
            await self.create_config(
                key="overwatch_theme_mode",
                value=overwatch_config.overwatch_theme_mode,
                description="Theme mode for admin panel (light/dark)",
                is_public=True,
                category="ui",
                data_type="string",
            )

    def _convert_value(self, value: str | None, data_type: str) -> Any:
        """Convert string value to appropriate type."""
        if value is None:
            return None

        try:
            if data_type == "integer":
                return int(value)
            elif data_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif data_type == "json":
                return json.loads(value)
            else:  # string
                return value
        except (ValueError, json.JSONDecodeError):
            return value

    async def log_config_action(
        self,
        admin_id: int | None,
        action: OverwatchAuditAction,
        resource_type: str,
        resource_id: int | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Log configuration-related actions."""

        # Import here to avoid circular imports
        from overwatch.models.audit_log import AuditLog

        audit_log = AuditLog(
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        await self.db.commit()

    def _get_client_ip(self, request) -> str | None:
        """Get client IP address from request."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to client IP
        return getattr(request.client, "host", None) if request.client else None
