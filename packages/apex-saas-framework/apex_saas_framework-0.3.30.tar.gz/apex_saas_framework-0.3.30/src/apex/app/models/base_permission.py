"""
Permission entity backing RBAC.
"""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from apex.app.database.base import BaseModel
from apex.app.models.associations import role_permission_table


class BasePermission(BaseModel):
    """Abstract permission."""

    __abstract__ = True

    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    module: Mapped[str | None] = mapped_column(String(50))  # e.g., "users", "billing", "reports"
    permission_group: Mapped[str | None] = mapped_column(String(50))   # e.g., "read", "write", "admin"

    @declared_attr
    def roles(cls):
        return relationship(
            "BaseRole",
            secondary=role_permission_table,
            back_populates="permissions",
            lazy="selectin",
        )


__all__ = ["BasePermission"]

