"""
User management functions - LangChain-style direct imports.

Usage:
    from apex.users import create_user, get_user
    
    # Set client once
    from apex import Client, set_default_client
    client = Client(database_url="...", user_model=User)
    set_default_client(client)
    
    # Use functions directly (no await, no client parameter)
    user = create_user(email="user@example.com", password="pass123")
    user = get_user(user_id=user.id)
"""

from typing import Any, Optional

from apex.client import Client
from apex.sync import (
    create_user as _create_user,
    get_user as _get_user,
    update_user as _update_user,
    delete_user as _delete_user,
    set_default_client as _set_default_client,
)


def set_client(client: Client) -> None:
    """Set the default client for user operations."""
    _set_default_client(client)


def create_user(
    email: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    client: Optional[Client] = None,
    **kwargs
) -> Any:
    """
    Create a new user.
    
    Args:
        email: User email
        password: User password
        first_name: First name (optional)
        last_name: Last name (optional)
        client: Optional client instance (uses default if not provided)
        **kwargs: Additional user fields
    
    Returns:
        Created user instance
    
    Example:
        from apex.users import create_user, set_client
        from apex import Client
        
        client = Client(database_url="...", user_model=User)
        set_client(client)
        user = create_user(email="user@example.com", password="pass123")
    """
    return _create_user(client=client, email=email, password=password, first_name=first_name, last_name=last_name, **kwargs)


def get_user(
    user_id: Optional[Any] = None,
    email: Optional[str] = None,
    client: Optional[Client] = None,
) -> Optional[Any]:
    """
    Get a user by ID or email.
    
    Args:
        user_id: User ID (optional)
        email: User email (optional)
        client: Optional client instance (uses default if not provided)
    
    Returns:
        User instance or None
    
    Example:
        from apex.users import get_user
        user = get_user(user_id=1)
        user = get_user(email="user@example.com")
    """
    return _get_user(client=client, user_id=user_id, email=email)


def update_user(
    user_id: Any,
    client: Optional[Client] = None,
    **kwargs
) -> Any:
    """
    Update a user.
    
    Args:
        user_id: User ID
        client: Optional client instance (uses default if not provided)
        **kwargs: Fields to update
    
    Returns:
        Updated user instance
    
    Example:
        from apex.users import update_user
        user = update_user(user_id=1, first_name="John")
    """
    return _update_user(client=client, user_id=user_id, **kwargs)


def delete_user(
    user_id: Any,
    client: Optional[Client] = None,
) -> bool:
    """
    Delete a user.
    
    Args:
        user_id: User ID
        client: Optional client instance (uses default if not provided)
    
    Returns:
        True if deleted, False otherwise
    
    Example:
        from apex.users import delete_user
        deleted = delete_user(user_id=1)
    """
    return _delete_user(client=client, user_id=user_id)


__all__ = ["create_user", "get_user", "update_user", "delete_user", "set_client"]

