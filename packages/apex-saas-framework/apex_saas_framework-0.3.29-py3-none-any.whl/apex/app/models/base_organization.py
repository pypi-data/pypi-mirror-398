"""
Base organization model definitions.
"""
from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from apex.app.database.base import BaseModel


class BaseOrganization(BaseModel):
    """Abstract organization entity."""

    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    domain: Mapped[str | None] = mapped_column(String(255), unique=True)
    organization_type: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    modules: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    @declared_attr
    def users(cls):
        return relationship("BaseUser", back_populates="organization", lazy="selectin")

    @declared_attr
    def locations(cls):
        return relationship("BaseOrganizationLocation", back_populates="organization", lazy="selectin")

    @declared_attr
    def settings(cls):
        return relationship("BaseOrganizationSettings", back_populates="organization", lazy="selectin", uselist=False)


__all__ = ["BaseOrganization"]

