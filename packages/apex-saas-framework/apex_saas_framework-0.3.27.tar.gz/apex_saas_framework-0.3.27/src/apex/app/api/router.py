"""
Unified API router that wires all module routers with configurable prefixes.
"""
from fastapi import APIRouter

from apex.app.auth.routes import router as auth_router
from apex.app.modules.routes import router as modules_router
from apex.app.organizations.routes import router as organizations_router
from apex.app.payments.routes import router as payments_router
from apex.app.permissions.routes import router as permissions_router
from apex.app.roles.routes import router as roles_router
from apex.app.settings.routes import router as settings_router
from apex.app.users.routes import router as users_router


def get_api_router(prefix: str = "/api/v1") -> APIRouter:
    router = APIRouter(prefix=prefix)
    router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    router.include_router(users_router, prefix="/users", tags=["Users"])
    router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
    router.include_router(roles_router, prefix="/roles", tags=["Roles"])
    router.include_router(permissions_router, prefix="/permissions", tags=["Permissions"])
    router.include_router(settings_router, prefix="/settings", tags=["Settings"])
    router.include_router(modules_router, prefix="/modules", tags=["Modules"])
    router.include_router(payments_router, prefix="/payments", tags=["Payments"])
    return router


__all__ = ["get_api_router"]

