from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.app.models.default import Organization


class ModuleManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_module(self, org_id: str, module: str, enabled: bool) -> dict:
        org = await self.session.get(Organization, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        modules = org.modules or {}
        modules[module] = enabled
        org.modules = modules
        await self.session.flush()
        return modules

