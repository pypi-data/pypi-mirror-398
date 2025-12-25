"""
Metadata Store Client - Database operations for metadata storage.

Manages tables for:
- Schemas (JSON Schema definitions)
- Metadata records (including governance rules and ownership)
- Other metadata
"""

from typing import Any, Dict, List, Optional


class MetadataStoreClient:
    """
    Client for storing and retrieving metadata from a relational database.

    This is a base implementation that can be extended for specific databases
    (PostgreSQL, MySQL, etc.) or cloud services (AWS RDS).
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize metadata store client.

        Args:
            connection_string: Database connection string (format depends on implementation)
        """
        self.connection_string = connection_string
        self._connection = None

    def connect(self) -> None:
        """
        Establish database connection.

        Subclasses should implement this method.
        """
        raise NotImplementedError("Subclasses must implement connect()")

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            # Subclasses should implement proper cleanup
            self._connection = None

    def store_schema(
        self,
        schema_name: str,
        schema: Dict[str, Any],
        version: str,
    ) -> str:
        """
        Store a JSON Schema in the database.

        Args:
            schema_name: Name/identifier for the schema
            schema: JSON Schema dictionary (must contain "version" field or it will be added)
            version: Required version string (must match schema["version"] if present)

        Returns:
            Schema ID or identifier

        Raises:
            ValueError: If version is missing or doesn't match schema version
        """
        # Ensure schema has version
        if "version" not in schema:
            schema = dict(schema)  # Make a copy
            schema["version"] = version
        elif schema.get("version") != version:
            raise ValueError(
                f"Version mismatch: provided version '{version}' does not match "
                f"schema version '{schema.get('version')}'"
            )

        raise NotImplementedError("Subclasses must implement store_schema()")

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
        raise NotImplementedError("Subclasses must implement get_schema()")

    def list_schemas(self) -> List[Dict[str, Any]]:
        """
        List all stored schemas.

        Returns:
            List of schema metadata dictionaries
        """
        raise NotImplementedError("Subclasses must implement list_schemas()")

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
        raise NotImplementedError("Subclasses must implement store_metadata()")

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
        raise NotImplementedError("Subclasses must implement get_metadata()")

    def store_coercion_rules(
        self,
        schema_id: str,
        coercion_rules: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Store coercion rules for a schema.

        Coercion rules specify how to transform data before validation.
        Format: {"field_name": "coercion_function_name", ...}

        Args:
            schema_id: Schema identifier
            coercion_rules: Dictionary mapping field names to coercion function names
            version: Optional version string

        Returns:
            Coercion rules ID or identifier
        """
        raise NotImplementedError("Subclasses must implement store_coercion_rules()")

    def get_coercion_rules(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve coercion rules for a schema.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, returns latest)

        Returns:
            Coercion rules dictionary or None if not found
        """
        raise NotImplementedError("Subclasses must implement get_coercion_rules()")

    def store_validation_rules(
        self,
        schema_id: str,
        validation_rules: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Store validation rules for a schema.

        Validation rules specify additional checks after standard validation.
        Format: {"field_name": {"validator_name": config, ...}, ...}

        Args:
            schema_id: Schema identifier
            validation_rules: Dictionary mapping field names to validation configurations
            version: Optional version string

        Returns:
            Validation rules ID or identifier
        """
        raise NotImplementedError("Subclasses must implement store_validation_rules()")

    def get_validation_rules(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve validation rules for a schema.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, returns latest)

        Returns:
            Validation rules dictionary or None if not found
        """
        raise NotImplementedError("Subclasses must implement get_validation_rules()")

    def get_complete_schema(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete schema with coercion and validation rules merged.

        This is a convenience method that retrieves schema, coercion rules, and
        validation rules, then merges them into a single schema dictionary.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, returns latest)

        Returns:
            Complete schema dictionary with coercion and validation rules merged,
            or None if schema not found
        """
        schema = self.get_schema(schema_id, version)
        if not schema:
            return None

        # Validate schema has version
        if "version" not in schema:
            raise ValueError(
                f"Schema {schema_id} does not have a version field. "
                "All schemas must be versioned."
            )

        # Deep copy to avoid modifying original
        import copy

        complete_schema = copy.deepcopy(schema)

        # Get coercion rules
        coercion_rules = self.get_coercion_rules(schema_id, version)
        if coercion_rules:
            _merge_coercion_rules(complete_schema, coercion_rules)

        # Get validation rules
        validation_rules = self.get_validation_rules(schema_id, version)
        if validation_rules:
            _merge_validation_rules(complete_schema, validation_rules)

        return complete_schema

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def _merge_coercion_rules(
    schema: Dict[str, Any], coercion_rules: Dict[str, Any]
) -> None:
    """
    Merge coercion rules into schema properties.

    Args:
        schema: Schema dictionary (modified in place)
        coercion_rules: Dictionary mapping field names to coercion function names
    """
    if "properties" not in schema:
        return

    for field_name, coercion_name in coercion_rules.items():
        if field_name in schema["properties"]:
            schema["properties"][field_name]["coercion"] = coercion_name


def _merge_validation_rules(
    schema: Dict[str, Any], validation_rules: Dict[str, Any]
) -> None:
    """
    Merge validation rules into schema properties.

    Supports nested field paths using dot notation (e.g., "author.name").

    Args:
        schema: Schema dictionary (modified in place)
        validation_rules: Dictionary mapping field names to validation configurations
    """
    if "properties" not in schema:
        return

    for field_path, field_validations in validation_rules.items():
        # Handle nested fields with dot notation (e.g., "author.name")
        if "." in field_path:
            parts = field_path.split(".")
            if len(parts) == 2:
                parent_field, child_field = parts
                if parent_field in schema["properties"]:
                    parent_prop = schema["properties"][parent_field]
                    if (
                        "properties" in parent_prop
                        and child_field in parent_prop["properties"]
                    ):
                        if "validations" not in parent_prop["properties"][child_field]:
                            parent_prop["properties"][child_field]["validations"] = {}
                        parent_prop["properties"][child_field]["validations"].update(
                            field_validations
                        )
        else:
            # Handle top-level fields
            if field_path in schema["properties"]:
                if "validations" not in schema["properties"][field_path]:
                    schema["properties"][field_path]["validations"] = {}
                schema["properties"][field_path]["validations"].update(
                    field_validations
                )
