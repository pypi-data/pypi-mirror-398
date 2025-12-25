from fastapi import APIRouter, Depends

from apex.app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from apex.app.auth.services import AuthManager
from apex.app.core.auth import get_current_user
from apex.app.core.dependencies import get_session, get_user_model
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_auth_manager(
    session: AsyncSession = Depends(get_session),
    user_model=Depends(get_user_model),
) -> AuthManager:
    return AuthManager(session=session, user_model=user_model)


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(payload: SignupRequest, manager: AuthManager = Depends(get_auth_manager)):
    return await manager.signup(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, manager: AuthManager = Depends(get_auth_manager)):
    return await manager.login(payload)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, manager: AuthManager = Depends(get_auth_manager)):
    return await manager.refresh(payload)


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, manager: AuthManager = Depends(get_auth_manager)):
    await manager.forgot_password(payload)
    return {"message": "Reset instructions sent"}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, manager: AuthManager = Depends(get_auth_manager)):
    await manager.reset_password(payload)
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    manager: AuthManager = Depends(get_auth_manager),
):
    await manager.change_password(current_user.id, payload)
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

