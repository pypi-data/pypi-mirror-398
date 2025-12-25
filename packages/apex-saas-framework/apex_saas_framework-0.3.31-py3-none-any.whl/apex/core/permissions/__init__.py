"""Permissions and RBAC module."""

from apex.core.permissions.dependencies import (
    require_permission,
    require_role,
    require_superuser,
)

__all__ = [
    "require_permission",
    "require_role",
    "require_superuser",
]

