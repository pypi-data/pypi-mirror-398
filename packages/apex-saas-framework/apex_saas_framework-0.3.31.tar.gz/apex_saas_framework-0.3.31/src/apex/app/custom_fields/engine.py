"""
Custom Fields Engine for Apex Framework.

This module provides utilities for detecting and managing custom fields
added to base models through ORM inheritance.

The engine automatically detects new columns in extended models and
integrates with Alembic to generate ALTER TABLE migrations.
"""
from __future__ import annotations

import inspect
from typing import Any, Dict, List, Set, Type

from sqlalchemy import Column, inspect as sa_inspect
from sqlalchemy.orm import DeclarativeBase


def get_base_model_columns(model: Type[DeclarativeBase]) -> Set[str]:
    """
    Get all column names from the base model (excluding inherited columns).

    Args:
        model: SQLAlchemy model class

    Returns:
        Set of column names defined in base classes
    """
    columns: Set[str] = set()
    
    # Get all base classes (excluding the model itself)
    for base in inspect.getmro(model):
        if base is model or base is object:
            continue
        
        # Check if it's a SQLAlchemy model
        if hasattr(base, "__table__") or hasattr(base, "__mapper__"):
            mapper = sa_inspect(base)
            if mapper:
                for column in mapper.columns:
                    columns.add(column.name)
    
    return columns


def get_model_columns(model: Type[DeclarativeBase]) -> Set[str]:
    """
    Get all column names from a model (including inherited).

    Args:
        model: SQLAlchemy model class

    Returns:
        Set of all column names in the model
    """
    mapper = sa_inspect(model)
    if not mapper:
        return set()
    
    return {col.name for col in mapper.columns}


def detect_custom_fields(model: Type[DeclarativeBase]) -> Dict[str, Column[Any]]:
    """
    Detect custom fields added to a model that extends a base model.

    Custom fields are columns defined in the model itself but not in its base classes.

    Args:
        model: SQLAlchemy model class that extends a base model

    Returns:
        Dictionary mapping field names to Column objects
    """
    base_columns = get_base_model_columns(model)
    all_columns = get_model_columns(model)
    
    custom_fields: Dict[str, Column[Any]] = {}
    
    mapper = sa_inspect(model)
    if mapper:
        for column in mapper.columns:
            if column.name not in base_columns:
                # This is a custom field
                custom_fields[column.name] = column
    
    return custom_fields


def get_custom_fields_summary(models: List[Type[DeclarativeBase]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get a summary of all custom fields across multiple models.

    Args:
        models: List of SQLAlchemy model classes

    Returns:
        Dictionary mapping model names to lists of custom field info
    """
    summary: Dict[str, List[Dict[str, Any]]] = {}
    
    for model in models:
        custom_fields = detect_custom_fields(model)
        if custom_fields:
            model_name = model.__name__
            summary[model_name] = []
            
            for field_name, column in custom_fields.items():
                summary[model_name].append({
                    "name": field_name,
                    "type": str(column.type),
                    "nullable": column.nullable,
                    "default": column.default.arg if column.default else None,
                })
    
    return summary


def validate_custom_field(model: Type[DeclarativeBase], field_name: str) -> bool:
    """
    Validate that a field name doesn't conflict with base model fields.

    Args:
        model: SQLAlchemy model class
        field_name: Name of the field to validate

    Returns:
        True if field name is valid, False if it conflicts
    """
    base_columns = get_base_model_columns(model)
    return field_name not in base_columns


def register_custom_field(
    model: Type[DeclarativeBase],
    name: str,
    column: Column[Any],
    validate: bool = True,
) -> None:
    """
    Register a custom field on a model at runtime.

    This is useful for dynamic field addition, though static definition
    in the model class is preferred.

    Args:
        model: SQLAlchemy model class
        name: Field name
        column: SQLAlchemy Column object
        validate: Whether to validate the field name

    Raises:
        ValueError: If field name conflicts with base model fields
        AttributeError: If field already exists
    """
    if validate and not validate_custom_field(model, name):
        raise ValueError(
            f"{model.__name__}.{name} conflicts with a base model field. "
            f"Choose a different name."
        )
    
    if hasattr(model, name):
        raise AttributeError(f"{model.__name__}.{name} already exists")
    
    setattr(model, name, column)


def compare_models(
    base_model: Type[DeclarativeBase],
    extended_model: Type[DeclarativeBase],
) -> Dict[str, Column[Any]]:
    """
    Compare a base model with an extended model to find new fields.

    Args:
        base_model: Base model class
        extended_model: Extended model class

    Returns:
        Dictionary of new fields in extended_model
    """
    base_columns = get_model_columns(base_model)
    extended_columns = get_model_columns(extended_model)
    
    new_fields: Dict[str, Column[Any]] = {}
    
    extended_mapper = sa_inspect(extended_model)
    if extended_mapper:
        for column in extended_mapper.columns:
            if column.name not in base_columns:
                new_fields[column.name] = column
    
    return new_fields


def generate_alter_table_statements(
    model: Type[DeclarativeBase],
    custom_fields: Dict[str, Column[Any]],
) -> List[str]:
    """
    Generate ALTER TABLE SQL statements for custom fields.

    Note: This is a helper function. Alembic's autogenerate feature
    should handle migration generation automatically.

    Args:
        model: SQLAlchemy model class
        custom_fields: Dictionary of custom field names to Column objects

    Returns:
        List of ALTER TABLE SQL statements
    """
    if not custom_fields:
        return []
    
    table_name = model.__tablename__ if hasattr(model, "__tablename__") else model.__name__.lower()
    statements: List[str] = []
    
    for field_name, column in custom_fields.items():
        # Generate column definition
        col_type = str(column.type)
        nullable = "NULL" if column.nullable else "NOT NULL"
        default = ""
        
        if column.default:
            default_val = column.default.arg
            if isinstance(default_val, str):
                default = f" DEFAULT '{default_val}'"
            else:
                default = f" DEFAULT {default_val}"
        
        statement = f"ALTER TABLE {table_name} ADD COLUMN {field_name} {col_type} {nullable}{default};"
        statements.append(statement)
    
    return statements


__all__ = [
    "get_base_model_columns",
    "get_model_columns",
    "detect_custom_fields",
    "get_custom_fields_summary",
    "validate_custom_field",
    "register_custom_field",
    "compare_models",
    "generate_alter_table_statements",
]
