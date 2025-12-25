"""
Dependencies for metadata store connections.

This module provides FastAPI dependency injection for metadata store instances.
"""

from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status
from pydantic_settings import BaseSettings

from pathlib import Path

from pycharter.config import get_database_url
from pycharter.metadata_store import (
    InMemoryMetadataStore,
    MetadataStoreClient,
    MongoDBMetadataStore,
    PostgresMetadataStore,
    RedisMetadataStore,
    SQLiteMetadataStore,
)


class StoreSettings(BaseSettings):
    """Settings for metadata store configuration."""
    
    store_type: str = "sqlite"  # Options: sqlite, in_memory, postgres, mongodb, redis
    connection_string: Optional[str] = None
    
    class Config:
        env_prefix = "PYCHARTER_API_"
        case_sensitive = False


@lru_cache()
def get_store_settings() -> StoreSettings:
    """Get store settings from environment variables (cached)."""
    return StoreSettings()


# Global store instance (singleton pattern)
_store_instance: Optional[MetadataStoreClient] = None


def get_metadata_store() -> MetadataStoreClient:
    """
    FastAPI dependency to get metadata store instance.
    
    This function creates and caches a single metadata store instance
    per application lifecycle. The store is reused across requests.
    
    Default behavior:
    - If PYCHARTER_DATABASE_URL is set and is PostgreSQL, uses PostgreSQL
    - If PYCHARTER_DATABASE_URL is set and is SQLite, uses SQLite
    - Otherwise, defaults to SQLite with a local database file
    
    Returns:
        MetadataStoreClient instance
        
    Raises:
        HTTPException: If store cannot be created or connected
    """
    global _store_instance
    
    if _store_instance is None:
        settings = get_store_settings()
        store_type = settings.store_type.lower()
        connection_string = settings.connection_string
        
        # Auto-detect database type from PYCHARTER_DATABASE_URL if available
        db_url = get_database_url()
        if db_url and not connection_string:
            if db_url.startswith(("postgresql://", "postgres://")):
                # Automatically use PostgreSQL if database URL is set
                store_type = "postgres"
                connection_string = db_url
            elif db_url.startswith("sqlite://"):
                # Automatically use SQLite if database URL is set
                store_type = "sqlite"
                connection_string = db_url
        
        try:
            if store_type == "sqlite":
                # Default SQLite database location if not specified
                if not connection_string:
                    # Use a default location in the current directory or user's home
                    default_db_path = Path.cwd() / "pycharter.db"
                    connection_string = f"sqlite:///{default_db_path}"
                _store_instance = SQLiteMetadataStore(connection_string=connection_string)
            elif store_type == "in_memory":
                _store_instance = InMemoryMetadataStore()
            elif store_type == "postgres":
                if not connection_string:
                    # Try to get from database URL if not explicitly set
                    connection_string = connection_string or get_database_url()
                    if not connection_string:
                        raise ValueError("connection_string required for PostgreSQL store")
                _store_instance = PostgresMetadataStore(connection_string=connection_string)
            elif store_type == "mongodb":
                if not connection_string:
                    raise ValueError("connection_string required for MongoDB store")
                _store_instance = MongoDBMetadataStore(connection_string=connection_string)
            elif store_type == "redis":
                if not connection_string:
                    raise ValueError("connection_string required for Redis store")
                _store_instance = RedisMetadataStore(connection_string=connection_string)
            else:
                raise ValueError(f"Unsupported store type: {store_type}")
            
            _store_instance.connect()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize metadata store: {str(e)}",
            )
    
    return _store_instance
