"""Base database setup and session management."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class TimestampMixin:
    """Mixin for created_at, updated_at and soft-deletion timestamp."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Abstract base model with UUID, timestamps, and flexible meta storage."""

    __abstract__ = True
    
    # Note: Cannot use 'metadata' as field name - it's reserved by SQLAlchemy
    # Using 'meta' instead for flexible JSON storage
    meta: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

