"""Permission domain model."""

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from apex.infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from apex.domain.models.role import BaseRole


class BasePermission(BaseModel):
    """
    Abstract base permission model.

    Users should extend this class to create their own Permission model.
    Example:
        class Permission(BasePermission):
            __tablename__ = "permissions"
    """

    __abstract__ = True

    # Basic fields
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    resource: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    action: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships - using @declared_attr for abstract base classes
    @declared_attr
    def roles(cls) -> Mapped[list["BaseRole"]]:
        """Roles relationship"""
        return relationship(
            "BaseRole",
            secondary="role_permissions",
            back_populates="permissions",
            lazy="selectin",
        )

