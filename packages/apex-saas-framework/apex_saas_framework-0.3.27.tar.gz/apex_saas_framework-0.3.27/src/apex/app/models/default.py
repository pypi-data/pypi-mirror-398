"""
Default concrete models used by the generator.

Developers can extend these or provide their own subclasses.
"""
from sqlalchemy.orm import relationship

from apex.app.models import (
    BaseOrganization,
    BaseOrganizationLocation,
    BaseOrganizationSettings,
    BasePayment,
    BasePermission,
    BaseRole,
    BaseUser,
)


class Organization(BaseOrganization):
    __tablename__ = "organizations"

    users = relationship("User", back_populates="organization", lazy="selectin")
    locations = relationship("OrganizationLocation", back_populates="organization", lazy="selectin")
    settings = relationship("OrganizationSettings", back_populates="organization", uselist=False, lazy="selectin")


class OrganizationLocation(BaseOrganizationLocation):
    __tablename__ = "organization_locations"

    organization = relationship("Organization", back_populates="locations", lazy="selectin")


class OrganizationSettings(BaseOrganizationSettings):
    __tablename__ = "organization_settings"

    organization = relationship("Organization", back_populates="settings", lazy="selectin")


class User(BaseUser):
    __tablename__ = "users"

    organization = relationship("Organization", back_populates="users", lazy="selectin")
    roles = relationship("Role", secondary="user_roles", back_populates="users", lazy="selectin")


class Role(BaseRole):
    __tablename__ = "roles"

    users = relationship("User", secondary="user_roles", back_populates="roles", lazy="selectin")
    permissions = relationship(
        "Permission", secondary="role_permissions", back_populates="roles", lazy="selectin"
    )


class Permission(BasePermission):
    __tablename__ = "permissions"

    roles = relationship(
        "Role", secondary="role_permissions", back_populates="permissions", lazy="selectin"
    )


class Payment(BasePayment):
    __tablename__ = "payments"


__all__ = [
    "User",
    "Organization",
    "OrganizationLocation",
    "Role",
    "Permission",
    "OrganizationSettings",
    "Payment",
]

