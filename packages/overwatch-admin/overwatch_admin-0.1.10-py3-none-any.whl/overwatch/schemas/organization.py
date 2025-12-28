"""
Organization schemas for Overwatch admin panel.
"""

from typing import Any

from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    level: int = Field(1, ge=1, le=10)
    is_active: bool = Field(True)


class OrganizationCreate(OrganizationBase):
    """Organization creation schema."""
    parent_id: int | None = Field(None, ge=1)


class OrganizationUpdate(BaseModel):
    """Organization update schema."""
    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    parent_id: int | None = Field(None, ge=1)
    level: int | None = Field(None, ge=1, le=10)
    status: str | None = Field(None, pattern="^(active|inactive|suspended)$")
    is_active: bool | None = None


class OrganizationResponse(OrganizationBase):
    """Organization response schema."""
    id: int
    status: str
    parent_id: int | None
    created_at: str
    updated_at: str

    # Additional fields
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    settings: str | None = None
    allowed_domains: str | None = None
    created_by: int | None = None
    updated_by: int | None = None

    class Config:
        from_attributes = True


class OrganizationStats(BaseModel):
    """Organization statistics schema."""
    total_organizations: int
    active_organizations: int
    inactive_organizations: int
    suspended_organizations: int
    organizations_by_level: dict[int, int]


class OrganizationSearchRequest(BaseModel):
    """Organization search request schema."""
    search: str | None = None
    status: str | None = Field(None, pattern="^(active|inactive|suspended)$")
    is_active: bool | None = None
    level: int | None = Field(None, ge=1, le=10)
    page: int = Field(1, ge=1)
    per_page: int = Field(25, ge=1, le=1000)


class PaginatedOrganizations(BaseModel):
    """Paginated organizations response schema."""
    items: list[OrganizationResponse]
    total: int
    page: int
    per_page: int
    pages: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrganizationAdmin(BaseModel):
    """Organization admin schema."""
    id: int
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: str
    is_active: bool
    created_at: str | None = None
    last_login: str | None = None

    class Config:
        from_attributes = True


class OrganizationAdminsResponse(BaseModel):
    """Organization admins response schema."""
    organization_id: int
    admins: list[OrganizationAdmin]
    total_count: int
    role_filter: str | None = None


class AccessibleOrganization(BaseModel):
    """Accessible organization schema."""
    id: int
    name: str
    slug: str
    description: str | None = None
    level: int
    is_active: bool
    created_at: str | None = None

    class Config:
        from_attributes = True


class AccessibleOrganizationsResponse(BaseModel):
    """Accessible organizations response schema."""
    admin_id: int
    organizations: list[AccessibleOrganization]
    total_count: int


class BulkOrganizationCreate(BaseModel):
    """Bulk organization creation schema."""
    organizations: list[OrganizationCreate]


class BulkOrganizationUpdate(BaseModel):
    """Bulk organization update schema."""
    organization_ids: list[int]
    updates: OrganizationUpdate


class BulkOrganizationDelete(BaseModel):
    """Bulk organization deletion schema."""
    organization_ids: list[int]
