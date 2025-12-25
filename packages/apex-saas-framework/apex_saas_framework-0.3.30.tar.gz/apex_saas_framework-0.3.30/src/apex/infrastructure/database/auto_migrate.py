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


async def migrate_organization_id_to_uuid(engine: AsyncEngine, table_name: str = "roles") -> None:
    """
    Migrate organization_id column from VARCHAR(36) to UUID type.
    
    ONLY migrates if it's clearly a framework-created column:
    - Must be VARCHAR(36) (exact match - framework's previous type)
    - Must reference organizations.id (framework default)
    
    If any condition doesn't match, assumes it's user's custom schema and skips migration.
    This prevents errors for users with existing databases.
    
    Users can override organization_id in their models to match existing schema.
    
    Args:
        engine: SQLAlchemy async engine
        table_name: Name of the table (default: 'roles')
    """
    try:
        # Check if this is PostgreSQL (only supported database for this migration)
        if engine.dialect.name != 'postgresql':
            logger.debug(f"Skipping UUID migration for {table_name} (not PostgreSQL)")
            return
        
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
            if not result.scalar():
                logger.debug(f"Table {table_name} does not exist, skipping migration")
                return
            
            # Check if organization_id column exists and its current type
            result = await conn.execute(
                text("""
                    SELECT data_type, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = 'organization_id'
                """),
                {"table_name": table_name}
            )
            row = result.fetchone()
            
            if not row:
                logger.debug(f"Column organization_id does not exist in {table_name}, skipping migration")
                return
            
            current_type = row[0].lower()
            max_length = row[1]
            
            # Check if it's already UUID - no migration needed
            if current_type == 'uuid':
                logger.debug(f"Column organization_id in {table_name} is already UUID type")
                return
            
            # Only migrate if it's VARCHAR(36) - the exact type framework used before
            # This ensures we only migrate framework-created columns, not user's custom ones
            if current_type in ['character varying', 'varchar'] and max_length == 36:
                # Check if it references organizations.id (framework default)
                # If it references something else, it's user's custom schema - skip migration
                try:
                    result = await conn.execute(
                        text("""
                            SELECT 
                                ccu.table_name AS foreign_table_name,
                                ccu.column_name AS foreign_column_name
                            FROM information_schema.table_constraints AS tc
                            JOIN information_schema.key_column_usage AS kcu
                                ON tc.constraint_name = kcu.constraint_name
                                AND tc.table_schema = kcu.table_schema
                            JOIN information_schema.constraint_column_usage AS ccu
                                ON ccu.constraint_name = tc.constraint_name
                                AND ccu.table_schema = tc.table_schema
                            WHERE tc.constraint_type = 'FOREIGN KEY'
                                AND tc.table_name = :table_name
                                AND kcu.column_name = 'organization_id'
                        """),
                        {"table_name": table_name}
                    )
                    fk_info = result.fetchone()
                    
                    # Only migrate if it references organizations.id (framework default)
                    if fk_info and fk_info[0] == 'organizations' and fk_info[1] == 'id':
                        # This is a framework-created column, safe to migrate
                        logger.info(f"Migrating framework-created organization_id from VARCHAR(36) to UUID in {table_name}")
                        
                        async with engine.begin() as conn:
                            try:
                                # Validate UUIDs before conversion
                                result = await conn.execute(
                                    text(f"""
                                        SELECT COUNT(*) 
                                        FROM {table_name} 
                                        WHERE organization_id IS NOT NULL 
                                        AND organization_id != ''
                                        AND organization_id !~ '^[0-9a-fA-F]{{8}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{12}}$'
                                    """)
                                )
                                invalid_count = result.scalar()
                                
                                if invalid_count > 0:
                                    logger.warning(
                                        f"Found {invalid_count} invalid UUID values in {table_name}.organization_id. "
                                        f"Setting them to NULL before migration."
                                    )
                                    await conn.execute(
                                        text(f"""
                                            UPDATE {table_name} 
                                            SET organization_id = NULL 
                                            WHERE organization_id IS NOT NULL 
                                            AND organization_id != ''
                                            AND organization_id !~ '^[0-9a-fA-F]{{8}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{12}}$'
                                        """)
                                    )
                                
                                # Convert to UUID
                                await conn.execute(
                                    text(f"""
                                        ALTER TABLE {table_name} 
                                        ALTER COLUMN organization_id 
                                        TYPE UUID USING 
                                            CASE 
                                                WHEN organization_id IS NULL OR organization_id = '' THEN NULL::uuid
                                                ELSE organization_id::uuid
                                            END
                                    """)
                                )
                                
                                logger.info(f"Successfully migrated organization_id to UUID in {table_name}")
                            except Exception as e:
                                # If migration fails, log but don't raise - allow app to continue
                                logger.warning(
                                    f"Could not migrate organization_id in {table_name}: {str(e)}. "
                                    f"Override organization_id in your model to match existing schema."
                                )
                                return
                    else:
                        # References different table/column - user's custom schema
                        ref_table = fk_info[0] if fk_info else 'unknown'
                        ref_column = fk_info[1] if fk_info else 'unknown'
                        logger.info(
                            f"organization_id in {table_name} references {ref_table}.{ref_column} - "
                            f"appears to be custom schema. Skipping migration. "
                            f"Override organization_id in your model to match existing schema."
                        )
                        return
                except Exception as e:
                    # If FK check fails, assume it's custom schema and skip
                    logger.debug(f"Could not check foreign key for {table_name}.organization_id: {str(e)}. Skipping migration.")
                    return
            elif current_type in ['character varying', 'varchar', 'char', 'text']:
                # VARCHAR but not length 36 - likely user's custom schema
                logger.info(
                    f"organization_id in {table_name} is {current_type}({max_length}) - "
                    f"appears to be custom schema (not framework's VARCHAR(36)). "
                    f"Skipping migration. Override organization_id in your model to match existing schema."
                )
                return
            else:
                # Different type (INTEGER, etc.) - definitely user's custom schema
                logger.info(
                    f"organization_id in {table_name} is {current_type} - "
                    f"appears to be custom schema. Skipping migration. "
                    f"Override organization_id in your model to match existing schema."
                )
                return
                
    except Exception as e:
        # Never raise - always allow application to continue
        error_msg = str(e).lower()
        if 'invalid input syntax for type uuid' in error_msg:
            logger.warning(
                f"Could not migrate {table_name}.organization_id: Invalid UUID values found. "
                f"Override organization_id in your model to match existing schema."
            )
        elif 'column "organization_id" does not exist' in error_msg:
            logger.debug(f"Column organization_id does not exist in {table_name}, skipping migration")
        else:
            logger.warning(
                f"Error checking organization_id migration for {table_name}: {str(e)}. "
                f"Skipping migration. Override organization_id in your model if needed."
            )
        return


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
        
        # Migrate organization_id from VARCHAR to UUID (breaking change fix for v0.3.27)
        # This handles existing databases that have VARCHAR(36) organization_id
        # Wrapped in try-except to ensure it never causes migration to fail
        try:
            await migrate_organization_id_to_uuid(engine, "roles")
        except Exception as e:
            # Migration function should never raise, but catch just in case
            logger.warning(f"Organization ID migration encountered an issue (non-critical): {str(e)}")
            # Continue with other migrations
        
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
    "migrate_organization_id_to_uuid",
    "auto_migrate_users_table",
    "add_deleted_at_to_table",
    "auto_migrate_permissions_table",
    "auto_migrate_payments_table",
    "auto_migrate_schema",
]

