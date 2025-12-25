"""Resource classes for Apex Client"""

from apex.resources.users import Users
from apex.resources.auth import Auth
from apex.resources.organizations import Organizations
from apex.resources.roles import Roles
from apex.resources.permissions import Permissions
from apex.resources.modules import Modules
from apex.resources.settings import Settings
from apex.resources.payments import Payments
from apex.resources.email import Email
from apex.resources.files import Files

__all__ = [
    "Users",
    "Auth",
    "Organizations",
    "Roles",
    "Permissions",
    "Modules",
    "Settings",
    "Payments",
    "Email",
    "Files",
]


