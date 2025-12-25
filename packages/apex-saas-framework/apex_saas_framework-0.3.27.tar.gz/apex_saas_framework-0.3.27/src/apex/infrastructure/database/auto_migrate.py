"""
Automatic schema migration utilities.

This module provides automatic detection and migration of schema changes
without requiring manual SQL scripts or Alembic migrations.
"""

import logging
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

logger = logging.getLogger(__name__)


async def check_column_exists(
    engine: AsyncEngine,
    table_name: str,
    column_name: str,
) -> bool:
    """
    Check if a column exists in a table.
    
    Args:
        engine: SQLAlchemy async engine
        table_name: Name of the table
        column_name: Name of the column
        
    Returns:
        True if column exists, False otherwise
    """
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                )
            """),
            {"table_name": table_name, "column_name": column_name}
        )
        exists = result.scalar()
        return bool(exists)


async def add_column_if_not_exists(
    engine: AsyncEngine,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> bool:
    """
    Add a column to a table if it doesn't exist.
    
    Args:
        engine: SQLAlchemy async engine
        table_name: Name of the table
        column_name: Name of the column
        column_definition: SQL column definition (e.g., "VARCHAR(100)")
        
    Returns:
        True if column was added, False if it already existed
    """
    exists = await check_column_exists(engine, table_name, column_name)
    
    if not exists:
        logger.info(f"Adding column {column_name} to table {table_name}")
        async with engine.begin() as conn:
            await conn.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            )
        logger.info(f"Successfully added column {column_name} to {table_name}")
        return True
    else:
        logger.debug(f"Column {column_name} already exists in {table_name}")
        return False


async def create_index_if_not_exists(
    engine: AsyncEngine,
    index_name: str,
    table_name: str,
    column_name: str,
    unique: bool = False,
) -> bool:
    """
    Create an index if it doesn't exist.
    
    Args:
        engine: SQLAlchemy async engine
        index_name: Name of the index
        table_name: Name of the table
        column_name: Name of the column to index
        unique: Whether the index should be unique
        
    Returns:
        True if index was created, False if it already existed
    """
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_indexes 
                    WHERE tablename = :table_name 
                    AND indexname = :index_name
                )
            """),
            {"table_name": table_name, "index_name": index_name}
        )
        exists = result.scalar()
        
        if not exists:
            logger.info(f"Creating index {index_name} on {table_name}({column_name})")
            unique_clause = "UNIQUE" if unique else ""
            async with engine.begin() as conn:
                await conn.execute(
                    text(f"CREATE {unique_clause} INDEX {index_name} ON {table_name}({column_name})")
                )
            logger.info(f"Successfully created index {index_name}")
            return True
        else:
            logger.debug(f"Index {index_name} already exists")
            return False


