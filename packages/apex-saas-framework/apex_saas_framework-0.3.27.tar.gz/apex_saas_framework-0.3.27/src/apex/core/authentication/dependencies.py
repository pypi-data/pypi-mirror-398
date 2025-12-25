"""FastAPI dependencies for authentication."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from apex.core.security.jwt import decode_token
from apex.infrastructure.database.session import get_db

# HTTP Bearer scheme for token extraction
oauth2_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token.
    Loads user from database with roles and permissions.

    Args:
        credentials: HTTP Bearer credentials containing the token
        db: Database session

    Returns:
        User payload with permissions and roles

    Raises:
        HTTPException: If token is invalid or user not found
    """
    from apex.app.core.dependencies import get_user_model
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Extract token from credentials
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Token type validation
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception

        # Load user from database with roles and permissions
        from uuid import UUID
        user_model = get_user_model()
        
        # Convert user_id string to UUID if needed
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, TypeError):
            raise credentials_exception
        
        # Try to load with relationships, fallback to simple query if relationships don't exist
        try:
            result = await db.execute(
                select(user_model)
                .options(
                    selectinload("roles").selectinload("permissions"),
                )
                .where(user_model.id == user_uuid)
            )
        except Exception:
            # Fallback: try without relationships
            result = await db.execute(
                select(user_model).where(user_model.id == user_uuid)
            )
        
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise credentials_exception
        
        # Build permissions list from roles
        permissions = []
        if hasattr(user, "roles") and user.roles:
            for role in user.roles:
                if hasattr(role, "permissions") and role.permissions:
                    for perm in role.permissions:
                        if hasattr(perm, "code"):
                            permissions.append(perm.code)
        
        # Return user data with permissions
        return {
            "sub": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": getattr(user, "is_superuser", False),
            "is_org_admin": getattr(user, "is_org_admin", False),
            "organization_id": str(user.organization_id) if user.organization_id else None,
            "permissions": permissions,
            "roles": [role.name for role in (user.roles or [])] if hasattr(user, "roles") else [],
        }

    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Dependency to ensure current user is active.

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current user payload

    Raises:
        HTTPException: If user is not active
    """
    is_active = current_user.get("is_active", True)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))] = None,
) -> dict[str, Any] | None:
    """
    Optional authentication dependency.

    Returns user if token is valid, None otherwise.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        User payload or None
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return payload
    except Exception:
        return None

