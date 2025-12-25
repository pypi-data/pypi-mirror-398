"""
Role entity with many-to-many permissions.
"""
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from apex.app.database.base import BaseModel
from apex.app.models.associations import role_permission_table, user_role_table


class BaseRole(BaseModel):
    """Abstract role."""

    __abstract__ = True
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uq_org_role_name'),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)

    @declared_attr
    def users(cls):
        return relationship("BaseUser", secondary=user_role_table, back_populates="roles", lazy="selectin")

    @declared_attr
    def permissions(cls):
        return relationship(
            "BasePermission",
            secondary=role_permission_table,
            back_populates="roles",
            lazy="selectin",
        )


__all__ = ["BaseRole"]

