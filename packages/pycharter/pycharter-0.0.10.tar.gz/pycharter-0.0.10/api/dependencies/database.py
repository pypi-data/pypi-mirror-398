"""
Database session dependency for API routes.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from pycharter.config import get_database_url, set_database_url
from pycharter.db.models.base import Base, get_session


def _get_migrations_dir() -> Path:
    """Find migrations directory relative to installed package."""
    try:
        import pycharter
        migrations_dir = Path(pycharter.__file__).parent / "db" / "migrations"
    except (ImportError, AttributeError):
        # Fallback for development
        migrations_dir = Path(__file__).resolve().parent.parent.parent / "pycharter" / "db" / "migrations"
    
    if not migrations_dir.exists():
        cwd_migrations = Path(os.getcwd()) / "pycharter" / "db" / "migrations"
        if cwd_migrations.exists():
            return cwd_migrations
        # If migrations dir doesn't exist, return a path anyway (create_all will still work)
        return migrations_dir
    return migrations_dir


def _ensure_sqlite_initialized(db_url: str) -> None:
    """
    Ensure SQLite database is initialized with all tables.
    
    This function checks if the database exists and has tables.
    If not, it automatically initializes the database.
    
    Note: SQLite doesn't support schemas, so we need to create tables
    without schema prefixes. SQLAlchemy handles this automatically when
    using create_all(), but we need to ensure the database is properly initialized.
    """
    if not db_url.startswith("sqlite://"):
        return  # Only auto-initialize SQLite
    
    try:
        # Extract database path
        db_path = db_url[10:] if db_url.startswith("sqlite:///") else db_url
        if db_path == ":memory:":
            return  # Skip auto-init for in-memory databases
        
        # Ensure parent directory exists
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        engine = create_engine(db_url)
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Check if key tables exist (data_contracts is a good indicator)
        # Note: SQLite doesn't use schemas, so table names won't have "pycharter." prefix
        if "data_contracts" not in existing_tables:
            # Database needs initialization
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Auto-initializing SQLite database: {db_url}")
            
            # For SQLite, we need to create tables without schema
            # SQLAlchemy will automatically ignore schema when using create_all() with SQLite
            # But we need to ensure all models are imported first
            from pycharter.db.models import (  # noqa: F401
                CoercionRuleModel,
                DataContractModel,
                DomainModel,
                MetadataRecordModel,
                OwnerModel,
                QualityMetricModel,
                QualityViolationModel,
                SchemaModel,
                SystemModel,
                ValidationRuleModel,
            )
            
            # For SQLite, we need to create tables without schema prefixes
            # SQLAlchemy's create_all() should handle this, but we explicitly
            # set schema=None for SQLite to ensure it works
            # Create a copy of metadata with schema=None for SQLite
            metadata = Base.metadata
            # Temporarily remove schema from all tables for SQLite
            for table in metadata.tables.values():
                if table.schema == "pycharter":
                    table.schema = None
            
            # Create all tables using SQLAlchemy models
            metadata.create_all(engine, tables=None)  # None means all tables
            
            # Run Alembic migrations if available
            try:
                from alembic import command
                from alembic.config import Config
                
                versions_dir = _get_migrations_dir() / "versions"
                if versions_dir.exists() and any(versions_dir.iterdir()):
                    set_database_url(db_url)
                    
                    # Create Alembic config
                    config = Config()
                    config.set_main_option("script_location", str(_get_migrations_dir()))
                    config.set_main_option("prepend_sys_path", ".")
                    config.set_main_option("version_path_separator", "os")
                    config.set_main_option(
                        "file_template",
                        "%%(year)d%%(month).2d%%(day).2d%%(hour).2d%%(minute).2d%%(second).2d_%%(rev)s_%%(slug)s"
                    )
                    config.set_main_option("sqlalchemy.url", db_url)
                    
                    command.upgrade(config, "head")
                    logger.info("✓ SQLite database auto-initialized with migrations")
                else:
                    logger.info("✓ SQLite database auto-initialized with base tables (no migrations found)")
            except ImportError:
                # Alembic not available - that's okay, we have the tables
                logger.info("✓ SQLite database auto-initialized with base tables (Alembic not available)")
            except Exception as e:
                # If migrations fail, at least we have the tables from create_all
                logger.warning(f"Could not run migrations during auto-init: {e}")
                logger.info("✓ SQLite database auto-initialized with base tables")
    except Exception as e:
        # Log but don't fail - let the actual query fail with a clearer error
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not auto-initialize SQLite database: {e}")


def get_db_session() -> Session:
    """
    FastAPI dependency to get database session.
    
    Defaults to SQLite (sqlite:///pycharter.db) if no database URL is configured.
    Automatically initializes SQLite database if it doesn't exist or is uninitialized.
    
    Returns:
        SQLAlchemy session
        
    Raises:
        HTTPException: If database connection fails
    """
    db_url = get_database_url()
    
    # Default to SQLite if no database URL is configured
    if not db_url:
        default_db_path = Path.cwd() / "pycharter.db"
        db_url = f"sqlite:///{default_db_path}"
    
    # Auto-initialize SQLite if needed
    _ensure_sqlite_initialized(db_url)
    
    try:
        session = get_session(db_url)
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to database: {str(e)}",
        )


