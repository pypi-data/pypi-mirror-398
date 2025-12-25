"""
Base organization location entity.
"""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from apex.app.database.base import BaseModel


class BaseOrganizationLocation(BaseModel):
    """Abstract organization location."""

    __abstract__ = True

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))

    @declared_attr
    def organization(cls):
        return relationship("BaseOrganization", back_populates="locations")


__all__ = ["BaseOrganizationLocation"]

