"""
Flexible model helpers - Users can use these OR define their own completely.

These are optional convenience classes. Users can:
- Use these and extend them
- Define their own models from scratch
- Mix and match as needed
"""
from typing import Optional
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from apex.core.base import FlexibleBaseModel, JSONType

# Try to import UUID for PostgreSQL, fallback to String for others
try:
    from sqlalchemy.dialects.postgresql import UUID
    from uuid import UUID as PyUUID
    UUIDType = UUID(as_uuid=True)
except ImportError:
    UUIDType = String(36)  # Fallback to String for non-PostgreSQL
    PyUUID = str


class FlexibleUser(FlexibleBaseModel):
    """
    Optional flexible user model - use this OR define your own.
    
    This provides common user fields, but you can:
    - Extend and add your own fields
    - Override primary key (add IntegerPKMixin, StringPKMixin, etc.)
    - Define your own foreign keys
    - Ignore this completely and define your own User model
    """
    __abstract__ = True
    
    # Basic fields - use what you need, ignore the rest
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Optional settings - works with any database
    settings: Mapped[dict | None] = mapped_column(JSONType, nullable=True, default=dict)
    
    # NOTE: No foreign keys defined here - YOU define them in your model!
    # Example:
    #   organization_id = Column(Integer, ForeignKey("organizations.id"))  # Your choice!


class FlexibleOrganization(FlexibleBaseModel):
    """
    Optional flexible organization model - use this OR define your own.
    """
    __abstract__ = True
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Optional settings - works with any database
    settings: Mapped[dict | None] = mapped_column(JSONType, nullable=True, default=dict)
    modules: Mapped[dict | None] = mapped_column(JSONType, nullable=True, default=dict)


class FlexibleRole(FlexibleBaseModel):
    """
    Optional flexible role model - use this OR define your own.
    """
    __abstract__ = True
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FlexiblePermission(FlexibleBaseModel):
    """
    Optional flexible permission model - use this OR define your own.
    """
    __abstract__ = True
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resource: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

