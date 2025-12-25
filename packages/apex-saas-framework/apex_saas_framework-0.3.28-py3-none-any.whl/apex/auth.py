"""
Authentication functions - LangChain-style direct imports.

Usage:
    from apex.auth import signup, login
    
    # Set client once
    from apex import Client, set_default_client
    client = Client(database_url="...", user_model=User)
    set_default_client(client)
    
    # Use functions directly (no await, no client parameter)
    user = signup(email="user@example.com", password="pass123")
    tokens = login(email="user@example.com", password="pass123")
"""

from typing import Any, Dict, Optional

from apex.client import Client
from apex.sync import (
    signup as _signup,
    login as _login,
    verify_token as _verify_token,
    refresh_token as _refresh_token,
    forgot_password as _forgot_password,
    reset_password as _reset_password,
    change_password as _change_password,
    set_default_client as _set_default_client,
)


def set_client(client: Client) -> None:
    """Set the default client for auth operations."""
    _set_default_client(client)


def signup(
    email: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    client: Optional[Client] = None,
    **kwargs
) -> Any:
    """
    Sign up a new user.
    
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
        from apex.auth import signup, set_client
        from apex import Client
        
        client = Client(database_url="...", user_model=User)
        set_client(client)
        user = signup(email="user@example.com", password="pass123")
    """
    return _signup(client=client, email=email, password=password, first_name=first_name, last_name=last_name, **kwargs)


def login(
    email: str,
    password: str,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Login user and get tokens.
    
    Args:
        email: User email
        password: User password
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Dictionary with access_token, refresh_token, and token_type
    
    Example:
        from apex.auth import login
        tokens = login(email="user@example.com", password="pass123")
    """
    return _login(client=client, email=email, password=password)


def verify_token(
    token: str,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Verify JWT token and return payload.
    
    Args:
        token: JWT access token
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Token payload dictionary
    
    Example:
        from apex.auth import verify_token
        payload = verify_token(token="eyJ...")
    """
    return _verify_token(token=token, client=client)


def refresh_token(
    refresh_token: str,
    client: Optional[Client] = None,
) -> Dict[str, Any]:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Refresh token string
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Dictionary with new access_token and token_type
    
    Example:
        from apex.auth import refresh_token
        new_tokens = refresh_token(refresh_token="...")
    """
    return _refresh_token(refresh_token=refresh_token, client=client)


def forgot_password(
    email: str,
    client: Optional[Client] = None,
) -> tuple[Any, str | None]:
    """
    Request password reset for a user.
    
    Args:
        email: User email address
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Tuple of (user, reset_token) if user found, (None, None) otherwise
    
    Example:
        from apex.auth import forgot_password
        user, token = forgot_password(email="user@example.com")
    """
    return _forgot_password(client=client, email=email)


def reset_password(
    token: str,
    new_password: str,
    client: Optional[Client] = None,
) -> bool:
    """
    Reset user password using reset token.
    
    Args:
        token: Reset token from forgot_password
        new_password: New password to set
        client: Optional client instance (uses default if not provided)
    
    Returns:
        True if password was reset successfully, False otherwise
    
    Example:
        from apex.auth import reset_password
        success = reset_password(token="...", new_password="NewPass123!")
    """
    return _reset_password(client=client, token=token, new_password=new_password)


def change_password(
    user_id: Any,
    old_password: str,
    new_password: str,
    client: Optional[Client] = None,
) -> bool:
    """
    Change user password (authenticated user).
    
    Args:
        user_id: User ID
        old_password: Current password
        new_password: New password
        client: Optional client instance (uses default if not provided)
    
    Returns:
        True if password changed, False if old password incorrect
    
    Example:
        from apex.auth import change_password
        success = change_password(user_id=user.id, old_password="OldPass", new_password="NewPass")
    """
    return _change_password(client=client, user_id=user_id, old_password=old_password, new_password=new_password)


__all__ = ["signup", "login", "verify_token", "refresh_token", "forgot_password", "reset_password", "change_password", "set_client"]

