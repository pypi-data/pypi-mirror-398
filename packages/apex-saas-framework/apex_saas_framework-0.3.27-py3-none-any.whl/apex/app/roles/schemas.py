from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    organization_id: UUID | None = None


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    organization_id: UUID | None = None


class RoleOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    organization_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True

