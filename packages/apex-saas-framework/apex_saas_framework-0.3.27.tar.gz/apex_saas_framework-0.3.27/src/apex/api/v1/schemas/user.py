"""User schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    username: str | None = None
    full_name: str | None = None
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)
    organization_id: UUID | None = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    username: str | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8)
    is_active: bool | None = None
    is_verified: bool | None = None
    settings: dict[str, Any] | None = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    organization_id: UUID | None = None
    settings: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

