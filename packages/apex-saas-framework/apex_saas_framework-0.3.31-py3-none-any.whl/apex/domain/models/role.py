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
    
    To match existing database schema, override organization_id:
        class Role(BaseRole):
            __tablename__ = "roles"
            # Override to match existing schema (VARCHAR, INTEGER, etc.)
            organization_id: Mapped[str | None] = mapped_column(
                String(36),  # or Integer, or your existing type
                ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=True,
                index=True,
            )
    
    To use existing table's primary key as foreign key:
        class Role(BaseRole):
            __tablename__ = "roles"
            # Reference existing companies table with INTEGER primary key
            company_id: Mapped[int | None] = mapped_column(
                Integer,
                ForeignKey("companies.id", ondelete="CASCADE"),
                nullable=True,
                index=True,
            )
    """

    __abstract__ = True

    # Basic fields
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Multi-tenant (optional - roles can be global or org-specific)
    # NOTE: Override this field in your concrete model to match existing schema
    # if your database uses VARCHAR, INTEGER, or other types for foreign keys.
    # The framework will only auto-migrate framework-created VARCHAR(36) columns.
    # For custom schemas, override this field to match your existing table structure.
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

