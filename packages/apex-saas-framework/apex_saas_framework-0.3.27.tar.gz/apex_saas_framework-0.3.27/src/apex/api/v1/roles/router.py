"""Roles router - CRUD operations for roles."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apex.core.authentication.dependencies import get_current_active_user
from apex.core.permissions.dependencies import require_permission
from apex.infrastructure.database.session import get_db

router = APIRouter(tags=["Roles"])


class RoleCreate(BaseModel):
    """Schema for creating a role."""

    name: str
    slug: str | None = None
    description: str | None = None
    organization_id: str | None = None


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: str | None = None
    slug: str | None = None
    description: str | None = None


class RoleResponse(BaseModel):
    """Schema for role response."""

    id: str
    name: str
    slug: str | None
    description: str | None
    organization_id: str | None
    created_at: str
    updated_at: str


class AssignPermissionsRequest(BaseModel):
    """Schema for assigning permissions to a role."""

    permission_ids: list[str]


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("roles", "create")),
):
    """Create a new role."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Role creation needs to be implemented with your Role model",
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_active_user),
):
    """Get role by ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get role needs to be implemented with your Role model",
    )


@router.get("/", response_model=list[RoleResponse])
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    organization_id: str | None = None,
):
    """List all roles, optionally filtered by organization."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List roles needs to be implemented with your Role model",
    )


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("roles", "update")),
):
    """Update role."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update role needs to be implemented with your Role model",
    )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("roles", "delete")),
):
    """Delete role."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete role needs to be implemented with your Role model",
    )


@router.post("/{role_id}/permissions", status_code=status.HTTP_200_OK)
async def assign_permissions(
    role_id: str,
    request: AssignPermissionsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("roles", "update")),
):
    """Assign permissions to a role."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Assign permissions needs to be implemented with your Role/Permission models",
    )

