"""Domain models module."""

# Import abstract base models - users will extend these
from apex.domain.models.user import BaseUser
from apex.domain.models.organization import BaseOrganization, BaseOrganizationLocation
from apex.domain.models.role import BaseRole
from apex.domain.models.permission import BasePermission

__all__ = [
    # Base models (for users to extend)
    "BaseUser",
    "BaseOrganization",
    "BaseOrganizationLocation",
    "BaseRole",
    "BasePermission",
]

