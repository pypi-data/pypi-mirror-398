"""
Declarative base exports for generated projects.
"""
from apex.infrastructure.database.base import (  # noqa: F401
    Base,
    BaseModel,
    TimestampMixin,
    UUIDMixin,
)

__all__ = ["Base", "BaseModel", "TimestampMixin", "UUIDMixin"]

