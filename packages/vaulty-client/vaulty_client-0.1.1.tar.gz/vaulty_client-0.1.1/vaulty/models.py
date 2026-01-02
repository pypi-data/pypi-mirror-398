"""Pydantic models for SDK."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# Pagination Models
class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


# Customer Models
class CustomerCreate(BaseModel):
    """Customer creation request."""

    email: str
    password: str


class CustomerResponse(BaseModel):
    """Customer response."""

    id: str
    email: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CustomerSettingsUpdate(BaseModel):
    """Customer settings update request."""

    rate_limit_enabled: bool | None = None
    rate_limit_requests_per_minute: int | None = None


class CustomerSettingsResponse(BaseModel):
    """Customer settings response."""

    rate_limit_enabled: bool
    rate_limit_requests_per_minute: int


# Project Models
class ProjectCreate(BaseModel):
    """Project creation request."""

    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    """Project update request."""

    description: str | None = None


class ProjectResponse(BaseModel):
    """Project response."""

    id: str | None = None
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# Secret Models
class SecretCreate(BaseModel):
    """Secret creation request."""

    key: str
    value: str


class SecretUpdate(BaseModel):
    """Secret update request."""

    value: str


class SecretResponse(BaseModel):
    """Secret metadata response (without value)."""

    key: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SecretValueResponse(BaseModel):
    """Secret value response (decrypted)."""

    key: str
    value: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# Token Models
class TokenCreate(BaseModel):
    """Token creation request."""

    scope: str
    description: str | None = None
    password: str | None = None


class TokenResponse(BaseModel):
    """Token response."""

    id: str
    customer_id: str | None = None
    scope: str
    description: str | None = None
    token: str | None = None  # Only present on creation
    created_at: datetime | None = None
    expires_at: datetime | None = None


# Activity Models
class ActivityFilters(BaseModel):
    """Activity filters."""

    action: str | None = None
    method: str | None = None
    resource_id: str | None = None
    search: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class ActivityResponse(BaseModel):
    """Activity response."""

    id: str | None = None
    action: str
    method: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    customer_id: str | None = None
    project_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] | None = None
