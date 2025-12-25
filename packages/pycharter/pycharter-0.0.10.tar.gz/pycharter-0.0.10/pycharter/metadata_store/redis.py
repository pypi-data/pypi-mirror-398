"""
Redis Metadata Store Implementation

Stores metadata in Redis using JSON serialization.
"""

import json
from typing import Any, Dict, List, Optional

try:
    import redis  # type: ignore[import-not-found,import-untyped]

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from pycharter.metadata_store.client import MetadataStoreClient


class RedisMetadataStore(MetadataStoreClient):
    """
    Redis metadata store implementation.

    Stores metadata in Redis with the following key patterns:
    - schemas:{schema_id}: JSON Schema definitions
    - schemas:index: Set of all schema IDs
    - governance:{rule_id}: Governance rules
    - governance:index: Set of all rule IDs
    - ownership:{resource_id}: Ownership information
    - metadata:{resource_type}:{resource_id}: Additional metadata

    Connection string format: redis://[password@]host[:port][/database]

    Example:
        >>> store = RedisMetadataStore("redis://localhost:6379/0")
        >>> store.connect()
        >>> schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        key_prefix: str = "pycharter",
    ):
        """
        Initialize Redis metadata store.

        Args:
            connection_string: Redis connection string
            key_prefix: Prefix for all keys (default: "pycharter")
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis is required for RedisMetadataStore. "
                "Install with: pip install redis"
            )
        super().__init__(connection_string)
        self.key_prefix = key_prefix
        self._client: Optional[redis.Redis] = None

    def connect(self) -> None:
        """Connect to Redis."""
        if not self.connection_string:
            raise ValueError("connection_string is required for Redis")

        self._client = redis.from_url(self.connection_string, decode_responses=True)
        # Test connection
        self._client.ping()
        self._connection = self._client

    def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._connection = None

    def _key(self, *parts: str) -> str:
        """Generate a Redis key with prefix."""
        return f"{self.key_prefix}:{':'.join(parts)}"

    def store_schema(
        self,
        schema_name: str,
        schema: Dict[str, Any],
        version: str,
    ) -> str:
        """
        Store a schema in Redis.

        Args:
            schema_name: Name/identifier for the schema
            schema: JSON Schema dictionary (must contain "version" field or it will be added)
            version: Required version string (must match schema["version"] if present)

        Returns:
            Schema ID

        Raises:
            ValueError: If version is missing or doesn't match schema version
        """
        if not self._client:
            raise RuntimeError("Not connected. Call connect() first.")

        # Ensure schema has version
        if "version" not in schema:
            schema = dict(schema)  # Make a copy
            schema["version"] = version
        elif schema.get("version") != version:
            raise ValueError(
                f"Version mismatch: provided version '{version}' does not match "
                f"schema version '{schema.get('version')}'"
            )

        # Generate schema ID
        schema_id = f"{schema_name}:{version}"

        # Store schema data
        schema_data = {
            "id": schema_id,
            "name": schema_name,
            "version": version,
            "schema": schema,
        }
        self._client.set(self._key("schemas", schema_id), json.dumps(schema_data))

        # Add to index
        self._client.sadd(self._key("schemas", "index"), schema_id)

        return schema_id

    def get_schema(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a schema by ID and optional version.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, returns latest version)

        Returns:
            Schema dictionary with version included, or None if not found

        Raises:
            ValueError: If schema is found but doesn't have a version field
        """
        if not self._client:
            raise RuntimeError("Not connected. Call connect() first.")

        # If version specified, try to get specific version
        if version:
            # Try versioned key first
            versioned_id = (
                f"{schema_id.split(':')[0]}:{version}"
                if ":" not in schema_id
                else f"{schema_id.rsplit(':', 1)[0]}:{version}"
            )
            data = self._client.get(self._key("schemas", versioned_id))
            if data:
                schema_data = json.loads(data)
                schema = schema_data.get("schema")
                if schema and "version" not in schema:
                    schema = dict(schema)
                    schema["version"] = version
                if schema and "version" not in schema:
                    raise ValueError(
                        f"Schema {schema_id} does not have a version field"
                    )
                return schema

        # Try original schema_id
        data = self._client.get(self._key("schemas", schema_id))
        if data:
            schema_data = json.loads(data)
            schema = schema_data.get("schema")
            stored_version = schema_data.get("version")

            # Ensure schema has version
            if schema and "version" not in schema:
                schema = dict(schema)  # Make a copy
                schema["version"] = stored_version or "1.0.0"

            # Validate schema has version
            if schema and "version" not in schema:
                raise ValueError(f"Schema {schema_id} does not have a version field")

            return schema
        return None

    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all stored schemas."""
        if not self._client:
            raise RuntimeError("Not connected. Call connect() first.")

        schema_ids = self._client.smembers(self._key("schemas", "index"))
        schemas = []

        for schema_id in schema_ids:
            data = self._client.get(self._key("schemas", schema_id))
            if data:
                schema_data = json.loads(data)
                schemas.append(
                    {
                        "id": schema_data.get("id"),
                        "name": schema_data.get("name"),
                        "version": schema_data.get("version"),
                    }
                )

        return schemas

    def store_metadata(
        self,
        schema_id: str,
        metadata: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Store additional metadata.

        Args:
            schema_id: Schema identifier
            metadata: Metadata dictionary
            version: Optional version string (if None, uses schema version)

        Returns:
            Metadata record ID
        """
        if not self._client:
            raise RuntimeError("Not connected. Call connect() first.")

        # For Redis store, version is stored in the key if provided
        if version:
            key = f"schema:{schema_id}:{version}"
        else:
            key = f"schema:{schema_id}"
        
        # Store metadata with version in the value
        metadata_with_version = metadata.copy()
        if version:
            metadata_with_version["version"] = version
        
        self._client.set(self._key("metadata", key), json.dumps(metadata_with_version))

        # Add to index
        self._client.sadd(self._key("metadata", "schema", "index"), schema_id)

        return key

    def get_metadata(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a schema.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, uses latest version)

        Returns:
            Metadata dictionary or None if not found
        """
        if not self._client:
            raise RuntimeError("Not connected. Call connect() first.")

        # Try versioned first
        if version:
            key = f"schema:{schema_id}:{version}"
            data = self._client.get(self._key("metadata", key))
            if data:
                return json.loads(data)
        
        # Try unversioned (latest)
        key = f"schema:{schema_id}"
        data = self._client.get(self._key("metadata", key))
        if data:
            return json.loads(data)
        return None
