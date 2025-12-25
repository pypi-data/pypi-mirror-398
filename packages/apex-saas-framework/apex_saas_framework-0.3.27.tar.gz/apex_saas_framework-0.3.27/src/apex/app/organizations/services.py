from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.app.core.dependencies import get_organization_model
from apex.app.organizations.schemas import (
    LocationCreate,
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
)
from apex.app.models.default import OrganizationLocation


class OrganizationManager:
    def __init__(self, session: AsyncSession, organization_model=None):
        self.session = session
        self.organization_model = organization_model or get_organization_model()

    async def list_organizations(self) -> list[OrganizationOut]:
        result = await self.session.execute(select(self.organization_model))
        orgs = result.scalars().all()
        return [OrganizationOut.model_validate(o) for o in orgs]

    async def create_organization(self, payload: OrganizationCreate) -> OrganizationOut:
        org = self.organization_model(**payload.model_dump())
        self.session.add(org)
        await self.session.flush()
        await self.session.refresh(org)
        return OrganizationOut.model_validate(org)

    async def get_organization(self, org_id: str) -> OrganizationOut:
        org = await self.session.get(self.organization_model, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        return OrganizationOut.model_validate(org)

    async def update_organization(self, org_id: str, payload: OrganizationUpdate) -> OrganizationOut:
        org = await self.session.get(self.organization_model, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(org, key, value)
        await self.session.flush()
        await self.session.refresh(org)
        return OrganizationOut.model_validate(org)

    async def add_location(self, org_id: str, payload: LocationCreate) -> None:
        org = await self.session.get(self.organization_model, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        location = OrganizationLocation(organization_id=org.id, **payload.model_dump())
        self.session.add(location)
        await self.session.flush()

