"""Utility functions module."""

from typing import Any, Type

from sqlalchemy import inspect
from sqlalchemy.orm import Mapper

from apex.core.utils.tokens import generate_reset_token, verify_reset_token


def get_primary_key_type(model_class: Type) -> Type:
    """
    Get the Python type of the primary key for a given SQLAlchemy model.
    """
    mapper: Mapper = inspect(model_class)
    pk_column = mapper.primary_key[0]
    return pk_column.type.python_type


def get_primary_key_column(model_class: Type) -> str:
    """
    Get the primary key column name for a given SQLAlchemy model.
    """
    mapper: Mapper = inspect(model_class)
    pk_column = mapper.primary_key[0]
    return pk_column.name


def convert_id_to_type(id_value: Any, target_type: Type) -> Any:
    """
    Convert ID value to the appropriate type.
    Handles asyncpg UUID objects, MySQL string UUIDs, and other database-specific types.
    """
    # If already the correct type, return as-is
    if isinstance(id_value, target_type):
        return id_value
    
    # Handle int
    if target_type == int:
        return int(id_value)
    
    # Handle str
    if target_type == str:
        return str(id_value)
    
    # Handle UUID - works with PostgreSQL (asyncpg UUID), MySQL (string UUID), and SQLite (string UUID)
    try:
        import uuid
        # Check if target_type is UUID (either Python uuid.UUID or PostgreSQL UUID type)
        is_uuid_type = (
            target_type == uuid.UUID or
            (hasattr(target_type, '__name__') and 'UUID' in target_type.__name__) or
            str(target_type).endswith('UUID')
        )
        
        if is_uuid_type:
            # If it's already a UUID-like object (asyncpg UUID or Python UUID), convert properly
            if isinstance(id_value, uuid.UUID):
                # Already a Python UUID, return as-is
                return id_value
            elif hasattr(id_value, 'hex'):  # asyncpg UUID or other UUID-like object
                # Convert asyncpg UUID to Python UUID via string
                return uuid.UUID(str(id_value))
            elif isinstance(id_value, str):
                # MySQL/SQLite store UUIDs as strings (CHAR(36))
                # Validate it's a valid UUID string
                try:
                    return uuid.UUID(id_value)
                except ValueError:
                    # Not a valid UUID string, return as string
                    return id_value
            elif isinstance(id_value, bytes):
                return uuid.UUID(bytes=id_value)
            else:
                # Try string conversion as fallback
                return uuid.UUID(str(id_value))
    except (ValueError, TypeError, AttributeError):
        pass
    
    # Try generic conversion
    try:
        if hasattr(target_type, "__call__"):
            return target_type(id_value)
    except (ValueError, TypeError):
        pass
    
    return id_value


__all__ = [
    "generate_reset_token",
    "verify_reset_token",
    "get_primary_key_type",
    "get_primary_key_column",
    "convert_id_to_type",
]

