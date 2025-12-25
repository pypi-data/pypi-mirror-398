"""User domain model."""

from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from apex.infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from apex.domain.models.organization import BaseOrganization
    from apex.domain.models.role import BaseRole


class BaseUser(BaseModel):
    """
    Abstract base user model.

    Users should extend this class to create their own User model.
    Example:
        class User(BaseUser):
            __tablename__ = "users"
    """

    __abstract__ = True

    # Basic fields (as per requirements: email, first_name, last_name, phone, country)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_org_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="Organization admin has full access within their organization")
    
    # Consent fields (GDPR compliance)
    accept_terms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="User has accepted Terms and Conditions and Privacy Policy")
    accept_terms_date: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Date when terms were accepted (ISO format)")
    newsletter_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="User consent to receive newsletters and updates")
    newsletter_consent_date: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Date when newsletter consent was given (ISO format)")
    
    # Password reset token (for forgot password flow)
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    reset_token_expires: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Multi-tenant
    organization_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Flexible settings stored as JSONB
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Relationships - using @declared_attr for abstract base classes
    @declared_attr
    def organization(cls) -> Mapped["BaseOrganization | None"]:
        """Organization relationship"""
        return relationship(
            "BaseOrganization",
            back_populates="users",
            lazy="selectin",
            foreign_keys=[cls.organization_id],
        )
    
    @declared_attr
    def roles(cls) -> Mapped[list["BaseRole"]]:
        """Roles relationship"""
        return relationship(
            "BaseRole",
            secondary="user_roles",
            back_populates="users",
            lazy="selectin",
        )
    
    @property
    def hashed_password(self) -> str:
        """Alias for password_hash for backward compatibility."""
        return self.password_hash
    
    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        """Setter for hashed_password alias."""
        self.password_hash = value

