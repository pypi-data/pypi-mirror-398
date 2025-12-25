from fastapi import APIRouter, Depends

from apex.app.core.auth import require_permission
from apex.app.core.dependencies import get_session, get_role_model
from apex.app.roles.schemas import RoleCreate, RoleOut, RoleUpdate
from apex.app.permissions.schemas import PermissionCreate
from apex.app.roles.services import RoleManager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_role_manager(
    session: AsyncSession = Depends(get_session),
    role_model=Depends(get_role_model),
) -> RoleManager:
    return RoleManager(session, role_model)


@router.get(
    "/",
    response_model=list[RoleOut],
    dependencies=[Depends(require_permission("roles:read"))],
)
async def list_roles(manager: RoleManager = Depends(get_role_manager)):
    return await manager.list_roles()


@router.post(
    "/",
    response_model=RoleOut,
    status_code=201,
    dependencies=[Depends(require_permission("roles:create"))],
)
async def create_role(payload: RoleCreate, manager: RoleManager = Depends(get_role_manager)):
    return await manager.create_role(payload)


@router.get(
    "/{role_id}",
    response_model=RoleOut,
    dependencies=[Depends(require_permission("roles:read"))],
)
async def get_role(role_id: str, manager: RoleManager = Depends(get_role_manager)):
    return await manager.get_role(role_id)


@router.put(
    "/{role_id}",
    response_model=RoleOut,
    dependencies=[Depends(require_permission("roles:update"))],
)
async def update_role(role_id: str, payload: RoleUpdate, manager: RoleManager = Depends(get_role_manager)):
    return await manager.update_role(role_id, payload)


@router.post(
    "/{role_id}/permissions",
    status_code=201,
    dependencies=[Depends(require_permission("roles:assign"))],
)
async def add_permission(role_id: str, payload: PermissionCreate, manager: RoleManager = Depends(get_role_manager)):
    await manager.add_permission(role_id, payload)
    return {"message": "Permission added"}

