"""FastAPI dependencies for permissions and RBAC."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status

from apex.core.authentication.dependencies import get_current_active_user


def require_superuser(
    current_user: Annotated[dict[str, Any], Depends(get_current_active_user)],
) -> dict[str, Any]:
    """
    Dependency to require superuser privileges.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user payload

    Raises:
        HTTPException: If user is not a superuser
    """
    is_superuser = current_user.get("is_superuser", False)
    if not is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required",
        )
    return current_user


def require_role(role_name: str):
    """
    Factory function to create a dependency that requires a specific role.

    Args:
        role_name: Name of the required role

    Returns:
        Dependency function
    """

    async def role_checker(
        current_user: Annotated[dict[str, Any], Depends(get_current_active_user)],
    ) -> dict[str, Any]:
        """
        Check if user has the required role.

        This is a base implementation. Users should override this to check
        actual roles from the database.

        Args:
            current_user: Current authenticated user

        Returns:
            Current user payload

        Raises:
            HTTPException: If user doesn't have the required role
        """
        # Base implementation - users should override to check actual roles
        user_roles = current_user.get("roles", [])
        if role_name not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required",
            )
        return current_user

    return role_checker


def require_permission(resource: str, action: str):
    """
    Factory function to create a dependency that requires a specific permission.

    Args:
        resource: Resource name (e.g., 'users', 'organizations')
        action: Action name (e.g., 'create', 'read', 'update', 'delete')

    Returns:
        Dependency function
    """

    async def permission_checker(
        current_user: Annotated[dict[str, Any], Depends(get_current_active_user)],
    ) -> dict[str, Any]:
        """
        Check if user has the required permission.
        Superusers and organization admins bypass permission checks.

        Args:
            current_user: Current authenticated user

        Returns:
            Current user payload

        Raises:
            HTTPException: If user doesn't have the required permission
        """
        # Superusers bypass all permission checks
        is_superuser = current_user.get("is_superuser", False)
        if is_superuser:
            return current_user
        
        # Organization admins bypass permission checks for their organization
        # They have full access within their organization
        is_org_admin = current_user.get("is_org_admin", False)
        if is_org_admin:
            return current_user
        
        # Base implementation - users should override this to check
        # actual permissions from the database
        user_permissions = current_user.get("permissions", [])
        permission_key = f"{resource}:{action}"
        if permission_key not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_key}' required",
            )
        return current_user

    return permission_checker

