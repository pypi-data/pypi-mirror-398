from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.app.permissions.schemas import PermissionCreate, PermissionOut
from apex.app.models.default import Permission


class PermissionManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_permissions(self) -> list[PermissionOut]:
        result = await self.session.execute(select(Permission))
        return [PermissionOut.model_validate(p) for p in result.scalars().all()]

    async def create_permission(self, payload: PermissionCreate) -> PermissionOut:
        existing = await self.session.execute(select(Permission).where(Permission.code == payload.code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exists")
        permission = Permission(**payload.model_dump())
        self.session.add(permission)
        await self.session.flush()
        await self.session.refresh(permission)
        return PermissionOut.model_validate(permission)

