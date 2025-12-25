from __future__ import annotations

from typing import Optional, Type
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
from apex.app.core.dependencies import get_user_model
from apex.core.config import get_settings
from apex.domain.services.auth import AuthService
from apex.domain.services.password_reset import PasswordResetService
from apex.domain.services.user import UserService


class AuthManager:
    """High-level auth orchestrator used by routers."""

    def __init__(self, session: AsyncSession, user_model: Optional[Type] = None) -> None:
        self.session = session
        self.user_model = user_model or get_user_model()
        self.user_service = UserService(session, self.user_model)
        self.auth_service = AuthService(session, self.user_model)
        self.reset_service = PasswordResetService(session, self.user_model)
        self.settings = get_settings()

    async def signup(self, payload: SignupRequest) -> UserResponse:
        existing = await self.user_service.get_user_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists.")

        user = await self.user_service.create_user(
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            country=payload.country,
            organization_id=payload.organization_id,
            is_active=True,
        )
        await self.session.refresh(user)
        return UserResponse.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.auth_service.authenticate_user(payload.email, payload.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

        tokens = await self.auth_service.create_tokens(user)
        return TokenResponse(**tokens)

    async def refresh(self, payload: RefreshRequest) -> TokenResponse:
        data = await self.auth_service.refresh_access_token(payload.refresh_token)
        if not data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
        return TokenResponse(**data)

    async def forgot_password(self, payload: ForgotPasswordRequest) -> None:
        user, token = await self.reset_service.request_password_reset(payload.email)
        # Placeholder for email integration
        if self.settings.DEBUG and token:
            print(f"[Password Reset] token for {payload.email}: {token}")  # noqa: T201
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    async def reset_password(self, payload: ResetPasswordRequest) -> None:
        success = await self.reset_service.reset_password(payload.token, payload.new_password)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token.")

    async def change_password(self, user_id: UUID, payload: ChangePasswordRequest) -> None:
        user = await self.user_service.get_user_by_id(str(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        changed = await self.user_service.change_password(user, payload.current_password, payload.new_password)
        if not changed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect.")

