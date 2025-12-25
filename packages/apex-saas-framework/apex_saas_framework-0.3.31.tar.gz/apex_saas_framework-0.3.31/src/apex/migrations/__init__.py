"""
Database migration helpers - Secure migration system.

Works with PostgreSQL, MySQL, and SQLite only.

Usage:
    from apex.migrations import setup_alembic, get_sync_url, find_models
    
    # Auto-setup Alembic (works with PostgreSQL, MySQL, SQLite)
    setup_alembic()
    
    # Get sync URL (automatically validated and secured)
    sync_url = get_sync_url()
    
    # Find your models
    files, classes = find_models()
"""

# Import from the actual module file, not from __init__
from apex.migrations.migrations import setup_alembic, get_sync_url, find_models
from apex.migrations.security import (
    validate_database_url,
    sanitize_database_url,
    mask_sensitive_url,
)

__all__ = [
    "setup_alembic",
    "get_sync_url",
    "find_models",
    "validate_database_url",
    "sanitize_database_url",
    "mask_sensitive_url",
]

