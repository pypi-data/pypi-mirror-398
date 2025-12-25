from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.app.core.dependencies import get_organization_model, get_role_model
from apex.app.roles.schemas import RoleCreate, RoleOut, RoleUpdate
from apex.app.permissions.schemas import PermissionCreate
from apex.app.models.default import Permission


class RoleManager:
    def __init__(self, session: AsyncSession, role_model=None):
        self.session = session
        self.role_model = role_model or get_role_model()

    async def list_roles(self) -> list[RoleOut]:
        result = await self.session.execute(select(self.role_model))
        return [RoleOut.model_validate(r) for r in result.scalars().all()]

    async def create_role(self, payload: RoleCreate) -> RoleOut:
        role = self.role_model(**payload.model_dump())
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return RoleOut.model_validate(role)

    async def get_role(self, role_id: str) -> RoleOut:
        role = await self.session.get(self.role_model, role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return RoleOut.model_validate(role)

    async def update_role(self, role_id: str, payload: RoleUpdate) -> RoleOut:
        role = await self.session.get(self.role_model, role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(role, key, value)
        await self.session.flush()
        await self.session.refresh(role)
        return RoleOut.model_validate(role)

    async def add_permission(self, role_id: str, payload: PermissionCreate) -> None:
        role = await self.session.get(self.role_model, role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        permission = Permission(**payload.model_dump())
        role.permissions.append(permission)
        await self.session.flush()

