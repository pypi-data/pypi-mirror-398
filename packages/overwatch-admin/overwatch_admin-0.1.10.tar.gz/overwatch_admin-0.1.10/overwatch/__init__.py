"""
Overwatch - Agnostic Admin Panel for FastAPI

A reusable, agnostic admin panel package for FastAPI applications that
automatically generates CRUD interfaces for SQLAlchemy models.
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from overwatch.api.admin import router as admin_router
from overwatch.api.audit import router as audit_router
from overwatch.api.auth import router as auth_router
from overwatch.api.config import router as config_router
from overwatch.api.dashboard import router as dashboard_router
from overwatch.api.organizations import router as organizations_router
from overwatch.api.permissions import router as permissions_router
from overwatch.core.config import OverwatchConfig
from overwatch.core.database import get_db_session, initialize_database
from overwatch.models.admin import Admin, OverwatchAdminRole
from overwatch.services.admin_service import AdminService
from overwatch.services.introspection import ModelIntrospector
from overwatch.utils.security import initialize_security

__version__ = "0.1.0"
__author__ = "Yashdiq Lubis"
__email__ = "yashdiq@lubis.dev"


class OverwatchAdmin:
    """
    Main Overwatch admin class that provides Admin functionality for FastAPI applications.
    """

    def __init__(
        self,
        app: FastAPI,
        db_session: type[AsyncSession] | None = None,
        models: list[type] | None = None,
        config: OverwatchConfig | None = None,
        prefix: str = "/admin",
        database_url: str | None = None,
    ) -> None:
        """
        Initialize Overwatch admin panel.

        Args:
            app: FastAPI application instance
            db_session: Database session dependency (deprecated, use database_url instead)
            models: List of SQLAlchemy models to manage
            config: Overwatch configuration
            prefix: URL prefix for admin routes
            database_url: Database connection URL for initialization
        """
        self.app = app
        self.db_session = db_session
        self.models = models
        self.config = config or OverwatchConfig()
        self.prefix = prefix.rstrip("/")
        self.database_url = database_url or (
            config.database.url if config and config.database else None
        )

        # Initialize model introspector (deferred until database is initialized)
        self.introspector: ModelIntrospector | None = None

        # Store model configurations
        self.model_configs: dict[str, dict[str, Any]] = {}

        # Register lifespan event handler for database initialization
        self._register_lifespan_event()

        # Register routes
        self._register_routes()
        # Note: _register_models is async but called from sync __init__
        # This will be handled by FastAPI lifespan event

    def _register_lifespan_event(self) -> None:
        """Register lifespan event handler for database initialization."""

        database_url = self.database_url
        config = self.config
        models = self.models

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Handle application startup and shutdown events."""
            # Startup logic
            if database_url:
                # Initialize the global database manager
                from overwatch.core.database import get_database_manager

                try:
                    # Check if already initialized
                    db_manager = get_database_manager()
                except RuntimeError:
                    # Not initialized, so initialize it
                    db_manager = await initialize_database(database_url, echo=False)

                    # Create tables
                    await db_manager.create_tables()

                # Initialize introspector with a proper session
                async for db_session in get_db_session():
                    self.introspector = ModelIntrospector(db_session)
                    break

                # Initialize security manager
                if config.security:
                    initialize_security(
                        secret_key=config.get_jwt_secret(),
                        algorithm=config.security.algorithm,
                        access_token_expire_minutes=config.security.access_token_expire_minutes,
                        refresh_token_expire_days=config.security.refresh_token_expire_days,
                    )
                else:
                    # Use default security configuration
                    initialize_security(
                        secret_key=config.get_jwt_secret(),
                    )

                # Check and create default admin if configured
                if config.default_admin:
                    await self._create_default_admin(config, db_manager)

                # Initialize default configuration values
                await self._initialize_default_configs(config)

                # Generate frontend config file
                self._generate_frontend_config()

                # Register models (async operation)
                if models:
                    for model in models:
                        await self.register_model(model)

                # Register catch-all SPA route after all CRUD routes are registered
                self._register_spa_route()
            else:
                raise ValueError(
                    "Database URL is required. Pass it to OverwatchAdmin or set it in config."
                )

            # Yield control to the application
            yield

            # Shutdown logic (if needed in future)
            pass

        # Set the lifespan handler on the app
        self.app.router.lifespan_context = lifespan

    def _register_routes(self) -> None:
        """Register admin routes with FastAPI app."""
        # Add CORS middleware with more permissive settings for development
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=self.config.cors_allow_credentials,
            allow_methods=self.config.cors_allow_methods,
            allow_headers=self.config.cors_allow_headers,
            expose_headers=["*"],  # Expose all headers
        )

        # Get the path to frontend static files
        frontend_dist_path = Path(__file__).parent / "static"

        # Mount static files for assets at the admin prefix level
        if frontend_dist_path.exists():
            self.app.mount(
                f"{self.prefix}/assets",
                StaticFiles(directory=str(frontend_dist_path / "assets")),
                name="overwatch_static",
            )

        # Include core admin routes
        self.app.include_router(
            router=auth_router,
            prefix=f"{self.prefix}/api/overwatch-auth",
        )

        self.app.include_router(
            router=admin_router,
            prefix=f"{self.prefix}/api/overwatch-admin",
        )

        self.app.include_router(
            router=config_router,
            prefix=f"{self.prefix}/api/overwatch-config",
        )

        self.app.include_router(
            router=dashboard_router,
            prefix=f"{self.prefix}/api/overwatch-dashboard",
        )

        self.app.include_router(
            router=audit_router,
            prefix=f"{self.prefix}/api/overwatch-audit-logs",
        )

        self.app.include_router(
            router=organizations_router,
            prefix=f"{self.prefix}/api/overwatch-organizations",
        )

        self.app.include_router(
            router=permissions_router,
            prefix=f"{self.prefix}/api/overwatch-permissions",
        )

        # Add the main admin route to serve the frontend
        @self.app.get(f"{self.prefix}", include_in_schema=False)
        @self.app.get(f"{self.prefix}/", include_in_schema=False)
        async def serve_admin_frontend():
            """Serve the Overwatch admin frontend."""
            index_path = frontend_dist_path / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return {
                "error": "Frontend static files not found. Build frontend and copy to overwatch/static/"
            }

        # Note: Catch-all route for SPA routing will be registered in lifespan event
        # after all model CRUD routes are registered to ensure proper precedence

    def _register_spa_route(self) -> None:
        """Register catch-all SPA route after all other routes are registered."""
        # Get the path to frontend static files
        frontend_dist_path = Path(__file__).parent / "static"

        # Catch-all route for SPA routing (must be registered last)
        @self.app.get(f"{self.prefix}/{{path:path}}", include_in_schema=False)
        async def serve_admin_spa(path: str):
            """Serve the Overwatch admin SPA routes."""
            # Don't intercept API routes - let them be handled by their respective routers
            # API routes should have been registered earlier and take precedence
            # Only serve frontend for non-API routes
            if path.startswith("api/") or path.startswith("assets/"):
                return {"error": "Not found"}

            index_path = frontend_dist_path / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return {
                "error": "Frontend static files not found. Build frontend and copy to overwatch/static/"
            }

    async def _register_models(self) -> None:
        """Register models for CRUD operations."""
        if self.models:
            for model in self.models:
                await self.register_model(model)

    def _model_name_to_kebab_case(self, model_name: str) -> str:
        """
        Convert model name to kebab-case for URLs.

        Args:
            model_name: Model class name (e.g., "WalletTransaction")

        Returns:
            kebab-case name for URLs (e.g., "wallet-transaction")
        """
        # Insert hyphen before each uppercase letter (except the first one)
        # and convert to lowercase
        import re

        kebab = re.sub("(?<!^)(?=[A-Z])", "-", model_name).lower()
        return kebab

    async def register_model(self, model: type) -> None:
        """
        Register a model for admin management.

        Args:
            model: SQLAlchemy model class
        """
        # Ensure introspector is initialized
        if self.introspector is None:
            async for db_session in get_db_session():
                self.introspector = ModelIntrospector(db_session)
                break

        # Get model information
        if self.introspector is None:
            raise RuntimeError("Introspector could not be initialized")

        model_info = await self.introspector.inspect_model(model)

        # Store model info
        self.model_configs[model.__name__] = {
            "model": model,
            "model_info": model_info,
            "config": {},
        }

        # Create and register CRUD router
        from overwatch.api.crud import create_crud_router

        router = create_crud_router(
            model_class=model,
            model_info=model_info,
            prefix="",  # No prefix since we'll include it with the full path
        )

        # Convert model name to kebab-case for URL
        model_route_name = self._model_name_to_kebab_case(model.__name__)
        self.app.include_router(router, prefix=f"{self.prefix}/api/{model_route_name}")

    def configure_model(
        self,
        model: type,
        list_fields: list[str] | None = None,
        search_fields: list[str] | None = None,
        exclude_fields: list[str] | None = None,
        readonly_fields: list[str] | None = None,
        per_page: int | None = None,
        order_by: str | None = None,
        permissions: dict[str, str] | None = None,
        custom_actions: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Configure model display and behavior.

        Args:
            model: SQLAlchemy model class
            list_fields: Fields to display in list view
            search_fields: Fields to include in search
            exclude_fields: Fields to exclude from forms
            readonly_fields: Fields that are read-only
            per_page: Items per page for this model
            order_by: Default ordering field
            permissions: Permission overrides
            custom_actions: Custom action buttons
        """
        model_name = model.__name__

        if model_name not in self.model_configs:
            raise ValueError(f"Model {model_name} is not registered")

        # Update configuration
        config = self.model_configs[model_name]["config"]

        if list_fields is not None:
            config["list_fields"] = list_fields
        if search_fields is not None:
            config["search_fields"] = search_fields
        if exclude_fields is not None:
            config["exclude_fields"] = exclude_fields
        if readonly_fields is not None:
            config["readonly_fields"] = readonly_fields
        if per_page is not None:
            config["per_page"] = per_page
        if order_by is not None:
            config["order_by"] = order_by
        if permissions is not None:
            config["permissions"] = permissions
        if custom_actions is not None:
            config["custom_actions"] = custom_actions

    async def _create_default_admin(self, config: OverwatchConfig, db_manager) -> None:
        """
        Create default admin user if no admins exist and log the action.

        Args:
            config: Overwatch configuration
            db_manager: Database manager
        """
        async for db in get_db_session():
            admin_service = AdminService(db)

            # Check if any admin exists
            admin_count = await admin_service.get_admin_count()

            if admin_count == 0:
                # Map role string to OverwatchAdminRole enum
                role_mapping = {
                    "admin": OverwatchAdminRole.ADMIN,
                    "super_admin": OverwatchAdminRole.SUPER_ADMIN,
                    "read_only": OverwatchAdminRole.READ_ONLY,
                }

                default_role = role_mapping.get(
                    config.default_admin.role, OverwatchAdminRole.ADMIN
                )

                # Create default admin
                await admin_service.create_admin(
                    username=config.default_admin.username,
                    password=config.default_admin.password,
                    email=config.default_admin.email,
                    first_name=config.default_admin.first_name,
                    last_name=config.default_admin.last_name,
                    role=default_role,
                    is_active=True,
                )

    async def _initialize_default_configs(self, config: OverwatchConfig) -> None:
        """
        Initialize default configuration values from OverwatchConfig.

        Args:
            config: Overwatch configuration
        """
        from overwatch.services.config_service import ConfigService

        async for db in get_db_session():
            config_service = ConfigService(db)
            await config_service.initialize_default_configs(config)

    def _generate_frontend_config(self) -> None:
        """Generate frontend configuration file for Vite to read."""
        # Use config's admin_path if available, otherwise fallback to prefix
        admin_path = getattr(self.config, 'admin_path', None) or self.prefix or "/admin"

        frontend_config = {
            "admin_path": admin_path,
            "api_path": f"{admin_path}/api"
        }

        # Write config to static folder
        config_path = Path(__file__).parent / "static" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(frontend_config, f, indent=2)

    async def create_admin(
        self,
        username: str,
        password: str,
        email: str,
        role: OverwatchAdminRole = OverwatchAdminRole.ADMIN,
        first_name: str | None = None,
        last_name: str | None = None,
        is_active: bool = True,
    ) -> Admin:
        """
        Create a new admin user.

        Args:
            username: Admin username
            password: Admin password
            email: Admin email
            role: Admin role
            first_name: First name
            last_name: Last name
            is_active: Whether admin is active

        Returns:
            Created admin user
        """
        async for db in get_db_session():
            admin_service = AdminService(db)
            return await admin_service.create_admin(
                username=username,
                password=password,
                email=email,
                role=role,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active,
            )

    def get_model_config(self, model: type) -> dict[str, Any]:
        """
        Get configuration for a model.

        Args:
            model: SQLAlchemy model class

        Returns:
            Model configuration dictionary
        """
        model_name = model.__name__
        return self.model_configs.get(model_name, {}).get("config", {})

    def get_registered_models(self) -> list[type]:
        """
        Get list of registered models.

        Returns:
            List of registered model classes
        """
        return [config["model"] for config in self.model_configs.values()]

    def get_model_info(self, model: type) -> Any:
        """
        Get model information for introspection.

        Args:
            model: SQLAlchemy model class

        Returns:
            Model information object
        """
        model_name = model.__name__
        return self.model_configs.get(model_name, {}).get("model_info")


# Convenience function for quick setup
def create_admin_panel(
    app: FastAPI,
    db_session: type[AsyncSession],
    models: list[type],
    config: OverwatchConfig | None = None,
    prefix: str = "/admin",
    database_url: str | None = None,
) -> OverwatchAdmin:
    """
    Convenience function to create and configure an admin panel.

    Args:
        app: FastAPI application
        db_session: Database session dependency (deprecated, use database_url instead)
        models: List of SQLAlchemy models
        config: Overwatch configuration
        prefix: URL prefix for admin routes
        database_url: Database connection URL for initialization

    Returns:
        Configured OverwatchAdmin instance
    """
    return OverwatchAdmin(
        app=app,
        db_session=db_session,
        models=models,
        config=config,
        prefix=prefix,
        database_url=database_url,
    )


__all__ = [
    "OverwatchAdmin",
    "OverwatchConfig",
    "create_admin_panel",
    "__version__",
]
