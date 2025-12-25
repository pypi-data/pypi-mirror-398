"""
Common dependency helpers for FastAPI routers.
"""
from typing import Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apex.app.database.session import AsyncSessionLocal
from apex.app.models import BaseOrganization, BaseRole, BaseUser
from apex.app.models.default import (
    Organization,
    OrganizationLocation,
    OrganizationSettings,
    Payment,
    Permission,
    Role,
    User,
)


def get_user_model() -> Type[BaseUser]:
    return User


def get_role_model() -> Type[BaseRole]:
    return Role


def get_organization_model() -> Type[BaseOrganization]:
    return Organization


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = [
    "get_session",
    "get_user_model",
    "get_role_model",
    "get_organization_model",
    "User",
    "Role",
    "Permission",
    "Organization",
    "OrganizationLocation",
    "OrganizationSettings",
    "Payment",
]

