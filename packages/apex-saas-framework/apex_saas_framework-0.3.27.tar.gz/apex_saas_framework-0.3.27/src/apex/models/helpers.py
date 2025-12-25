"""
Easy model definition helpers - Simple, conflict-free model creation.

Usage:
    from apex.models import define_model, create_tables
    
    # Define a model easily
    User = define_model(
        "User",
        "users",
        {
            "email": Column(String(255), unique=True),
            "password_hash": Column(String(255)),
        }
    )
    
    # Create all tables
    create_tables()
"""

from typing import Dict, Any, Optional, Type
from sqlalchemy import Column
from apex.core.base import Base, UUIDPKMixin, TimestampMixin
from apex.models.registry import register_model, get_registry, validate_models


def define_model(
    class_name: str,
    table_name: Optional[str] = None,
    columns: Optional[Dict[str, Column]] = None,
    base_mixins: Optional[tuple] = None,
    schema: Optional[str] = None,
    **kwargs
) -> Type[Any]:
    """
    Easily define a model with automatic conflict prevention.
    
    Args:
        class_name: Name of the model class
        table_name: Database table name (auto-generated if not provided)
        columns: Dictionary of column_name -> Column definitions (optional)
        base_mixins: Mixins to include (default: UUIDPKMixin, TimestampMixin)
        schema: Optional schema name for namespacing
        **kwargs: Additional class attributes or columns
    
    Returns:
        Model class (already registered)
    
    Example:
        # Simple way
        User = define_model("User", email=Column(String(255)))
        
        # With explicit table name
        User = define_model("User", "users", {"email": Column(String(255))})
        
        # With custom mixins
        User = define_model("User", base_mixins=(ID,), email=Column(String(255)))
    """
    # Auto-generate table name if not provided
    if table_name is None:
        table_name = auto_table_name(class_name)
    
    # Default mixins
    if base_mixins is None:
        base_mixins = (UUIDPKMixin, TimestampMixin)
    
    # Combine columns and kwargs
    if columns is None:
        columns = {}
    
    # Allow columns to be passed as kwargs for convenience
    all_columns = {**columns, **kwargs}
    
    # Build class attributes
    attrs = {
        "__tablename__": table_name,
        **all_columns,
    }
    
    # Create class with Base and mixins
    bases = (Base,) + base_mixins
    model_class = type(class_name, bases, attrs)
    
    # Register to prevent conflicts
    return register_model(model_class, schema=schema)


def create_tables(
    engine: Any = None,
    models: Optional[list] = None,
    checkfirst: bool = True,
    schema: Optional[str] = None
) -> None:
    """
    Create all registered tables without conflicts.
    
    Args:
        engine: SQLAlchemy engine (optional, uses default if not provided)
        models: List of models to create (optional, uses all registered if not provided)
        checkfirst: Check if tables exist before creating (default: True)
        schema: Optional schema name
    
    Example:
        from apex.models import create_tables
        create_tables()  # Creates all registered tables
    """
    from apex.core.base import Base
    
    # Validate no conflicts
    try:
        validate_models()
    except ValueError as e:
        import warnings
        warnings.warn(f"Model validation warning: {e}")
    
    # Get models to create
    if models is None:
        models = get_registry().get_all_models()
    
    if not models:
        raise ValueError("No models registered. Define models first.")
    
    # Create tables
    if engine:
        # Use provided engine
        if hasattr(engine, "begin"):
            # Async engine
            import asyncio
            async def _create():
                async with engine.begin() as conn:
                    await conn.run_sync(
                        lambda sync_conn: Base.metadata.create_all(
                            sync_conn, 
                            checkfirst=checkfirst,
                            schema=schema
                        )
                    )
            asyncio.run(_create())
        else:
            # Sync engine
            if schema:
                Base.metadata.create_all(engine, checkfirst=checkfirst, schema=schema)
            else:
                Base.metadata.create_all(engine, checkfirst=checkfirst)
    else:
        # Use default client
        from apex.sync import _run
        from apex.client import Client
        from apex.core.config import get_settings
        
        settings = get_settings()
        client = Client(database_url=str(settings.DATABASE_URL))
        
        async def _create():
            async with client.engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn: Base.metadata.create_all(
                        sync_conn,
                        checkfirst=checkfirst,
                        schema=schema
                    )
                )
        
        _run(_create())


def auto_table_name(class_name: str, prefix: str = "") -> str:
    """
    Auto-generate table name from class name.
    
    Args:
        class_name: Model class name
        prefix: Optional prefix for table name
    
    Returns:
        Generated table name
    
    Example:
        table_name = auto_table_name("UserProfile")  # Returns "user_profiles"
        table_name = auto_table_name("User", prefix="app_")  # Returns "app_users"
    """
    import re
    
    # Convert CamelCase to snake_case
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
    
    # Add 's' for plural if not already plural
    if not name.endswith('s'):
        name += 's'
    
    if prefix:
        name = f"{prefix}{name}"
    
    return name

