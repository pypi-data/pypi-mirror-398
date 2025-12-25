from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    country: str | None = None
    organization_id: UUID | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    country: str | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str | None
    last_name: str | None
    phone: str | None
    country: str | None
    organization_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True

