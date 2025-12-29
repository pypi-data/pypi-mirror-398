"""
Metadata Store Client Service

Connects to various databases and manages storage/retrieval
of decomposed metadata (schemas, governance rules, ownership, etc.).

Available implementations:
- InMemoryMetadataStore: In-memory store for testing/development
- MongoDBMetadataStore: MongoDB implementation
- PostgresMetadataStore: PostgreSQL implementation
- SQLiteMetadataStore: SQLite implementation
- RedisMetadataStore: Redis implementation
"""

from pycharter.metadata_store.client import MetadataStoreClient

# Import implementations (with optional dependencies)
try:
    from pycharter.metadata_store.in_memory import InMemoryMetadataStore
except ImportError:
    InMemoryMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store.mongodb import MongoDBMetadataStore
except ImportError:
    MongoDBMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store.postgres import PostgresMetadataStore
except ImportError:
    PostgresMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store.sqlite import SQLiteMetadataStore
except ImportError:
    SQLiteMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store.redis import RedisMetadataStore
except ImportError:
    RedisMetadataStore = None  # type: ignore[assignment,misc]

__all__ = [
    "MetadataStoreClient",
    "InMemoryMetadataStore",
    "MongoDBMetadataStore",
    "PostgresMetadataStore",
    "SQLiteMetadataStore",
    "RedisMetadataStore",
]
