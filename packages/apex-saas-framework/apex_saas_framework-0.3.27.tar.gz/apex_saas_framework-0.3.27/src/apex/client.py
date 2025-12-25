"""
Apex Client - Clerk-style SDK client for managing database connections and resources.
"""

from typing import Optional, Type, Any, List, TYPE_CHECKING
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker

from apex.core.config import get_settings

# Avoid circular imports
if TYPE_CHECKING:
    from apex.resources.auth import Auth
    from apex.resources.users import Users
    from apex.resources.organizations import Organizations


def _convert_to_async_url(url: str) -> str:
    """
    Convert sync database URL to async format if needed.
    
    Args:
        url: Database URL (sync or async)
        
    Returns:
        Async database URL
    """
    if "+" in url.split("://")[0]:
        return url
    
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
    ):
        """
        Initialize Apex Client.
        
        Args:
            database_url: Database connection URL (any SQLAlchemy-compatible database)
            user_model: User model class (your SQLAlchemy model)
            organization_model: Organization model class (optional)
            secret_key: Secret key for JWT authentication (optional - auto-generated if not provided)
        """
        # Convert sync URL to async if needed
        self.database_url = _convert_to_async_url(database_url)
        self.user_model = user_model
        self.organization_model = organization_model
        
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
        
        # Create async engine with proper connection pooling
        self.engine: AsyncEngine = create_async_engine(
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
        Get an async database session.
        
        Usage:
            async with client.get_session() as session:
                # Use session
                pass
        """
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def init_database(self, models: Optional[List[Type[Any]]] = None) -> None:
        """
        Initialize database tables for the provided models.
        
        This is a convenience method for development/quick starts.
        For production, use Alembic migrations instead.
        
        Args:
            models: List of SQLAlchemy model classes to create tables for.
                   If None, uses the client's registered models.
        
        Example:
            await client.init_database(models=[User, Organization])
        """
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
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - dispose engine."""
        await self.engine.dispose()
