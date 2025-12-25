"""Role domain model."""

from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from apex.infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from apex.domain.models.permission import BasePermission
    from apex.domain.models.user import BaseUser


class BaseRole(BaseModel):
    """
    Abstract base role model.

    Users should extend this class to create their own Role model.
    Example:
        class Role(BaseRole):
            __tablename__ = "roles"
    """

    __abstract__ = True

    # Basic fields
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Multi-tenant (optional - roles can be global or org-specific)
    organization_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Relationships - using @declared_attr for abstract base classes
    @declared_attr
    def users(cls) -> Mapped[list["BaseUser"]]:
        """Users relationship"""
        return relationship(
            "BaseUser",
            secondary="user_roles",
            back_populates="roles",
            lazy="selectin",
        )
    
    @declared_attr
    def permissions(cls) -> Mapped[list["BasePermission"]]:
        """Permissions relationship"""
        return relationship(
            "BasePermission",
            secondary="role_permissions",
            back_populates="roles",
            lazy="selectin",
        )

