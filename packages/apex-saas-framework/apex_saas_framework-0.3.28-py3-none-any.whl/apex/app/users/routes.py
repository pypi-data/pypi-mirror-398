from fastapi import APIRouter, Depends, Response

from apex.app.core.auth import get_current_user, require_permission
from apex.app.core.dependencies import get_session, get_user_model
from apex.app.users.schemas import UserCreate, UserOut, UserUpdate
from apex.app.users.services import UserManager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_user_manager(
    session: AsyncSession = Depends(get_session),
    user_model=Depends(get_user_model),
) -> UserManager:
    return UserManager(session, user_model)


@router.get(
    "/",
    response_model=list[UserOut],
    dependencies=[Depends(require_permission("users:read"))],
)
async def list_users(manager: UserManager = Depends(get_user_manager)):
    return await manager.list_users()


@router.post(
    "/",
    response_model=UserOut,
    status_code=201,
    dependencies=[Depends(require_permission("users:create"))],
)
async def create_user(payload: UserCreate, manager: UserManager = Depends(get_user_manager)):
    return await manager.create_user(payload)


@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.get(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_permission("users:read"))],
)
async def get_user(user_id: str, manager: UserManager = Depends(get_user_manager)):
    return await manager.get_user(user_id)


@router.put(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_permission("users:update"))],
)
async def update_user(user_id: str, payload: UserUpdate, manager: UserManager = Depends(get_user_manager)):
    return await manager.update_user(user_id, payload)


@router.delete(
    "/{user_id}",
    status_code=204,
    dependencies=[Depends(require_permission("users:delete"))],
)
async def delete_user(user_id: str, manager: UserManager = Depends(get_user_manager)):
    await manager.delete_user(user_id)
    return Response(status_code=204)

