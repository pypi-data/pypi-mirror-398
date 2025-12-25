"""
Flexible base classes - Users can use these OR define their own completely.

These are optional helpers. Users can:
1. Use these base classes and extend them
2. Define their own models completely from scratch
3. Mix and match - use some, ignore others
"""
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models - use this or your own."""
    pass


class TimestampMixin:
    """
    Optional mixin for timestamps.
    Users can use this OR define their own timestamp fields.
    
    Note: Uses timezone-aware timestamps for PostgreSQL, timezone-naive for MySQL/SQLite.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # PostgreSQL supports timezone, MySQL/SQLite will ignore it
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # PostgreSQL supports timezone, MySQL/SQLite will ignore it
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),  # PostgreSQL supports timezone, MySQL/SQLite will ignore it
        nullable=True,
        default=None,
    )


class IntegerPKMixin:
    """Optional mixin for Integer primary key - use if you want integer IDs."""
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )


class StringPKMixin:
    """Optional mixin for String primary key - use if you want string IDs."""
    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        nullable=False,
    )


# UUID primary key mixin - database-agnostic
# Uses PostgreSQL native UUID when available, falls back to CHAR(36) for MySQL/SQLite
from uuid import uuid4

try:
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    
    class UUIDPKMixin:
        """
        Optional mixin for UUID primary key.
        
        Works with:
        - PostgreSQL: Uses native UUID type
        - MySQL/SQLite: Automatically uses CHAR(36) (SQLAlchemy handles conversion)
        
        Note: For MySQL, you can also use StringPKMixin if you prefer explicit string IDs.
        """
        id: Mapped[PostgresUUID] = mapped_column(
            PostgresUUID(as_uuid=True),
            primary_key=True,
            default=uuid4,
            nullable=False,
        )
except ImportError:
    # If PostgreSQL types not available, use CHAR(36) for MySQL/SQLite
    class UUIDPKMixin:
        """
        Optional mixin for UUID primary key - stored as CHAR(36) string.
        
        Use this for MySQL or SQLite databases.
        """
        id: Mapped[str] = mapped_column(
            String(36),
            primary_key=True,
            default=lambda: str(uuid4()),
            nullable=False,
        )


# MySQL-specific UUID mixin (always uses CHAR(36))
class MySQLUUIDMixin:
    """
    MySQL-specific UUID mixin - always uses CHAR(36) regardless of PostgreSQL availability.
    
    Use this if you want explicit string UUIDs for MySQL compatibility.
    """
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False,
    )


# For JSON/JSONB - database-agnostic
try:
    from sqlalchemy.dialects.postgresql import JSONB
    JSONType = JSONB  # Use JSONB for PostgreSQL
except ImportError:
    try:
        from sqlalchemy import JSON
        JSONType = JSON  # Use JSON for other databases
    except ImportError:
        from sqlalchemy import Text
        JSONType = Text  # Fallback to Text


class FlexibleBaseModel(Base, TimestampMixin):
    """
    Flexible base model - optional helper.
    
    Users can:
    1. Use this and add their own primary key
    2. Extend this and override primary key
    3. Ignore this and define their own model completely
    
    Example 1 - Use with Integer PK:
        class User(FlexibleBaseModel, IntegerPKMixin):
            __tablename__ = "users"
            email = Column(String(255))
    
    Example 2 - Use with String PK:
        class User(FlexibleBaseModel, StringPKMixin):
            __tablename__ = "users"
            email = Column(String(255))
    
    Example 3 - Define your own completely:
        class User(Base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)  # Your choice!
            email = Column(String(255))
    """
    __abstract__ = True
    
    # Optional JSON storage - works with any database
    meta: Mapped[dict[str, Any] | None] = mapped_column(
        JSONType,
        nullable=True,
        default=dict,
    )

