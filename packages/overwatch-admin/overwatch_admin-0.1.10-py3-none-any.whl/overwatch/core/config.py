"""
Configuration management for Overwatch admin panel.
"""

from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """Configuration for a specific model."""

    list_fields: list[str] | None = None
    search_fields: list[str] | None = None
    exclude_fields: list[str] = Field(default_factory=list)
    readonly_fields: list[str] = Field(default_factory=list)
    hidden_fields: list[str] = Field(default_factory=list)
    permissions: dict[str, str] = Field(
        default_factory=lambda: {"read": "admin", "write": "admin"}
    )
    custom_actions: list[dict[str, Any]] = Field(default_factory=list)
    per_page: int = 25
    order_by: str | None = None
    order_direction: str = "asc"


class SecurityConfig(BaseModel):
    """Security configuration."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str | None = None  # Will use app's database if not provided
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30


class AuditConfig(BaseModel):
    """Audit logging configuration."""

    enabled: bool = True
    log_reads: bool = False
    log_writes: bool = True
    log_logins: bool = True
    retention_days: int = 90
    exclude_models: list[str] = Field(default_factory=list)


class DefaultAdminConfig(BaseModel):
    """Default admin configuration for automatic creation."""

    username: str = "admin"
    email: str = "admin@example.com"
    password: str = "admin123"
    first_name: str = "Admin"
    last_name: str = "User"
    role: str = "admin"


class OverwatchConfig(BaseSettings):
    """
    Main configuration class for Overwatch admin panel.

    This can be initialized from environment variables, .env files,
    or directly from a dictionary.
    """

    # Basic settings
    admin_title: str = "Overwatch Admin"
    logo_url: str | None = "/assets/overwatch.png"
    favicon_url: str | None = "/assets/favicon.ico"

    # Theme settings
    overwatch_theme_primary_color: str = "#3b82f6"
    overwatch_theme_secondary_color: str = "#64748b"
    overwatch_theme_mode: str = "light"

    # Database settings
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Security settings
    security: SecurityConfig | None = None

    # UI settings
    per_page: int = 25
    date_format: str = "YYYY-MM-DD"
    time_format: str = "HH:mm:ss"
    timezone: str = "UTC"
    language: str = "en"

    # Feature flags
    enable_audit_log: bool = True
    enable_dashboard: bool = True
    enable_bulk_operations: bool = True
    enable_export: bool = True
    enable_import: bool = False

    # Model configurations
    models: dict[str, ModelConfig] = Field(default_factory=dict)

    # URL configuration
    admin_path: str = "/admin"
    api_path: str = "/admin/api"
    static_path: str = "/admin/static"

    # CORS settings
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:4200",
            "http://localhost:8080",
        ]
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    # Audit configuration
    audit: AuditConfig = Field(default_factory=AuditConfig)

    # Default admin configuration
    default_admin: DefaultAdminConfig = Field(default_factory=DefaultAdminConfig)

    model_config = {
        "env_prefix": "OVERWATCH_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
    }

    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model."""
        return self.models.get(model_name, ModelConfig())

    def set_model_config(self, model_name: str, config: ModelConfig) -> None:
        """Set configuration for a specific model."""
        self.models[model_name] = config

    def get_jwt_secret(self) -> str:
        """Get JWT secret key."""
        if self.security and self.security.secret_key:
            return self.security.secret_key

        # Fallback to environment variable
        import os

        return os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    def is_production(self) -> bool:
        """Check if running in production mode."""
        import os

        return os.getenv("ENVIRONMENT", "development").lower() == "production"