async def grant_schema_privileges(engine: AsyncEngine, schema_name: str = "public") -> None:
    """
    Grant necessary privileges on schema to the database user.
    
    This ensures the application user can create tables, indexes, and perform migrations.
    Required for PostgreSQL databases where the user may not have default privileges.
    
    Args:
        engine: SQLAlchemy async engine
        schema_name: Schema name (default: 'public')
    """
    try:
        # Check if this is PostgreSQL
        dialect_name = engine.dialect.name
        if dialect_name != 'postgresql':
            logger.debug(f"Skipping schema privileges grant (not PostgreSQL, dialect: {dialect_name})")
            return
        
        # Get the database user from the connection URL
        from apex.core.config import get_settings
        settings = get_settings()
        db_url = str(settings.DATABASE_URL)
        
        # Parse the URL to extract username
        # Handle both postgresql:// and postgresql+asyncpg:// formats
        clean_url = db_url.replace('+asyncpg', '').replace('+psycopg2', '')
        parsed = urlparse(clean_url)
        
        if not parsed.username:
            logger.warning("Could not extract username from DATABASE_URL, skipping privilege grants")
            return
        
        username = parsed.username
        
        logger.info(f"Granting schema privileges to user '{username}' on schema '{schema_name}'")
        
        async with engine.begin() as conn:
            try:
                # Grant usage on schema
                await conn.execute(
                    text(f'GRANT USAGE ON SCHEMA "{schema_name}" TO "{username}"')
                )
                
                # Grant all privileges on all existing tables in schema
                await conn.execute(
                    text(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "{schema_name}" TO "{username}"')
                )
                
                # Grant all privileges on all existing sequences in schema
                await conn.execute(
                    text(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "{schema_name}" TO "{username}"')
                )
                
                # Set default privileges for future tables
                await conn.execute(
                    text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON TABLES TO "{username}"')
                )
                
                # Set default privileges for future sequences
                await conn.execute(
                    text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON SEQUENCES TO "{username}"')
                )
                
                logger.info(f"Successfully granted schema privileges to {username} on schema {schema_name}")
                
            except Exception as e:
                # Check if it's a permission error (user might not have grant privileges)
                error_msg = str(e).lower()
                if 'permission denied' in error_msg or 'must be owner' in error_msg:
                    logger.warning(
                        f"Could not grant schema privileges (user '{username}' may not have GRANT privileges). "
                        f"This is normal if the user is not a superuser. Error: {str(e)}"
                    )
                else:
                    logger.warning(f"Error granting schema privileges: {str(e)}")
                    # Don't raise - this is not critical if user already has privileges
                    
    except Exception as e:
        logger.warning(f"Could not grant schema privileges (this may be expected): {str(e)}")
        # Don't raise - this is not critical for non-PostgreSQL databases or if user already has privileges


async def auto_migrate_users_table(engine: AsyncEngine) -> None:
    """
    Automatically migrate the users table to include new columns.
    
    This function adds:
    - username column (VARCHAR(100), unique, indexed)
    - country_code column (VARCHAR(10))
    - deleted_at column (TIMESTAMP WITH TIME ZONE) for soft deletion
    - last_login_at, login_attempts, locked_until (security fields)
    
    Args:
        engine: SQLAlchemy async engine
    """
    logger.info("Starting automatic migration for users table")
    
    # Check if users table exists
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """)
        )
        table_exists = result.scalar()
        
        if not table_exists:
            logger.info("Users table does not exist yet, skipping migration")
            return
    
    # Add deleted_at column (for soft deletion)
    await add_column_if_not_exists(
        engine,
        "users",
        "deleted_at",
        "TIMESTAMP WITH TIME ZONE"
    )
    
    # Add username column
    username_added = await add_column_if_not_exists(
        engine,
        "users",
        "username",
        "VARCHAR(100)"
    )
    
    # Create unique index for username if column was added or index doesn't exist
    if username_added:
        await create_index_if_not_exists(
            engine,
            "ix_users_username",
            "users",
            "username",
            unique=True
        )
    
    # Add country_code column
    await add_column_if_not_exists(
        engine,
        "users",
        "country_code",
        "VARCHAR(10)"
    )
    
    # Add security fields
    await add_column_if_not_exists(
        engine,
        "users",
        "last_login_at",
        "VARCHAR(255)"
    )
    
    await add_column_if_not_exists(
        engine,
        "users",
        "login_attempts",
        "INTEGER DEFAULT 0"
    )
    
    await add_column_if_not_exists(
        engine,
        "users",
        "locked_until",
        "VARCHAR(255)"
    )
    
    # Add is_org_admin column (for organization admin privileges)
    await add_column_if_not_exists(
        engine,
        "users",
        "is_org_admin",
        "BOOLEAN DEFAULT FALSE NOT NULL"
    )
    
    # Add consent columns (GDPR compliance)
    await add_column_if_not_exists(
        engine,
        "users",
        "accept_terms",
        "BOOLEAN DEFAULT FALSE NOT NULL"
    )
    
    await add_column_if_not_exists(
        engine,
        "users",
        "accept_terms_date",
        "VARCHAR(255)"
    )
    
    await add_column_if_not_exists(
        engine,
        "users",
        "newsletter_consent",
        "BOOLEAN DEFAULT FALSE NOT NULL"
    )
    
    await add_column_if_not_exists(
        engine,
        "users",
        "newsletter_consent_date",
        "VARCHAR(255)"
    )
    
    logger.info("Automatic migration for users table completed")


async def add_deleted_at_to_table(engine: AsyncEngine, table_name: str) -> None:
    """
    Add deleted_at column to any table for soft deletion support.
    
    Args:
        engine: SQLAlchemy async engine
        table_name: Name of the table to add deleted_at column to
    """
    # Check if table exists
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = :table_name
                )
            """),
            {"table_name": table_name}
        )
        table_exists = result.scalar()
        
        if not table_exists:
            return
    
    # Add deleted_at column
    await add_column_if_not_exists(
        engine,
        table_name,
        "deleted_at",
        "TIMESTAMP WITH TIME ZONE"
    )


async def auto_migrate_permissions_table(engine: AsyncEngine) -> None:
    """Add module and group fields to permissions table."""
    # Check if table exists
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'permissions')")
        )
        if not result.scalar():
            return
    
    await add_column_if_not_exists(engine, "permissions", "module", "VARCHAR(50)")
    await add_column_if_not_exists(engine, "permissions", "permission_group", "VARCHAR(50)")


async def auto_migrate_payments_table(engine: AsyncEngine) -> None:
    """Add status, payment_method, user_id, and organization_id to payments table."""
    # Check if table exists
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments')")
        )
        if not result.scalar():
            return
    
    await add_column_if_not_exists(engine, "payments", "status", "VARCHAR(50) DEFAULT 'created'")
    await add_column_if_not_exists(engine, "payments", "payment_method", "VARCHAR(50) DEFAULT 'paypal'")
    await add_column_if_not_exists(engine, "payments", "user_id", "UUID")
    await add_column_if_not_exists(engine, "payments", "organization_id", "UUID")


async def auto_migrate_schema(engine: AsyncEngine) -> None:
    """
    Automatically migrate all tables to match current model definitions.
    
    This is the main entry point for automatic migrations.
    
    Args:
        engine: SQLAlchemy async engine
    """
    try:
        logger.info("Starting automatic schema migration")
        
        # Grant schema privileges for PostgreSQL (before any operations)
        await grant_schema_privileges(engine)
        
        # Add deleted_at to all base tables (for soft deletion)
        tables_with_timestamps = [
            "users",
            "organizations",
            "organization_locations",
            "roles",
            "permissions",
            "payments",
            "organization_settings",
        ]
        
        for table in tables_with_timestamps:
            await add_deleted_at_to_table(engine, table)
        
        # Migrate users table (username, country_code, security fields)
        await auto_migrate_users_table(engine)
        
        # Migrate permissions table (module, group)
        await auto_migrate_permissions_table(engine)
        
        # Migrate payments table (status, payment_method, user_id, org_id)
        await auto_migrate_payments_table(engine)
        
        logger.info("Automatic schema migration completed successfully")
    except Exception as e:
        logger.error(f"Error during automatic migration: {str(e)}")
        raise


__all__ = [
    "check_column_exists",
    "add_column_if_not_exists",
    "create_index_if_not_exists",
    "grant_schema_privileges",
    "auto_migrate_users_table",
    "add_deleted_at_to_table",
    "auto_migrate_permissions_table",
    "auto_migrate_payments_table",
    "auto_migrate_schema",
]

