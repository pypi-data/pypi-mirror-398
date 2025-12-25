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
    Auto-converts to async format if DB_ASYNC_MODE is True and URL doesn't specify driver.
    If DB_ASYNC_MODE is False or URL already has a driver, returns URL as-is.
    """
    url = str(settings.DATABASE_URL)
    
    # If sync mode is enabled, don't auto-convert
    if not settings.DB_ASYNC_MODE:
        return url
    
    # Check if URL already has a driver specified (sync or async)
    # If it has a driver, don't auto-convert
    if "+" in url:
        return url
    
    # Auto-convert common database URLs to async format if needed
    # Only if no driver is specified and async mode is enabled
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+aiomysql://", 1)
    if url.startswith("sqlite:///") and "+" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("sqlite://") and not url.startswith("sqlite:///"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


# Lazy engine creation - only create when needed
_engine = None
_AsyncSessionLocal = None
_SyncSessionLocal = None

def _get_engine():
    """Get or create engine (async or sync based on DB_ASYNC_MODE)"""
    global _engine
    if _engine is None:
        if settings.DB_ASYNC_MODE:
            _engine = create_async_engine(
                get_database_url(),
                echo=settings.DB_ECHO,
                poolclass=NullPool,
                future=True,
            )
        else:
            from sqlalchemy import create_engine
            _engine = create_engine(
                get_database_url(),
                echo=settings.DB_ECHO,
                future=True,
            )
    return _engine

def _get_async_session_local():
    """Get or create async session factory (lazy initialization)"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        if not settings.DB_ASYNC_MODE:
            raise RuntimeError("Cannot create async session when DB_ASYNC_MODE is False")
        _AsyncSessionLocal = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal

def _get_sync_session_local():
    """Get or create sync session factory (lazy initialization)"""
    global _SyncSessionLocal
    if _SyncSessionLocal is None:
        if settings.DB_ASYNC_MODE:
            raise RuntimeError("Cannot create sync session when DB_ASYNC_MODE is True")
        _SyncSessionLocal = sessionmaker(
            bind=_get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _SyncSessionLocal

# For backward compatibility - use properties
class _EngineProxy:
    def __getattr__(self, name):
        return getattr(_get_engine(), name)

class _AsyncSessionLocalProxy:
    def __call__(self, *args, **kwargs):
        return _get_async_session_local()(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(_get_async_session_local(), name)

class _SyncSessionLocalProxy:
    def __call__(self, *args, **kwargs):
        return _get_sync_session_local()(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(_get_sync_session_local(), name)

engine = _EngineProxy()
AsyncSessionLocal = _AsyncSessionLocalProxy() if settings.DB_ASYNC_MODE else None
SyncSessionLocal = _SyncSessionLocalProxy() if not settings.DB_ASYNC_MODE else None


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

