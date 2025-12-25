"""
Base user model supporting inheritance and JSONB settings.
"""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from apex.app.database.base import BaseModel
from apex.app.models.associations import user_role_table


class BaseUser(BaseModel):
    """Abstract user entity."""

    __abstract__ = True

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_org_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="Organization admin has full access within their organization")

    # Consent fields (GDPR compliance)
    accept_terms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="User has accepted Terms and Conditions and Privacy Policy")
    accept_terms_date: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Date when terms were accepted (ISO format)")
    newsletter_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="User consent to receive newsletters and updates")
    newsletter_consent_date: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Date when newsletter consent was given (ISO format)")

    reset_token: Mapped[str | None] = mapped_column(String(255), index=True)
    reset_token_expires: Mapped[str | None] = mapped_column(String(255))
    
    # Security fields
    last_login_at: Mapped[str | None] = mapped_column(String(255))
    login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[str | None] = mapped_column(String(255))

    organization_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        index=True,
    )

    settings: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    @declared_attr
    def organization(cls):
        return relationship("BaseOrganization", back_populates="users", foreign_keys=[cls.organization_id])

    @declared_attr
    def roles(cls):
        return relationship("BaseRole", secondary=user_role_table, back_populates="users", lazy="selectin")


__all__ = ["BaseUser"]

