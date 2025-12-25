"""Database session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from apex.core.config import get_settings

settings = get_settings()


def get_database_url() -> str:
    """
    Get database URL - supports PostgreSQL, MySQL, and SQLite.
    
    Supports localhost, 127.0.0.1, and remote hosts.
    Auto-converts to async format if needed.
    """
    url = str(settings.DATABASE_URL)
    # Auto-convert common database URLs to async format if needed
    # Supports localhost, 127.0.0.1, and remote hosts
    if url.startswith("postgresql://") and "+" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://") and "+" not in url:
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("mysql://") and "+" not in url:
        return url.replace("mysql://", "mysql+aiomysql://", 1)
    if url.startswith("sqlite:///") and "+" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("sqlite://") and "+" not in url and not url.startswith("sqlite:///"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


# Lazy engine creation - only create when needed
_engine = None
_AsyncSessionLocal = None

def _get_engine():
    """Get or create async engine (lazy initialization)"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            echo=settings.DB_ECHO,
            poolclass=NullPool,
            future=True,
        )
    return _engine

def _get_async_session_local():
    """Get or create async session factory (lazy initialization)"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal

# For backward compatibility - use properties
class _EngineProxy:
    def __getattr__(self, name):
        return getattr(_get_engine(), name)

class _SessionLocalProxy:
    def __call__(self, *args, **kwargs):
        return _get_async_session_local()(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(_get_async_session_local(), name)

engine = _EngineProxy()
AsyncSessionLocal = _SessionLocalProxy()


# For synchronous operations (migrations, CLI)
def get_sync_database_url(database_url: str = None) -> str:
    """
    Convert database URL (async or sync) to sync URL for Alembic.
    
    Supports PostgreSQL, MySQL, and SQLite only:
    - PostgreSQL: postgresql+asyncpg:// -> postgresql+psycopg2://
    - MySQL: mysql+aiomysql:// -> mysql+pymysql://
    - SQLite: sqlite+aiosqlite:// -> sqlite://
    
    Args:
        database_url: Optional database URL. If not provided, uses settings.DATABASE_URL.
    
    Returns:
        Synchronous database URL compatible with Alembic.
    
    Raises:
        ValueError: If URL is invalid, contains security issues, or uses unsupported database
    """
    from apex.migrations.security import validate_database_url, sanitize_database_url
    
    url = database_url or str(settings.DATABASE_URL)
    
    # Validate and sanitize URL for security
    validate_database_url(url)
    url = sanitize_database_url(url)
    
    url_lower = url.lower()
    
    # PostgreSQL
    if "postgresql" in url_lower or "postgres" in url_lower:
        if "+asyncpg" in url_lower:
            return url.replace("+asyncpg", "+psycopg2", 1)
        elif "+psycopg2" in url_lower or "+psycopg" in url_lower:
            return url  # Already sync
        elif "://" in url and "+" not in url.split("://")[0]:
            # postgresql:// without driver -> add psycopg2
            return url.replace("postgresql://", "postgresql+psycopg2://", 1).replace("postgres://", "postgresql+psycopg2://", 1)
        return url
    
    # MySQL
    if "mysql" in url_lower:
        if "+aiomysql" in url_lower:
            return url.replace("+aiomysql", "+pymysql", 1)
        elif "+pymysql" in url_lower or "+mysqlconnector" in url_lower:
            return url  # Already sync
        elif "://" in url and "+" not in url.split("://")[0]:
            # mysql:// without driver -> add pymysql
            return url.replace("mysql://", "mysql+pymysql://", 1)
        return url
    
    # SQLite
    if "sqlite" in url_lower:
        if "+aiosqlite" in url_lower:
            return url.replace("+aiosqlite", "", 1)
        return url  # sqlite:// is already sync
    
    # Unsupported database
    raise ValueError(
        f"Unsupported database type. Only PostgreSQL, MySQL, and SQLite are supported. "
        f"Detected: {url.split('://')[0] if '://' in url else 'unknown'}"
    )


# Note: For synchronous operations, use create_engine instead
# This is kept for compatibility but users should use async operations
from sqlalchemy import create_engine

sync_engine = create_engine(
    get_sync_database_url(),
    echo=settings.DB_ECHO,
    future=True,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with get_async_session_local()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

