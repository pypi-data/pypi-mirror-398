"""
Users router - CRUD operations for users.

This is a base implementation. Users should extend this to work with their
specific User model and add custom business logic.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.api.v1.schemas.user import UserCreate, UserResponse, UserUpdate
from apex.core.authentication.dependencies import get_current_active_user
from apex.core.permissions.dependencies import require_permission
from apex.infrastructure.database.session import get_db

router = APIRouter(tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("users", "create")),
):
    """
    Create a new user.

    This is a base implementation. Users should override this to:
    1. Provide their User model
    2. Implement actual creation logic

    Args:
        user_data: User creation data
        db: Database session
        current_user: Current authenticated user with permissions

    Returns:
        Created user data

    Raises:
        HTTPException: If creation fails
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User creation endpoint needs to be implemented with your User model",
    )


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_active_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Get current user's own profile.
    Simple - any authenticated user can access their own data without permissions.
    """
    from apex.app.core.dependencies import get_user_model
    from apex.domain.services.user import UserService
    from uuid import UUID
    
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user in token",
        )
    
    # Get database session if not provided
    if db is None:
        from apex.infrastructure.database.session import get_db as get_db_session
        async for session in get_db_session():
            db = session
            break
    
    user_model = get_user_model()
    user_service = UserService(db, user_model)
    
    try:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    user = await user_service.get_user_by_id(str(user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(get_current_active_user),
):
    """
    Get user by ID.
    Users can access their own data, superusers can access any user.
    """
    from apex.app.core.dependencies import get_user_model
    from apex.domain.services.user import UserService
    from uuid import UUID
    
    current_user_id = current_user.get("sub")
    is_superuser = current_user.get("is_superuser", False)
    is_org_admin = current_user.get("is_org_admin", False)
    current_user_org_id = current_user.get("organization_id")
    
    user_model = get_user_model()
    user_service = UserService(db, user_model)
    
    try:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    user = await user_service.get_user_by_id(str(user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Users can access their own data
    # Superusers can access any data
    # Organization admins can access any data in their organization
    if not is_superuser and current_user_id != user_id:
        if is_org_admin:
            # Org admin: Check if target user is in same organization
            if str(user.organization_id) != current_user_org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only access users in your organization",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own data",
    )
    
    return UserResponse.model_validate(user)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("users", "read")),
    skip: int = 0,
    limit: int = 100,
    organization_id: str | None = None,
):
    """
    List users with organization-based filtering.
    
    Access Rules:
    - Admin (superuser): See ALL users in the user table (organization_id is NULL for admins)
    - Organization users: See only users in their organization
    - Users without organization: See only users without organizations

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)
        organization_id: Optional filter for admins to filter by specific org
        db: Database session
        current_user: Current authenticated user with permissions

    Returns:
        List of users based on access rules
    """
    from apex.app.core.dependencies import get_user_model
    from sqlalchemy import select
    from uuid import UUID
    
    user_model = get_user_model()
    is_superuser = current_user.get("is_superuser", False)
    is_org_admin = current_user.get("is_org_admin", False)
    current_user_org_id = current_user.get("organization_id")
    
    # Build query
    stmt = select(user_model)
    
    # Apply filtering based on user type
    if is_superuser:
        # Global Admin: See ALL users in the database
        # Optional: Filter by specific organization if requested
        if organization_id:
            try:
                org_uuid = UUID(organization_id) if isinstance(organization_id, str) else organization_id
                stmt = stmt.where(user_model.organization_id == org_uuid)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid organization ID format",
                )
        # If no organization_id filter, return ALL users (no WHERE clause)
    elif is_org_admin and current_user_org_id:
        # Organization Admin: See ALL users in their organization
        try:
            org_uuid = UUID(current_user_org_id) if isinstance(current_user_org_id, str) else current_user_org_id
            stmt = stmt.where(user_model.organization_id == org_uuid)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID in token",
            )
    elif current_user_org_id:
        # Regular user with organization: Only see users in their organization
        try:
            org_uuid = UUID(current_user_org_id) if isinstance(current_user_org_id, str) else current_user_org_id
            stmt = stmt.where(user_model.organization_id == org_uuid)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID in token",
            )
    else:
        # User without organization: Only see users without organizations
        stmt = stmt.where(user_model.organization_id.is_(None))
    
    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    
    # Execute query
    try:
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}",
        ) from e


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("users", "update")),
):
    """
    Update user.

    Args:
        user_id: User UUID
        user_data: User update data
        db: Database session
        current_user: Current authenticated user with permissions

    Returns:
        Updated user data

    Raises:
        HTTPException: If user not found or update fails
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update user endpoint needs to be implemented with your User model",
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: dict = Depends(require_permission("users", "delete")),
):
    """
    Delete user.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated user with permissions

    Raises:
        HTTPException: If user not found or deletion fails
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete user endpoint needs to be implemented with your User model",
    )

