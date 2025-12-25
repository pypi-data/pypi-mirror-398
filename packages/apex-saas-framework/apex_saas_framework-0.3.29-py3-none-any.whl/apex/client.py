"""
Apex Client - Clerk-style SDK client for managing database connections and resources.
"""

from typing import Optional, Type, Any, List, Union, TYPE_CHECKING
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, Engine

from apex.core.config import get_settings

# Avoid circular imports
if TYPE_CHECKING:
    from apex.resources.auth import Auth
    from apex.resources.users import Users
    from apex.resources.organizations import Organizations


def _is_async_url(url: str) -> bool:
    """
    Check if database URL is async or sync.
    
    Args:
        url: Database URL
        
    Returns:
        True if async, False if sync
    """
    url_lower = url.lower()
    # Check for async drivers
    async_drivers = ["+asyncpg", "+aiomysql", "+aiosqlite"]
    sync_drivers = ["+psycopg2", "+psycopg", "+pymysql", "+mysqlconnector"]
    
    # If URL has explicit driver, check it
    for driver in async_drivers:
        if driver in url_lower:
            return True
    for driver in sync_drivers:
        if driver in url_lower:
            return False
    
    # If no driver specified, check settings
    settings = get_settings()
    return settings.DB_ASYNC_MODE


class Client:
    """
    Apex Client - Main entry point for the SDK.
    
    Usage:
        client = Client(
            database_url="sqlite+aiosqlite:///./mydb.db",
            user_model=User,
            organization_model=Organization  # optional
            # secret_key is optional - auto-generated if not provided
        )
        
        async with client:
            await client.init_database(models=[User, Organization])
            user = await client.users.create(email="...", password="...")
    """
    
    def __init__(
        self,
        database_url: str,
        user_model: Optional[Type[Any]] = None,
        organization_model: Optional[Type[Any]] = None,
        secret_key: Optional[str] = None,
        async_mode: Optional[bool] = None,
    ):
        """
        Initialize Apex Client.
        
        Args:
            database_url: Database connection URL (any SQLAlchemy-compatible database)
            user_model: User model class (your SQLAlchemy model)
            organization_model: Organization model class (optional)
            secret_key: Secret key for JWT authentication (optional - auto-generated if not provided)
            async_mode: Force async (True) or sync (False) mode. If None, auto-detects from URL or uses settings.
        """
        self.database_url = database_url
        self.user_model = user_model
        self.organization_model = organization_model
        
        # Determine if async or sync mode
        if async_mode is None:
            self.is_async = _is_async_url(database_url)
        else:
            self.is_async = async_mode
        
        # Get secret key from parameter, settings, or auto-generate
        if secret_key:
            self.secret_key = secret_key
        else:
            settings = get_settings()
            # Check if SECRET_KEY is set and not the default placeholder
            if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY and settings.SECRET_KEY != "change-this-secret-key-in-production":
                self.secret_key = settings.SECRET_KEY
            else:
                # Auto-generate a secret key (only used for JWT auth if needed)
                import secrets
                self.secret_key = secrets.token_urlsafe(32)
        
        # Create engine (async or sync) with proper connection pooling
        if self.is_async:
            self.engine: Union[AsyncEngine, Engine] = create_async_engine(
                self.database_url,
                echo=False,
                future=True,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
            )
            # Create async session factory
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            self.sync_session_maker = None
        else:
            self.engine: Union[AsyncEngine, Engine] = create_engine(
                self.database_url,
                echo=False,
                future=True,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            # Create sync session factory
            self.sync_session_maker = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
            self.async_session_maker = None
        
        # Initialize resources (lazy import to avoid circular dependency)
        from apex.resources.auth import Auth
        from apex.resources.users import Users
        from apex.resources.organizations import Organizations
        from apex.resources.roles import Roles
        from apex.resources.permissions import Permissions
        from apex.resources.settings import Settings
        from apex.resources.payments import Payments
        from apex.resources.email import Email
        from apex.resources.files import Files
        from apex.resources.modules import Modules
        
        self.auth = Auth(client=self, user_model=user_model)
        self.users = Users(client=self, user_model=user_model)
        self.organizations = Organizations(
            client=self,
            organization_model=organization_model
        ) if organization_model else None
        self.roles = Roles(client=self)
        self.permissions = Permissions(client=self)
        self.settings = Settings(client=self, user_model=user_model, organization_model=organization_model)
        self.payments = Payments(client=self)
        self.email = Email(client=self)
        self.files = Files(client=self)
        self.modules = Modules(client=self)
    
    @asynccontextmanager
    async def get_session(self):
        """
        Get a database session (async or sync based on mode).
        
        Usage (async):
            async with client.get_session() as session:
                # Use session
                pass
        
        Usage (sync):
            with client.get_session() as session:
                # Use session
                pass
        """
        if self.is_async:
            async with self.async_session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        else:
            # For sync mode, we need to use a regular context manager
            # But this is an async method, so we'll raise an error
            raise RuntimeError("Use get_sync_session() for sync mode instead of get_session()")
    
    @contextmanager
    def get_sync_session(self):
        """
        Get a synchronous database session.
        
        Usage:
            with client.get_sync_session() as session:
                # Use session
                pass
        """
        if not self.is_async:
            session = self.sync_session_maker()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        else:
            raise RuntimeError("Use get_session() for async mode instead of get_sync_session()")
    
    async def init_database(self, models: Optional[List[Type[Any]]] = None) -> None:
        """
        Initialize database tables for the provided models (async mode only).
        
        This is a convenience method for development/quick starts.
        For production, use Alembic migrations instead.
        
        Args:
            models: List of SQLAlchemy model classes to create tables for.
                   If None, uses the client's registered models.
        
        Example:
            await client.init_database(models=[User, Organization])
        """
        if not self.is_async:
            raise RuntimeError("init_database() is async-only. Use init_database_sync() for sync mode.")
        
        from apex.core.base import Base
        from apex.models.registry import validate_models, get_registry
        
        if models is None:
            models = []
            if self.user_model:
                models.append(self.user_model)
            if self.organization_model:
                models.append(self.organization_model)
            
            # Also check registry
            registered = get_registry().get_all_models()
            for model in registered:
                if model not in models:
                    models.append(model)
        
        # Validate no conflicts before creating
        try:
            validate_models()
        except ValueError as e:
            import warnings
            warnings.warn(f"Model validation warning: {e}")
        
        # Create all tables (checkfirst=True means it won't fail if tables already exist)
        async with self.engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True))
        
        # Grant PostgreSQL schema privileges after table creation
        try:
            from apex.infrastructure.database.auto_migrate import grant_schema_privileges
            await grant_schema_privileges(self.engine)
        except Exception as e:
            # Log but don't fail - privileges might already be set
            import warnings
            warnings.warn(f"Could not grant schema privileges: {e}")
    
    def init_database_sync(self, models: Optional[List[Type[Any]]] = None) -> None:
        """
        Initialize database tables for the provided models (sync mode only).
        
        This is a convenience method for development/quick starts.
        For production, use Alembic migrations instead.
        
        Args:
            models: List of SQLAlchemy model classes to create tables for.
                   If None, uses the client's registered models.
        
        Example:
            client.init_database_sync(models=[User, Organization])
        """
        if self.is_async:
            raise RuntimeError("init_database_sync() is sync-only. Use init_database() for async mode.")
        
        from apex.core.base import Base
        from apex.models.registry import validate_models, get_registry
        
        if models is None:
            models = []
            if self.user_model:
                models.append(self.user_model)
            if self.organization_model:
                models.append(self.organization_model)
            
            # Also check registry
            registered = get_registry().get_all_models()
            for model in registered:
                if model not in models:
                    models.append(model)
        
        # Validate no conflicts before creating
        try:
            validate_models()
        except ValueError as e:
            import warnings
            warnings.warn(f"Model validation warning: {e}")
        
        # Create all tables (checkfirst=True means it won't fail if tables already exist)
        Base.metadata.create_all(self.engine, checkfirst=True)
        
        # Grant PostgreSQL schema privileges after table creation (sync version)
        # Note: grant_schema_privileges requires async engine, so skip for sync mode
        # Users can grant privileges manually or use async mode for migrations
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.is_async:
            raise RuntimeError("Cannot use async context manager with sync mode. Use regular context manager or set async_mode=True.")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - dispose engine."""
        if self.is_async:
            await self.engine.dispose()
    
    def __enter__(self):
        """Sync context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit - dispose engine."""
        if not self.is_async:
            self.engine.dispose()
