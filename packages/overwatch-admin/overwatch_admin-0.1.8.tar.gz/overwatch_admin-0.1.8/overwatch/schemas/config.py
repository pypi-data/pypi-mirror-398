"""
Pydantic schemas for Overwatch config management.
"""

from typing import Any

from pydantic import BaseModel, Field


class ConfigBase(BaseModel):
    """Base configuration schema."""

    key: str = Field(..., description="Configuration key")
    value: str | None = Field(None, description="Configuration value")
    description: str | None = Field(None, description="Configuration description")
    is_public: bool = Field(True, description="Whether this config is public")
    category: str | None = Field(None, description="Configuration category")
    data_type: str = Field("string", description="Data type of the value")


class ConfigCreate(ConfigBase):
    """Schema for creating configuration."""

    pass


class ConfigUpdate(BaseModel):
    """Schema for updating configuration."""

    value: str | None = Field(None, description="Configuration value")
    description: str | None = Field(None, description="Configuration description")
    is_public: bool | None = Field(None, description="Whether this config is public")
    category: str | None = Field(None, description="Configuration category")
    data_type: str | None = Field(None, description="Data type of the value")


class ConfigResponse(ConfigBase):
    """Schema for configuration response."""

    id: int
    created_at: str
    updated_at: str
    updated_by: int | None = None

    class Config:
        from_attributes = True


class ConfigListResponse(BaseModel):
    """Schema for configuration list response."""

    items: list[ConfigResponse]
    total: int
    page: int
    per_page: int
    pages: int
    metadata: dict[str, Any]


class PublicConfigResponse(BaseModel):
    """Schema for public configuration response (for frontend)."""

    admin_title: str = "Overwatch Admin"
    logo_url: str | None = None
    favicon_url: str | None = None
    overwatch_theme_primary_color: str | None = None
    overwatch_theme_secondary_color: str | None = None
    overwatch_theme_mode: str | None = None

    class Config:
        from_attributes = False


class ConfigBulkCreate(BaseModel):
    """Schema for bulk creating configurations."""

    configs: list[ConfigCreate]


class ConfigBulkUpdate(BaseModel):
    """Schema for bulk updating configurations."""

    keys: list[str]
    updates: ConfigUpdate


class ConfigBulkDelete(BaseModel):
    """Schema for bulk deleting configurations."""

    keys: list[str]
