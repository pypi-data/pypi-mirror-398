"""
Custom Fields Engine for Apex Framework.

This module provides utilities for detecting and managing custom fields
added to base models through ORM inheritance.
"""
from apex.app.custom_fields.engine import (
    compare_models,
    detect_custom_fields,
    generate_alter_table_statements,
    get_base_model_columns,
    get_custom_fields_summary,
    get_model_columns,
    register_custom_field,
    validate_custom_field,
)

__all__ = [
    "detect_custom_fields",
    "get_custom_fields_summary",
    "get_base_model_columns",
    "get_model_columns",
    "validate_custom_field",
    "register_custom_field",
    "compare_models",
    "generate_alter_table_statements",
]

