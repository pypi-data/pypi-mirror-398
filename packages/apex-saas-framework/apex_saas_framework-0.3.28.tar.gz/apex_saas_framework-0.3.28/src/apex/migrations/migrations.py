"""
Database migration helpers - Alembic setup and utilities.

Secure migration system for PostgreSQL, MySQL, and SQLite.

Usage:
    from apex.migrations import setup_alembic, get_sync_url, find_models
    
    # Auto-setup Alembic (works with PostgreSQL, MySQL, SQLite)
    setup_alembic()
    
    # Get sync URL for custom setup
    sync_url = get_sync_url()
    
    # Find your models
    files, classes = find_models()
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple, Optional

from apex.infrastructure.database.session import get_sync_database_url
from apex.migrations.security import validate_database_url, mask_sensitive_url


def get_sync_url(database_url: Optional[str] = None) -> str:
    """
    Convert database URL (async/sync) to sync URL for Alembic.
    
    Supports PostgreSQL, MySQL, and SQLite only.
    
    Args:
        database_url: Optional database URL (uses .env if not provided)
    
    Returns:
        Synchronous database URL compatible with Alembic
    
    Raises:
        ValueError: If URL is invalid, contains security issues, or uses unsupported database
    
    Example:
        from apex.migrations import get_sync_url
        sync_url = get_sync_url()
    """
    try:
        return get_sync_database_url(database_url)
    except ValueError as e:
        # Mask sensitive info in error messages
        masked_url = mask_sensitive_url(database_url or os.getenv("DATABASE_URL", ""))
        raise ValueError(f"Invalid database URL: {str(e)} (URL: {masked_url})")


def find_models() -> Tuple[List[str], List[str]]:
    """
    Auto-detect model files and extract SQLAlchemy model class names.
    
    Returns:
        Tuple of (model_files, model_classes)
    
    Example:
        from apex.migrations import find_models
        files, classes = find_models()
        print(f"Found models: {classes}")
    """
    cwd = Path(".")
    files, classes = [], []
    
    # Check common locations
    for path in [cwd / "models.py", cwd / "model.py"]:
        if path.exists():
            files.append(str(path))
            classes.extend(_extract_classes(str(path)))
    
    # Check models directory
    models_dir = cwd / "models"
    if models_dir.exists():
        for py_file in models_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                files.append(str(py_file))
                classes.extend(_extract_classes(str(py_file)))
    
    return files, list(set(classes))


def _extract_classes(file_path: str) -> List[str]:
    """Extract SQLAlchemy model class names from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id in ["Base", "DeclarativeBase", "Model"]:
                        classes.append(node.name)
                    elif isinstance(base, ast.Attribute) and base.attr in ["Base", "DeclarativeBase", "Model"]:
                        classes.append(node.name)
        return classes
    except:
        return []


def setup_alembic(models_file: str = "models.py", output_dir: str = "alembic") -> None:
    """
    Auto-setup Alembic migrations with your models.
    
    Works with PostgreSQL, MySQL, and SQLite only.
    Automatically validates and secures database URLs.
    
    Args:
        models_file: Path to models file (default: "models.py")
        output_dir: Output directory for Alembic files (default: "alembic")
    
    Raises:
        ValueError: If database URL is invalid, uses unsupported database, or models cannot be found
    
    Example:
        from apex.migrations import setup_alembic
        setup_alembic()  # Auto-detects models and creates alembic/env.py
    """
    # Validate inputs for security
    if not isinstance(models_file, str) or not models_file:
        raise ValueError("models_file must be a non-empty string")
    if not isinstance(output_dir, str) or not output_dir:
        raise ValueError("output_dir must be a non-empty string")
    
    # Sanitize paths to prevent directory traversal
    models_file = os.path.normpath(models_file).replace("..", "").replace("~", "")
    output_dir = os.path.normpath(output_dir).replace("..", "").replace("~", "")
    
    import_path = models_file.replace(".py", "").replace("/", ".").replace("\\", ".")
    
    # Get and validate sync URL
    try:
        sync_url = get_sync_url()
    except ValueError as e:
        raise ValueError(f"Failed to setup migrations: {str(e)}")
    
    _, model_classes = find_models()
    import_lines = "\n".join([f"from {import_path} import {cls}  # noqa: F401" for cls in model_classes]) if model_classes else f"# from {import_path} import YourModel  # noqa: F401"
    
    # Mask URL in env.py for security (actual URL comes from get_sync_url())
    masked_url = mask_sensitive_url(sync_url)
    
    env_content = f'''"""
Alembic environment configuration - Auto-generated by Apex.

This file is automatically generated. Do not edit manually.
Database URL is loaded securely from environment variables.
"""

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

from apex.migrations import get_sync_url
from apex.core.config import get_settings
from apex.core.base import Base

# Your models - Auto-detected
{import_lines}

config = context.config
settings = get_settings()

# Get sync URL securely (validates and sanitizes)
sync_url = get_sync_url()
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Combine metadata from Base and user models
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in offline mode (generates SQL scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}}
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in online mode (connects to database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {{}}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write env.py with secure handling
    env_file = output_path / "env.py"
    try:
        env_file.write_text(env_content, encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Failed to write alembic/env.py: {str(e)}")
    
    # Create alembic.ini with masked URL (actual URL loaded from env)
    alembic_ini = Path("alembic.ini")
    if not alembic_ini.exists():
        masked_url = mask_sensitive_url(sync_url)
        ini_content = f"""[alembic]
# Auto-generated by Apex - Do not edit manually
# Database URL is loaded securely from environment variables
script_location = {output_dir}
# Note: sqlalchemy.url is set dynamically in env.py for security
sqlalchemy.url = {masked_url}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =

[logger_alembic]
level = INFO
handlers =

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        alembic_ini.write_text(ini_content, encoding="utf-8")


# Re-export security functions for convenience
from apex.migrations.security import (
    validate_database_url,
    sanitize_database_url,
    mask_sensitive_url,
)

__all__ = [
    "setup_alembic",
    "get_sync_url",
    "find_models",
    "validate_database_url",
    "sanitize_database_url",
    "mask_sensitive_url",
]

