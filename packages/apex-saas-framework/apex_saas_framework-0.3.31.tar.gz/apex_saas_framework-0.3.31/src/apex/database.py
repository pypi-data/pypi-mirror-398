"""
Database utilities - Secure URL conversion and connection helpers.

Works with PostgreSQL, MySQL, and SQLite only.

Usage:
    from apex.database import get_sync_url, get_async_url, validate_url
    
    # Get URLs (automatically validated and secured)
    sync_url = get_sync_url()   # For Alembic migrations
    async_url = get_async_url()  # For async operations
    
    # Validate URL manually
    is_valid = validate_url("postgresql://user:pass@localhost/db")
"""

from apex.infrastructure.database.session import (
    get_sync_database_url,
    get_database_url,
)
from apex.migrations.security import validate_database_url, mask_sensitive_url

# Clear, simple aliases with security
def get_sync_url(database_url: str = None) -> str:
    """
    Get synchronous database URL for migrations.
    
    Automatically validates and secures the URL.
    Supports PostgreSQL, MySQL, and SQLite only.
    
    Args:
        database_url: Optional database URL (uses .env if not provided)
    
    Returns:
        Synchronous database URL compatible with Alembic
    
    Raises:
        ValueError: If URL is invalid, contains security issues, or uses unsupported database
    """
    return get_sync_database_url(database_url)


def get_async_url(database_url: str = None) -> str:
    """
    Get asynchronous database URL for async operations.
    
    Automatically validates and secures the URL.
    Supports PostgreSQL, MySQL, and SQLite only.
    
    Args:
        database_url: Optional database URL (uses .env if not provided)
    
    Returns:
        Asynchronous database URL
    
    Raises:
        ValueError: If URL is invalid, contains security issues, or uses unsupported database
    """
    return get_database_url()


def validate_url(url: str) -> bool:
    """
    Validate database URL format and security.
    
    Args:
        url: Database URL string
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If URL is invalid or contains security issues
    """
    return validate_database_url(url)


__all__ = [
    "get_sync_url",
    "get_async_url",
    "get_sync_database_url",
    "get_database_url",
    "validate_url",
    "validate_database_url",
    "mask_sensitive_url",
]

