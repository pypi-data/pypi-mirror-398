"""Permissions router - CRUD operations for permissions."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apex.core.authentication.dependencies import get_current_active_user
from apex.core.permissions.dependencies import require_superuser
from apex.infrastructure.database.session import get_db

router = APIRouter(tags=["Permissions"])


class PermissionCreate(BaseModel):
    """Schema for creating a permission."""

    name: str
    slug: str | None = None
    resource: str | None = None
    action: str | None = None
    description: str | None = None


class PermissionUpdate(BaseModel):
    """Schema for updating a permission."""

    name: str | None = None
    slug: str | None = None
    resource: str | None = None
    action: str | None = None
    description: str | None = None


class PermissionResponse(BaseModel):
    """Schema for permission response."""

    id: str
    name: str
    slug: str | None
    resource: str | None
    action: str | None
    description: str | None
    created_at: str
    updated_at: str


@router.post("/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_superuser),
):
    """Create a new permission (superuser only)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Permission creation needs to be implemented with your Permission model",
    )


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_active_user),
):
    """Get permission by ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get permission needs to be implemented with your Permission model",
    )


@router.get("/", response_model=list[PermissionResponse])
async def list_permissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    resource: str | None = None,
):
    """List all permissions, optionally filtered by resource."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List permissions needs to be implemented with your Permission model",
    )


@router.patch("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    permission_data: PermissionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_superuser),
):
    """Update permission (superuser only)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update permission needs to be implemented with your Permission model",
    )


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_superuser),
):
    """Delete permission (superuser only)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete permission needs to be implemented with your Permission model",
    )

