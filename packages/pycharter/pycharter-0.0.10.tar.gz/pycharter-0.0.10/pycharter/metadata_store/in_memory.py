"""
In-Memory Metadata Store Implementation

A simple in-memory implementation useful for testing and development.
"""

import json
from typing import Any, Dict, List, Optional

from pycharter.metadata_store.client import MetadataStoreClient


class InMemoryMetadataStore(MetadataStoreClient):
    """
    In-memory metadata store implementation.

    Useful for testing, development, or when persistence is not required.
    All data is stored in memory and will be lost when the instance is destroyed.

    Example:
        >>> store = InMemoryMetadataStore()
        >>> store.connect()
        >>> schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
        >>> schema = store.get_schema(schema_id)
    """

    def __init__(self):
        """Initialize in-memory store."""
        super().__init__()
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._next_id = 1

    def connect(self) -> None:
        """Connect to in-memory store (no-op for in-memory)."""
        self._connection: Any = "connected"

    def disconnect(self) -> None:
        """Disconnect from in-memory store."""
        self._connection = None

    def store_schema(
        self,
        schema_name: str,
        schema: Dict[str, Any],
        version: str,
    ) -> str:
        """
        Store a schema in memory.

        Args:
            schema_name: Name/identifier for the schema
            schema: JSON Schema dictionary (must contain "version" field or it will be added)
            version: Required version string (must match schema["version"] if present)

        Returns:
            Schema ID

        Raises:
            ValueError: If version is missing or doesn't match schema version
        """
        # Ensure schema has version (parent class handles validation)
        if "version" not in schema:
            schema = dict(schema)  # Make a copy
            schema["version"] = version
        elif schema.get("version") != version:
            raise ValueError(
                f"Version mismatch: provided version '{version}' does not match "
                f"schema version '{schema.get('version')}'"
            )

        schema_id = f"schema_{self._next_id}"
        self._next_id += 1
        self._schemas[schema_id] = {
            "id": schema_id,
            "name": schema_name,
            "version": version,
            "schema": schema,
        }
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
        if schema_id in self._schemas:
            schema = self._schemas[schema_id]["schema"]
            stored_version = self._schemas[schema_id].get("version")

            # If version specified, check it matches
            if version and stored_version and stored_version != version:
                return None  # Version mismatch

            # Ensure schema has version
            if "version" not in schema:
                schema = dict(schema)  # Make a copy
                schema["version"] = stored_version or "1.0.0"

            # Validate schema has version
            if "version" not in schema:
                raise ValueError(f"Schema {schema_id} does not have a version field")

            return schema
        return None

    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all stored schemas."""
        return [
            {
                "id": schema_id,
                "name": data["name"],
                "version": data["version"],
            }
            for schema_id, data in self._schemas.items()
        ]

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
        # For in-memory store, version is stored in the key if provided
        if version:
            key = f"schema:{schema_id}:{version}"
        else:
            key = f"schema:{schema_id}"
        self._metadata[key] = {
            "schema_id": schema_id,
            "version": version,
            "metadata": metadata,
        }
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
        # Try versioned first
        if version:
            key = f"schema:{schema_id}:{version}"
            if key in self._metadata:
                return self._metadata[key]["metadata"]
        
        # Try unversioned (latest)
        key = f"schema:{schema_id}"
        if key in self._metadata:
            return self._metadata[key]["metadata"]
        return None

    def store_coercion_rules(
        self,
        schema_id: str,
        coercion_rules: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """Store coercion rules for a schema."""
        key = f"coercion:{schema_id}"
        if version:
            key = f"{key}:{version}"
        self._metadata[key] = {
            "schema_id": schema_id,
            "version": version,
            "type": "coercion_rules",
            "rules": coercion_rules,
        }
        return key

    def get_coercion_rules(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve coercion rules for a schema."""
        # Try versioned first
        if version:
            key = f"coercion:{schema_id}:{version}"
            if (
                key in self._metadata
                and self._metadata[key].get("type") == "coercion_rules"
            ):
                return self._metadata[key]["rules"]

        # Try latest (no version)
        key = f"coercion:{schema_id}"
        if (
            key in self._metadata
            and self._metadata[key].get("type") == "coercion_rules"
        ):
            return self._metadata[key]["rules"]

        return None

    def store_validation_rules(
        self,
        schema_id: str,
        validation_rules: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """Store validation rules for a schema."""
        key = f"validation:{schema_id}"
        if version:
            key = f"{key}:{version}"
        self._metadata[key] = {
            "schema_id": schema_id,
            "version": version,
            "type": "validation_rules",
            "rules": validation_rules,
        }
        return key

    def get_validation_rules(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve validation rules for a schema."""
        # Try versioned first
        if version:
            key = f"validation:{schema_id}:{version}"
            if (
                key in self._metadata
                and self._metadata[key].get("type") == "validation_rules"
            ):
                return self._metadata[key]["rules"]

        # Try latest (no version)
        key = f"validation:{schema_id}"
        if (
            key in self._metadata
            and self._metadata[key].get("type") == "validation_rules"
        ):
            return self._metadata[key]["rules"]

        return None
