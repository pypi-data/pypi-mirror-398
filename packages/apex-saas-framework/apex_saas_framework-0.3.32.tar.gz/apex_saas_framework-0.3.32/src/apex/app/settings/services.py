from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.app.core.utils import merge_jsonb
from apex.app.models.default import OrganizationSettings, UserSettings
from apex.app.settings.schemas import OrgSettingsOut, OrgSettingsUpdate, UserSettingsOut, UserSettingsUpdate


class SettingsManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_user_settings(self, user_id: str, payload: UserSettingsUpdate) -> UserSettingsOut:
        settings = await self.session.get(UserSettings, user_id)
        if not settings:
            settings = UserSettings(user_id=user_id, preferences={})
            self.session.add(settings)
        settings.preferences = merge_jsonb(settings.preferences or {}, payload.preferences or {})
        await self.session.flush()
        await self.session.refresh(settings)
        return UserSettingsOut(user_id=settings.user_id, preferences=settings.preferences)

    async def update_org_settings(self, org_id: str, payload: OrgSettingsUpdate) -> OrgSettingsOut:
        settings = await self.session.get(OrganizationSettings, org_id)
        if not settings:
            settings = OrganizationSettings(organization_id=org_id, preferences={})
            self.session.add(settings)
        settings.preferences = merge_jsonb(settings.preferences or {}, payload.preferences or {})
        await self.session.flush()
        await self.session.refresh(settings)
        return OrgSettingsOut(organization_id=settings.organization_id, preferences=settings.preferences)

