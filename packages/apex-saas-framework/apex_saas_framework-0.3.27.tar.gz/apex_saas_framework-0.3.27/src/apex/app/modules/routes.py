from fastapi import APIRouter, Depends

from apex.app.core.auth import require_permission
from apex.app.core.dependencies import get_session
from apex.app.modules.services import ModuleManager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_module_manager(session: AsyncSession = Depends(get_session)) -> ModuleManager:
    return ModuleManager(session)


@router.post(
    "/{org_id}/enable/{module_name}",
    dependencies=[Depends(require_permission("modules:update"))],
)
async def enable_module(org_id: str, module_name: str, manager: ModuleManager = Depends(get_module_manager)):
    modules = await manager.set_module(org_id, module_name, True)
    return {"modules": modules}


@router.post(
    "/{org_id}/disable/{module_name}",
    dependencies=[Depends(require_permission("modules:update"))],
)
async def disable_module(org_id: str, module_name: str, manager: ModuleManager = Depends(get_module_manager)):
    modules = await manager.set_module(org_id, module_name, False)
    return {"modules": modules}

