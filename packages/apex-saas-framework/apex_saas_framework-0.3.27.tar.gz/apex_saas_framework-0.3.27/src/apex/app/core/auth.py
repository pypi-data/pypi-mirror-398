"""
Authentication / authorization dependencies.
"""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from apex.core.security.jwt import decode_token
from apex.app.core.dependencies import get_session, get_user_model


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
    user_model=Depends(get_user_model),
):
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await session.execute(
        select(user_model)
        .options(
            selectinload("roles").selectinload("permissions"),
            selectinload("organization"),
        )
        .where(user_model.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


def require_permission(code: str) -> Callable:
    async def dependency(user=Depends(get_current_user)):
        if getattr(user, "is_superuser", False):
            return user
        for role in getattr(user, "roles", []):
            for perm in getattr(role, "permissions", []):
                if perm.code == code:
                    return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    return dependency


async def require_active_user(user=Depends(get_current_user)):
    return user


__all__ = ["get_current_user", "require_permission", "require_active_user", "oauth2_scheme"]

