"""
Utility functions for working with dynamic models.
"""
from typing import Any, Type
from sqlalchemy import inspect
from sqlalchemy.orm import Mapper


def get_primary_key_column(model_class: Type) -> str:
    """
    Get the primary key column name from a model.
    
    Args:
        model_class: SQLAlchemy model class
    
    Returns:
        Primary key column name (e.g., 'id', 'user_id', etc.)
    
    Raises:
        ValueError: If model has no primary key or multiple primary keys
    """
    mapper: Mapper = inspect(model_class)
    pk_columns = [col.name for col in mapper.primary_key]
    
    if not pk_columns:
        raise ValueError(f"Model {model_class.__name__} has no primary key")
    if len(pk_columns) > 1:
        raise ValueError(f"Model {model_class.__name__} has composite primary key - use get() with specific columns")
    
    return pk_columns[0]


def get_primary_key_type(model_class: Type) -> Type:
    """
    Get the Python type of the primary key.
    
    Args:
        model_class: SQLAlchemy model class
    
    Returns:
        Primary key Python type (int, str, UUID, etc.)
    """
    mapper: Mapper = inspect(model_class)
    pk_column = mapper.primary_key[0]
    
    # Get Python type from SQLAlchemy type
    try:
        python_type = pk_column.type.python_type
        return python_type
    except (AttributeError, NotImplementedError):
        # Fallback: try to infer from type name
        type_name = str(pk_column.type)
        if 'INTEGER' in type_name.upper() or 'INT' in type_name.upper():
            return int
        elif 'VARCHAR' in type_name.upper() or 'STRING' in type_name.upper() or 'TEXT' in type_name.upper():
            return str
        elif 'UUID' in type_name.upper():
            try:
                from uuid import UUID
                return UUID
            except ImportError:
                return str
        else:
            # Default to string if can't determine
            return str


def convert_id_to_type(id_value: Any, target_type: Type) -> Any:
    """
    Convert ID value to the appropriate type.
    
    Args:
        id_value: ID value (can be string, int, UUID, etc.)
        target_type: Target Python type
    
    Returns:
        Converted ID value
    """
    if target_type == int:
        return int(id_value)
    elif target_type == str:
        return str(id_value)
    else:
        # For UUID or other types, try to convert from string
        try:
            if hasattr(target_type, '__call__'):
                return target_type(id_value)
        except (ValueError, TypeError):
            pass
        return id_value


def get_model_columns(model_class: Type) -> list[str]:
    """
    Get all column names from a model.
    
    Args:
        model_class: SQLAlchemy model class
    
    Returns:
        List of column names
    """
    mapper: Mapper = inspect(model_class)
    return [col.name for col in mapper.columns]


def has_column(model_class: Type, column_name: str) -> bool:
    """
    Check if model has a specific column.
    
    Args:
        model_class: SQLAlchemy model class
        column_name: Column name to check
    
    Returns:
        True if column exists
    """
    return column_name in get_model_columns(model_class)

