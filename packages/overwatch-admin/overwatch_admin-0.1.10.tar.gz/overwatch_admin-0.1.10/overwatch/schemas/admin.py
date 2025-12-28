"""
Pydantic schemas for admin operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.types import SecretStr

from overwatch.models.admin import OverwatchAdminRole, OverwatchAdminStatus


class AdminLogin(BaseModel):
    """Admin login request schema."""

    username: str = Field(..., min_length=1, max_length=50)
    password: SecretStr = Field(..., min_length=8)


class AdminCreate(BaseModel):
    """Admin creation request schema."""

    username: str = Field(..., min_length=1, max_length=50)
    email: EmailStr | None = Field(None, max_length=255)
    password: SecretStr = Field(..., min_length=8)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    role: OverwatchAdminRole = Field(OverwatchAdminRole.ADMIN)
    is_active: bool = Field(True)
    organization_id: int | None = Field(None)


class AdminUpdate(BaseModel):
    """Admin update request schema."""

    username: str | None = Field(None, min_length=1, max_length=50)
    email: EmailStr | None = Field(None, max_length=255)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    role: OverwatchAdminRole | None = None
    status: OverwatchAdminStatus | None = None
    is_active: bool | None = None
    organization_id: int | None = Field(None)


class AdminOrganizationResponse(BaseModel):
    """Organization response schema for admin."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    level: int
    status: str
    is_active: bool


class AdminResponse(BaseModel):
    """Admin response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    first_name: str | None
    last_name: str | None
    role: OverwatchAdminRole
    status: OverwatchAdminStatus
    is_active: bool
    is_verified: bool
    last_login: str | None
    created_at: str
    updated_at: str
    organization: AdminOrganizationResponse | None = None

    @field_validator("last_login", mode="before")
    @classmethod
    def serialize_last_login(cls, v: Any) -> str | None:
        """Serialize last_login datetime to string."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_created_at(cls, v: Any) -> str:
        """Serialize created_at datetime to string."""
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    @field_validator("updated_at", mode="before")
    @classmethod
    def serialize_updated_at(cls, v: Any) -> str:
        """Serialize updated_at datetime to string."""
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    @property
    def full_name(self) -> str:
        """Get admin's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


class AdminLoginResponse(BaseModel):
    """Admin login response schema."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    admin: AdminResponse


class TokenRefresh(BaseModel):
    """Token refresh request schema."""

    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminPasswordChange(BaseModel):
    """Admin password change request schema."""

    current_password: SecretStr = Field(..., min_length=1)
    new_password: SecretStr = Field(..., min_length=8)


class AdminListResponse(BaseModel):
    """Admin list response schema."""

    items: list[AdminResponse]
    total: int
    page: int
    per_page: int
    pages: int


class AdminStatsResponse(BaseModel):
    """Admin statistics response schema."""

    total_admins: int
    active_admins: int
    inactive_admins: int
    suspended_admins: int
    super_admins: int
    admins: int
    read_only_admins: int


class AdminPermissionCheck(BaseModel):
    """Admin permission check request schema."""

    permission: str = Field(..., min_length=1)
    resource_id: int | None = None


class AdminPermissionResponse(BaseModel):
    """Admin permission check response schema."""

    has_permission: bool
    permission: str
    reason: str | None


class AdminSearchRequest(BaseModel):
    """Admin search request schema."""

    search: str | None = Field(None, min_length=1)
    role: OverwatchAdminRole | None = None
    is_active: bool | None = None
    page: int = Field(1, ge=1)
    per_page: int = Field(25, ge=1, le=100)


class AdminBulkCreate(BaseModel):
    """Admin bulk creation request schema."""

    admins: list[AdminCreate] = Field(..., min_length=1, max_length=50)


class AdminBulkUpdate(BaseModel):
    """Admin bulk update request schema."""

    admin_ids: list[int] = Field(..., min_length=1, max_length=50)
    updates: AdminUpdate = Field(...)


class AdminBulkDelete(BaseModel):
    """Admin bulk delete request schema."""

    admin_ids: list[int] = Field(..., min_length=1, max_length=50)
