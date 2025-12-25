"""
Quick start helpers - Reduce code writing for users.

Simple, one-line functions for common tasks.
"""

import os
from typing import Optional, List, Type, Any
from pathlib import Path
from dotenv import load_dotenv

from apex.client import Client
from apex.sync import set_default_client, bootstrap
from apex.migrations import setup_alembic, find_models
from apex.models import register_model, create_tables, Model, ID, Timestamps


def quick_setup(
    database_url: Optional[str] = None,
    models_file: str = "models.py",
    auto_create_tables: bool = True,
    setup_migrations: bool = True,
) -> Client:
    """
    One-line setup for everything - client, models, tables, migrations.
    
    Args:
        database_url: Database URL (uses .env if not provided)
        models_file: Path to models file (default: "models.py")
        auto_create_tables: Auto-create tables (default: True)
        setup_migrations: Auto-setup Alembic (default: True)
    
    Returns:
        Configured Client instance
    
    Example:
        from apex.quickstart import quick_setup
        
        client = quick_setup()  # That's it! Everything is ready.
    """
    # Load .env if exists
    if Path(".env").exists():
        load_dotenv()
    
    # Get database URL
    if not database_url:
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./apex.db")
    
    # Find models
    model_files, model_classes = find_models()
    
    # Import user model if found
    user_model = None
    if model_files and model_classes:
        try:
            import_path = models_file.replace(".py", "").replace("/", ".").replace("\\", ".")
            # Try to import first model class
            import importlib
            module = importlib.import_module(import_path)
            if model_classes:
                user_model = getattr(module, model_classes[0], None)
        except Exception:
            pass
    
    # Create client
    client = Client(
        database_url=database_url,
        user_model=user_model,
    )
    set_default_client(client)
    
    # Auto-create tables if requested
    if auto_create_tables:
        try:
            create_tables()
        except Exception:
            pass  # Tables might already exist
    
    # Auto-setup migrations if requested
    if setup_migrations:
        try:
            setup_alembic(models_file=models_file)
        except Exception:
            pass  # Migrations might already be setup
    
    return client


def quick_model(
    class_name: str,
    table_name: Optional[str] = None,
    fields: Optional[dict] = None,
    use_timestamps: bool = True,
    **kwargs
) -> Type[Any]:
    """
    Create a model in one line.
    
    Args:
        class_name: Name of the model class
        table_name: Table name (auto-generated if not provided)
        fields: Dictionary of field_name: Column definitions
        use_timestamps: Add created_at, updated_at (default: True)
        **kwargs: Additional fields as Column definitions
    
    Returns:
        Model class (already registered)
    
    Example:
        from apex.quickstart import quick_model
        from sqlalchemy import Column, String
        
        # Simple way
        User = quick_model("User", email=Column(String(255)), name=Column(String(100)))
        
        # With fields dict
        User = quick_model("User", fields={"email": Column(String(255))})
    """
    from apex.models import define_model, auto_table_name
    
    if table_name is None:
        table_name = auto_table_name(class_name)
    
    if fields is None:
        fields = {}
    
    # Combine fields and kwargs
    all_fields = {**fields, **kwargs}
    
    # Default mixins
    mixins = (ID,)
    if use_timestamps:
        mixins = (ID, Timestamps)
    
    return define_model(class_name, table_name, all_fields, base_mixins=mixins)


def quick_user(
    email_field: str = "email",
    password_field: str = "password_hash",
    **extra_fields
) -> Type[Any]:
    """
    Create a user model in one line with common fields.
    
    Args:
        email_field: Name of email field (default: "email")
        password_field: Name of password field (default: "password_hash")
        **extra_fields: Additional fields as Column definitions
    
    Returns:
        User model class (already registered)
    
    Example:
        from apex.quickstart import quick_user
        from sqlalchemy import Column, String
        
        User = quick_user(
            username=Column(String(100)),
            phone=Column(String(20))
        )
    """
    from sqlalchemy import Column, String, Boolean
    
    fields = {
        email_field: Column(String(255), unique=True, nullable=False),
        password_field: Column(String(255), nullable=False),
        **extra_fields
    }
    
    return quick_model("User", "users", fields, use_timestamps=True)


def auto_setup() -> Client:
    """
    Automatic setup - detects everything and sets up automatically.
    
    Looks for:
    - .env file for DATABASE_URL
    - models.py for models
    - Auto-creates tables
    - Auto-setup migrations
    
    Returns:
        Configured Client instance
    
    Example:
        from apex.quickstart import auto_setup
        
        client = auto_setup()  # Fully automatic!
    """
    return quick_setup(
        auto_create_tables=True,
        setup_migrations=True,
    )


__all__ = [
    "quick_setup",
    "quick_model",
    "quick_user",
    "auto_setup",
]

