from fastapi import APIRouter, Depends

from apex.app.core.auth import require_permission
from apex.app.core.dependencies import get_session
from apex.app.permissions.schemas import PermissionCreate, PermissionOut
from apex.app.permissions.services import PermissionManager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_permission_manager(session: AsyncSession = Depends(get_session)) -> PermissionManager:
    return PermissionManager(session)


@router.get(
    "/",
    response_model=list[PermissionOut],
    dependencies=[Depends(require_permission("permissions:read"))],
)
async def list_permissions(manager: PermissionManager = Depends(get_permission_manager)):
    return await manager.list_permissions()


@router.post(
    "/",
    response_model=PermissionOut,
    status_code=201,
    dependencies=[Depends(require_permission("permissions:create"))],
)
async def create_permission(payload: PermissionCreate, manager: PermissionManager = Depends(get_permission_manager)):
    return await manager.create_permission(payload)

