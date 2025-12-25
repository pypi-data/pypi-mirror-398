"""Organizations router - CRUD operations for organizations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.app.core.dependencies import get_organization_model
from apex.core.authentication.dependencies import get_current_active_user
from apex.core.permissions.dependencies import require_permission
from apex.infrastructure.database.session import get_db

router = APIRouter(tags=["Organizations"])


class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""

    name: str
    slug: str | None = None
    description: str | None = None
    settings: dict | None = None
    modules: dict | None = None


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: str | None = None
    slug: str | None = None
    description: str | None = None
    settings: dict | None = None
    modules: dict | None = None


class OrganizationResponse(BaseModel):
    """Schema for organization response."""

    id: str
    name: str
    slug: str | None
    description: str | None
    settings: dict | None
    modules: dict | None
    created_at: str
    updated_at: str


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("organizations", "create")),
    organization_model: type = Depends(get_organization_model),
):
    """Create a new organization."""
    try:
        # Get available columns from the model
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(organization_model)
        available_columns = {col.name for col in mapper.columns} if mapper else set()
        
        # Check if slug is unique (if provided and model supports it)
        if org_data.slug and "slug" in available_columns:
            stmt = select(organization_model).where(organization_model.slug == org_data.slug)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization with this slug already exists",
                )
        
        # Build organization data - only include attributes that exist as columns
        org_kwargs = {"name": org_data.name}
        
        # Add optional attributes if they exist as columns on the model
        if "slug" in available_columns and org_data.slug:
            org_kwargs["slug"] = org_data.slug
        if "description" in available_columns and org_data.description:
            org_kwargs["description"] = org_data.description
        if "modules" in available_columns:
            org_kwargs["modules"] = org_data.modules or {}
        # Note: settings is a relationship, not a column, so we don't set it here
        
        # Create organization
        org = organization_model(**org_kwargs)
        db.add(org)
        await db.flush()
        await db.refresh(org)
        
        return OrganizationResponse(
            id=str(org.id),
            name=org.name,
            slug=getattr(org, "slug", None),
            description=getattr(org, "description", None),
            settings=getattr(org, "settings", {}),
            modules=getattr(org, "modules", {}),
            created_at=org.created_at.isoformat() if hasattr(org, "created_at") and org.created_at else "",
            updated_at=org.updated_at.isoformat() if hasattr(org, "updated_at") and org.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}",
        ) from e


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_active_user),
    organization_model: type = Depends(get_organization_model),
):
    """Get organization by ID."""
    try:
        org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format",
        )
    
    org = await db.get(organization_model, org_uuid)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=getattr(org, "slug", None),
        description=getattr(org, "description", None),
        settings=getattr(org, "settings", {}),
        modules=getattr(org, "modules", {}),
        created_at=org.created_at.isoformat() if hasattr(org, "created_at") and org.created_at else "",
        updated_at=org.updated_at.isoformat() if hasattr(org, "updated_at") and org.updated_at else "",
    )


@router.get("/", response_model=list[OrganizationResponse])
async def list_organizations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    organization_model: type = Depends(get_organization_model),
):
    """List all organizations."""
    try:
        stmt = select(organization_model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        orgs = result.scalars().all()
        
        return [
            OrganizationResponse(
                id=str(org.id),
                name=org.name,
                slug=getattr(org, "slug", None),
                description=getattr(org, "description", None),
                settings=getattr(org, "settings", {}),
                modules=getattr(org, "modules", {}),
                created_at=org.created_at.isoformat() if hasattr(org, "created_at") and org.created_at else "",
                updated_at=org.updated_at.isoformat() if hasattr(org, "updated_at") and org.updated_at else "",
            )
            for org in orgs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list organizations: {str(e)}",
        ) from e


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("organizations", "update")),
    organization_model: type = Depends(get_organization_model),
):
    """Update organization."""
    try:
        org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format",
        )
    
    org = await db.get(organization_model, org_uuid)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    try:
        # Get available columns from the model
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(organization_model)
        available_columns = {col.name for col in mapper.columns} if mapper else set()
        
        # Check if slug is unique (if being updated and model supports it)
        if org_data.slug and "slug" in available_columns and hasattr(org, "slug") and org_data.slug != org.slug:
            stmt = select(organization_model).where(organization_model.slug == org_data.slug)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization with this slug already exists",
                )
        
        # Update fields - only set attributes that exist as columns on the model
        update_data = org_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key in available_columns:
                setattr(org, key, value)
        
        await db.flush()
        await db.refresh(org)
        
        return OrganizationResponse(
            id=str(org.id),
            name=org.name,
            slug=getattr(org, "slug", None),
            description=getattr(org, "description", None),
            settings=getattr(org, "settings", {}),
            modules=getattr(org, "modules", {}),
            created_at=org.created_at.isoformat() if hasattr(org, "created_at") and org.created_at else "",
            updated_at=org.updated_at.isoformat() if hasattr(org, "updated_at") and org.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}",
        ) from e


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("organizations", "delete")),
    organization_model: type = Depends(get_organization_model),
):
    """Delete organization."""
    try:
        org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format",
        )
    
    org = await db.get(organization_model, org_uuid)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    try:
        await db.delete(org)
        await db.flush()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}",
        ) from e

