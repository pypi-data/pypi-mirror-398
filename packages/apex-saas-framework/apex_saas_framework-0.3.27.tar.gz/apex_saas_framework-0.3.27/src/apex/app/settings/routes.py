from fastapi import APIRouter, Depends

from apex.app.core.auth import require_permission
from apex.app.core.dependencies import get_session
from apex.app.settings.schemas import OrgSettingsOut, OrgSettingsUpdate, UserSettingsOut, UserSettingsUpdate
from apex.app.settings.services import SettingsManager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_settings_manager(session: AsyncSession = Depends(get_session)) -> SettingsManager:
    return SettingsManager(session)


@router.patch(
    "/user/{user_id}",
    response_model=UserSettingsOut,
    dependencies=[Depends(require_permission("settings:update"))],
)
async def update_user_settings(
    user_id: str,
    payload: UserSettingsUpdate,
    manager: SettingsManager = Depends(get_settings_manager),
):
    return await manager.update_user_settings(user_id, payload)


@router.patch(
    "/organization/{org_id}",
    response_model=OrgSettingsOut,
    dependencies=[Depends(require_permission("settings:update"))],
)
async def update_org_settings(
    org_id: str,
    payload: OrgSettingsUpdate,
    manager: SettingsManager = Depends(get_settings_manager),
):
    return await manager.update_org_settings(org_id, payload)

