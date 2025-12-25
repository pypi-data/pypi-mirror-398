"""
Organization settings entity.
"""
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from apex.app.database.base import BaseModel


class BaseOrganizationSettings(BaseModel):
    """Abstract org settings."""

    __abstract__ = True

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), unique=True)
    preferences: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    @declared_attr
    def organization(cls):
        return relationship("BaseOrganization", back_populates="settings")


__all__ = ["BaseOrganizationSettings"]

