from uuid import UUID

from pydantic import BaseModel


class UserSettingsUpdate(BaseModel):
    preferences: dict | None = None


class OrgSettingsUpdate(BaseModel):
    preferences: dict | None = None


class UserSettingsOut(BaseModel):
    user_id: UUID
    preferences: dict | None = None


class OrgSettingsOut(BaseModel):
    organization_id: UUID
    preferences: dict | None = None

