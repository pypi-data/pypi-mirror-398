from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str
    domain: str | None = None
    organization_type: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    organization_type: str | None = None
    is_active: bool | None = None


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    domain: str | None
    organization_type: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LocationCreate(BaseModel):
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None

