"""API v1 module."""

from apex.api.v1.auth import router as auth_router
from apex.api.v1.modules import router as modules_router
from apex.api.v1.organizations import router as organizations_router
from apex.api.v1.payments import router as payments_router
from apex.api.v1.permissions import router as permissions_router
from apex.api.v1.roles import router as roles_router
from apex.api.v1.settings import router as settings_router
from apex.api.v1.users import router as users_router

__all__ = [
    "auth_router",
    "users_router",
    "organizations_router",
    "roles_router",
    "permissions_router",
    "modules_router",
    "settings_router",
    "payments_router",
]

