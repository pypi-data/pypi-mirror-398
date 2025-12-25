"""Organization domain models."""

from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from apex.infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from apex.domain.models.user import BaseUser


class BaseOrganization(BaseModel):
    """
    Abstract base organization model.

    Users should extend this class to create their own Organization model.
    Example:
        class Organization(BaseOrganization):
            __tablename__ = "organizations"
    """

    __abstract__ = True

    # Basic fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Flexible settings stored as JSONB
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    
    # Modules / Feature Flags stored as JSONB
    # Example: {"customer_management": true, "invoice_system": false}
    modules: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Relationships - using @declared_attr for abstract base classes
    @declared_attr
    def users(cls) -> Mapped[list["BaseUser"]]:
        """Users relationship"""
        return relationship(
            "BaseUser",
            back_populates="organization",
            lazy="selectin",
        )
    
    @declared_attr
    def locations(cls) -> Mapped[list["BaseOrganizationLocation"]]:
        """Locations relationship"""
        return relationship(
            "BaseOrganizationLocation",
            back_populates="organization",
            lazy="selectin",
            cascade="all, delete-orphan",
        )


class BaseOrganizationLocation(BaseModel):
    """
    Abstract base organization location model.

    Users should extend this class to create their own OrganizationLocation model.
    Example:
        class OrganizationLocation(BaseOrganizationLocation):
            __tablename__ = "organization_locations"
    """

    __abstract__ = True

    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Flexible settings stored as JSONB
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Relationships - using @declared_attr for abstract base classes
    @declared_attr
    def organization(cls) -> Mapped["BaseOrganization"]:
        """Organization relationship"""
        return relationship(
            "BaseOrganization",
            back_populates="locations",
            lazy="selectin",
            foreign_keys=[cls.organization_id],
        )

