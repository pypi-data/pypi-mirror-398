from fastapi import APIRouter, Depends

from apex.app.core.auth import require_permission
from apex.app.core.dependencies import get_session, get_organization_model
from apex.app.organizations.schemas import (
    LocationCreate,
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
)
from apex.app.organizations.services import OrganizationManager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_org_manager(
    session: AsyncSession = Depends(get_session),
    org_model=Depends(get_organization_model),
) -> OrganizationManager:
    return OrganizationManager(session, org_model)


@router.get(
    "/",
    response_model=list[OrganizationOut],
    dependencies=[Depends(require_permission("organizations:read"))],
)
async def list_organizations(manager: OrganizationManager = Depends(get_org_manager)):
    return await manager.list_organizations()


@router.post(
    "/",
    response_model=OrganizationOut,
    status_code=201,
    dependencies=[Depends(require_permission("organizations:create"))],
)
async def create_organization(payload: OrganizationCreate, manager: OrganizationManager = Depends(get_org_manager)):
    return await manager.create_organization(payload)


@router.get(
    "/{org_id}",
    response_model=OrganizationOut,
    dependencies=[Depends(require_permission("organizations:read"))],
)
async def get_organization(org_id: str, manager: OrganizationManager = Depends(get_org_manager)):
    return await manager.get_organization(org_id)


@router.put(
    "/{org_id}",
    response_model=OrganizationOut,
    dependencies=[Depends(require_permission("organizations:update"))],
)
async def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    manager: OrganizationManager = Depends(get_org_manager),
):
    return await manager.update_organization(org_id, payload)


@router.post(
    "/{org_id}/locations",
    status_code=201,
    dependencies=[Depends(require_permission("organizations:update"))],
)
async def add_location(
    org_id: str,
    payload: LocationCreate,
    manager: OrganizationManager = Depends(get_org_manager),
):
    await manager.add_location(org_id, payload)
    return {"message": "Location added"}

