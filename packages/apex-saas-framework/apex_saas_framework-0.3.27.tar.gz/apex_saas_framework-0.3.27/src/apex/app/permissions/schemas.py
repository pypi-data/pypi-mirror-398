from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PermissionCreate(BaseModel):
    code: str
    description: str | None = None


class PermissionOut(BaseModel):
    id: UUID
    code: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True

