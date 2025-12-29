"""
MongoDB Metadata Store Implementation

Stores metadata in MongoDB collections.
"""

from typing import Any, Dict, List, Optional, Union

try:
    from pymongo import MongoClient  # type: ignore[import-untyped]
    from pymongo.collection import Collection  # type: ignore[import-untyped]
    from pymongo.database import Database  # type: ignore[import-untyped]

    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    MongoClient = None  # type: ignore[assignment,misc]
    Collection = None  # type: ignore[assignment,misc]
    Database = None  # type: ignore[assignment,misc]

from pycharter.metadata_store.client import MetadataStoreClient


class MongoDBMetadataStore(MetadataStoreClient):
    """
    MongoDB metadata store implementation.

    Stores metadata in MongoDB collections:
    - data_contracts: Central collection that links all components together
    - schemas: JSON Schema definitions (linked via data_contract_id)
    - metadata_records: Metadata including governance rules (linked via data_contract_id)
    - coercion_rules: Coercion rules for data transformation (linked via data_contract_id)
    - validation_rules: Validation rules for data validation (linked via data_contract_id)

    Connection string format: mongodb://[username:password@]host[:port][/database]

    The structure mirrors PostgreSQL's data_contracts table, where all components
    are linked via data_contract_id. This ensures consistency across both storage backends.

    Example:
        >>> store = MongoDBMetadataStore("mongodb://localhost:27017/pycharter")
        >>> store.connect()  # Indexes are created automatically on first connection
        >>> schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
        >>> store.store_coercion_rules(schema_id, {"age": "coerce_to_integer"}, version="1.0")
        >>> store.store_validation_rules(schema_id, {"age": {"is_positive": {}}}, version="1.0")

    Note:
        Indexes are created automatically on connect() by default. The implementation
        checks if indexes exist before creating them to avoid unnecessary overhead.
        To skip index creation (e.g., if indexes are managed externally), use:
        >>> store.connect(ensure_indexes=False)
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_name: str = "pycharter",
    ):
        """
        Initialize MongoDB metadata store.

        Args:
            connection_string: MongoDB connection string
            database_name: Database name (default: "pycharter")
        """
        if not MONGO_AVAILABLE:
            raise ImportError(
                "pymongo is required for MongoDBMetadataStore. "
                "Install with: pip install pymongo"
            )
        super().__init__(connection_string)
        self.database_name = database_name
        self._client: Optional[MongoClient] = None
        self._db: Any = None

    def connect(self, ensure_indexes: bool = True) -> None:
        """
        Connect to MongoDB.

        Args:
            ensure_indexes: If True, ensure indexes exist (default: True).
                          Set to False if you've already created indexes manually
                          or want to skip index creation for performance.
        """
        if not self.connection_string:
            raise ValueError("connection_string is required for MongoDB")

        self._client = MongoClient(self.connection_string)
        self._db = self._client[self.database_name]  # type: ignore[assignment]
        self._connection = self._db

        # Create indexes for better query performance (only if requested)
        if ensure_indexes:
            self._ensure_indexes()

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._connection = None

    def _ensure_indexes(self) -> None:
        """
        Ensure all required indexes exist.

        This method checks if indexes exist before creating them to avoid
        unnecessary overhead on every connection. Indexes are created in
        the background to avoid blocking operations.

        Note: MongoDB's create_index() is idempotent, but checking first
        avoids the overhead of the check that MongoDB does internally.
        """
        if self._db is None:
            return

        # Helper to normalize index spec for comparison
        def normalize_index_spec(spec):
            """Normalize index spec to a comparable format."""
            if isinstance(spec, str):
                return {spec: 1}
            elif isinstance(spec, list):
                return dict(spec)
            return spec

        # Helper to check if index exists by comparing key specs
        def index_exists_by_keys(collection, index_spec) -> bool:
            """Check if an index with the given key specification exists."""
            try:
                normalized_spec = normalize_index_spec(index_spec)
                indexes = list(collection.list_indexes())
                for idx in indexes:
                    # Compare index keys (excluding _id index)
                    idx_keys = idx.get("key", {})
                    if idx_keys == normalized_spec:
                        return True
                return False
            except Exception:
                # If we can't check, assume it doesn't exist and let create_index handle it
                return False

        # Helper to create index if it doesn't exist
        def create_index_if_missing(collection, index_spec, **kwargs):
            """Create index only if it doesn't exist."""
            if not index_exists_by_keys(collection, index_spec):
                collection.create_index(index_spec, background=True, **kwargs)

        # Create indexes for data_contracts collection
        create_index_if_missing(self._db.data_contracts, "name")
        create_index_if_missing(
            self._db.data_contracts, [("name", 1), ("version", 1)], unique=True
        )

        # Create indexes for schemas collection
        create_index_if_missing(self._db.schemas, "data_contract_id")
        create_index_if_missing(
            self._db.schemas, [("data_contract_id", 1), ("version", 1)], unique=True
        )

        # Create indexes for metadata_records collection
        create_index_if_missing(self._db.metadata_records, "data_contract_id")
        create_index_if_missing(
            self._db.metadata_records,
            [("data_contract_id", 1), ("version", 1)],
            unique=True,
        )

        # Create indexes for coercion_rules collection
        create_index_if_missing(self._db.coercion_rules, "data_contract_id")
        create_index_if_missing(self._db.coercion_rules, "schema_id")
        create_index_if_missing(
            self._db.coercion_rules,
            [("data_contract_id", 1), ("version", 1)],
            unique=True,
        )

        # Create indexes for validation_rules collection
        create_index_if_missing(self._db.validation_rules, "data_contract_id")
        create_index_if_missing(self._db.validation_rules, "schema_id")
        create_index_if_missing(
            self._db.validation_rules,
            [("data_contract_id", 1), ("version", 1)],
            unique=True,
        )

    def _get_or_create_data_contract(
        self,
        contract_name: str,
        version: str,
        status: str = "active",
        description: Optional[str] = None,
    ) -> str:
        """
        Get or create a data_contract record.

        Args:
            contract_name: Data contract name
            version: Contract version
            status: Contract status (default: "active")
            description: Optional description

        Returns:
            Data contract ID as string
        """
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Try to get existing data contract
        existing = self._db.data_contracts.find_one(
            {"name": contract_name, "version": version}
        )

        if existing:
            return str(existing["_id"])

        # Create new data contract
        from bson import ObjectId

        data_contract_id = ObjectId()
        doc = {
            "_id": data_contract_id,
            "name": contract_name,
            "version": version,
            "status": status,
            "description": description,
        }
        self._db.data_contracts.insert_one(doc)
        return str(data_contract_id)

    def store_schema(
        self,
        schema_name: str,
        schema: Dict[str, Any],
        version: str,
    ) -> str:
        """
        Store a schema in MongoDB.

        Args:
            schema_name: Name/identifier for the schema (used as data_contract name)
            schema: JSON Schema dictionary (must contain "version" field or it will be added)
            version: Required version string (must match schema["version"] if present)

        Returns:
            Schema ID as string

        Raises:
            ValueError: If version is missing or doesn't match schema version
        """
        if self._db is None:
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

        # Get or create data contract
        from bson import ObjectId

        data_contract_id_str = self._get_or_create_data_contract(
            contract_name=schema_name,
            version=version,
            description=schema.get("description"),
        )
        data_contract_id: Any = ObjectId(data_contract_id_str)

        # Get title from schema or use schema_name
        title = schema.get("title") or schema_name

        # Check if schema already exists for this data_contract_id and version
        existing = self._db.schemas.find_one(
            {"data_contract_id": data_contract_id, "version": version}
        )

        if existing:
            # Prevent overwriting existing schemas - raise error instead
            raise ValueError(
                f"Schema with version '{version}' already exists for contract '{schema_name}'. "
                f"Cannot overwrite existing contracts. Use a different version number."
            )
        else:
            # Insert new schema
            schema_id = ObjectId()
            doc = {
                "_id": schema_id,
                "title": title,
                "data_contract_id": data_contract_id,
                "version": version,
                "schema_data": schema,
            }
            self._db.schemas.insert_one(doc)

        # Update data_contract with schema_id
        self._db.data_contracts.update_one(
            {"_id": data_contract_id},
            {
                "$set": {
                    "schema_id": schema_id,
                    "schema_version": version,
                }
            },
        )

        return str(schema_id)

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
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        from bson import ObjectId

        try:
            schema_obj_id: Union[Any, str] = ObjectId(schema_id)
        except Exception:
            # If ObjectId conversion fails, try as string
            schema_obj_id = schema_id

        query = {"_id": schema_obj_id}
        if version:
            query["version"] = version

        doc = self._db.schemas.find_one(query)

        if not doc and version:
            # If version specified but not found, try without version filter
            doc = self._db.schemas.find_one({"_id": schema_obj_id})

        if doc:
            schema_data = doc.get("schema_data") or doc.get("schema")
            stored_version = doc.get("version")

            # If version specified, check it matches
            if version and stored_version and stored_version != version:
                return None  # Version mismatch

            # Ensure schema has version
            if schema_data and "version" not in schema_data:
                schema_data = dict(schema_data)  # Make a copy
                schema_data["version"] = stored_version or "1.0.0"

            return schema_data
        return None

    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all stored schemas."""
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        schemas = []
        for doc in self._db.schemas.find(
            {}, {"_id": 1, "title": 1, "version": 1, "data_contract_id": 1}
        ):
            # Get data_contract name
            data_contract_id = doc.get("data_contract_id")
            data_contract_name = None
            if data_contract_id:
                dc_doc = self._db.data_contracts.find_one(
                    {"_id": data_contract_id}, {"name": 1}
                )
                if dc_doc:
                    data_contract_name = dc_doc.get("name")

            schemas.append(
                {
                    "id": str(doc["_id"]),
                    "name": data_contract_name or doc.get("title"),
                    "title": doc.get("title"),
                    "version": doc.get("version"),
                }
            )
        return schemas

    def _get_schema_info(
        self, schema_id: str, raise_if_not_found: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Helper method to get schema info (data_contract_id, version, title, name) from schema_id.

        Args:
            schema_id: Schema identifier
            raise_if_not_found: If True, raise ValueError if schema not found

        Returns:
            Dictionary with data_contract_id, version, title, data_contract_name, or None if not found

        Raises:
            ValueError: If schema is not found and raise_if_not_found is True
        """
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        from bson import ObjectId

        try:
            schema_obj_id: Any = ObjectId(schema_id)
        except Exception:
            schema_obj_id = schema_id  # type: ignore[assignment]

        schema_doc = self._db.schemas.find_one({"_id": schema_obj_id})

        if not schema_doc:
            if raise_if_not_found:
                raise ValueError(f"Schema not found: {schema_id}")
            return None

        data_contract_id = schema_doc.get("data_contract_id")
        version = schema_doc.get("version")
        title = schema_doc.get("title")

        # Get data_contract name
        data_contract_name = None
        if data_contract_id:
            dc_doc = self._db.data_contracts.find_one(
                {"_id": data_contract_id}, {"name": 1}
            )
            if dc_doc:
                data_contract_name = dc_doc.get("name")

        return {
            "data_contract_id": data_contract_id,
            "version": version,
            "title": title,
            "data_contract_name": data_contract_name,
        }

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
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Get data_contract_id and version from schema
        schema_info = self._get_schema_info(schema_id, raise_if_not_found=True)
        if not schema_info:
            raise ValueError(f"Schema not found: {schema_id}")

        data_contract_id = schema_info["data_contract_id"]
        schema_version = schema_info["version"]
        data_contract_name = schema_info["data_contract_name"]

        # Use provided version or schema version
        if not version:
            version = schema_version

        # Extract metadata fields
        title = metadata.get("title") or f"Metadata for {schema_id}"
        status = metadata.get("status", "active")
        description = metadata.get("description")
        governance_rules = metadata.get("governance_rules")

        # Check if metadata_record already exists
        existing = self._db.metadata_records.find_one(
            {"data_contract_id": data_contract_id, "version": version}
        )

        from bson import ObjectId

        if existing:
            # Update existing metadata_record
            metadata_id = existing["_id"]
            self._db.metadata_records.update_one(
                {"_id": metadata_id},
                {
                    "$set": {
                        "title": title,
                        "status": status,
                        "description": description,
                        "governance_rules": governance_rules,
                    }
                },
            )
        else:
            # Insert new metadata_record
            metadata_id = ObjectId()
            doc = {
                "_id": metadata_id,
                "title": title,
                "data_contract_id": data_contract_id,
                "version": version,
                "status": status,
                "description": description,
                "governance_rules": governance_rules,
            }
            self._db.metadata_records.insert_one(doc)

        # Update data_contract with metadata_record_id
        self._db.data_contracts.update_one(
            {"_id": data_contract_id},
            {
                "$set": {
                    "metadata_record_id": metadata_id,
                    "metadata_version": version,
                }
            },
        )

        return str(metadata_id)

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
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Get metadata_record via schema -> data_contract
        schema_info = self._get_schema_info(schema_id, raise_if_not_found=False)
        if not schema_info:
            return None

        data_contract_id = schema_info["data_contract_id"]

        # Get metadata_record for this data_contract
        if version:
            doc = self._db.metadata_records.find_one(
                {"data_contract_id": data_contract_id, "version": version}
            )
        else:
            # Get latest metadata_record for this data_contract
            doc = self._db.metadata_records.find_one(
                {"data_contract_id": data_contract_id},
                sort=[("version", -1)],  # Sort by version descending (latest first)
            )

        if not doc:
            return None

        # Reconstruct metadata dictionary
        metadata = {
            "title": doc.get("title"),
            "status": doc.get("status"),
            "description": doc.get("description"),
            "version": doc.get("version"),
        }

        # Add JSON fields
        if doc.get("governance_rules"):
            metadata["governance_rules"] = doc["governance_rules"]

        return metadata

    def store_coercion_rules(
        self,
        schema_id: str,
        coercion_rules: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Store coercion rules for a schema.

        Args:
            schema_id: Schema identifier
            coercion_rules: Dictionary mapping field names to coercion function names
            version: Optional version string (if None, uses schema version)

        Returns:
            Rule ID or identifier

        Raises:
            ValueError: If schema is not found
        """
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Get data_contract_id, name, and version from schema
        schema_info = self._get_schema_info(schema_id, raise_if_not_found=True)
        if not schema_info:
            raise ValueError(f"Schema not found: {schema_id}")

        data_contract_id = schema_info["data_contract_id"]
        schema_version = schema_info["version"]
        schema_title = schema_info["title"]
        data_contract_name = schema_info["data_contract_name"]

        # Use provided version or schema version
        if not version:
            version = schema_version

        # Create title for coercion rules
        title = f"{schema_title} Coercion Rules"

        from bson import ObjectId

        # Check if coercion_rules already exists
        existing = self._db.coercion_rules.find_one(
            {"data_contract_id": data_contract_id, "version": version}
        )

        # Convert schema_id to ObjectId
        try:
            schema_obj_id: Any = ObjectId(schema_id)
        except Exception:
            schema_obj_id = schema_id  # type: ignore[assignment]

        if existing:
            # Update existing coercion_rules
            rule_id = existing["_id"]
            self._db.coercion_rules.update_one(
                {"_id": rule_id},
                {
                    "$set": {
                        "rules": coercion_rules,
                        "title": title,
                        "schema_id": schema_obj_id,
                    }
                },
            )
        else:
            # Insert new coercion_rules
            rule_id = ObjectId()
            doc = {
                "_id": rule_id,
                "title": title,
                "data_contract_id": data_contract_id,
                "version": version,
                "rules": coercion_rules,
                "schema_id": schema_obj_id,
            }
            self._db.coercion_rules.insert_one(doc)

        # Update data_contract with coercion_rules_id
        self._db.data_contracts.update_one(
            {"_id": data_contract_id},
            {
                "$set": {
                    "coercion_rules_id": rule_id,
                    "coercion_rules_version": version,
                }
            },
        )

        return f"coercion:{schema_id}" + (f":{version}" if version else "")

    def get_coercion_rules(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve coercion rules for a schema.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, uses schema version)

        Returns:
            Dictionary of coercion rules, or None if not found
        """
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Get data_contract_id from schema
        schema_info = self._get_schema_info(schema_id, raise_if_not_found=False)
        if not schema_info:
            return None

        data_contract_id = schema_info["data_contract_id"]
        schema_version = schema_info["version"]

        # Use provided version or schema version
        if not version:
            version = schema_version

        # Get coercion rules
        query = {"data_contract_id": data_contract_id}
        if version:
            query["version"] = version

        doc = self._db.coercion_rules.find_one(query)

        if not doc and version:
            # If version specified but not found, try without version filter
            doc = self._db.coercion_rules.find_one(
                {"data_contract_id": data_contract_id},
                sort=[("version", -1)],  # Sort by version descending (latest first)
            )

        if doc:
            return doc.get("rules")
        return None

    def store_validation_rules(
        self,
        schema_id: str,
        validation_rules: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Store validation rules for a schema.

        Args:
            schema_id: Schema identifier
            validation_rules: Dictionary mapping field names to validation configurations
            version: Optional version string (if None, uses schema version)

        Returns:
            Rule ID or identifier

        Raises:
            ValueError: If schema is not found
        """
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Get data_contract_id, name, and version from schema
        schema_info = self._get_schema_info(schema_id, raise_if_not_found=True)
        if not schema_info:
            raise ValueError(f"Schema not found: {schema_id}")

        data_contract_id = schema_info["data_contract_id"]
        schema_version = schema_info["version"]
        schema_title = schema_info["title"]
        data_contract_name = schema_info["data_contract_name"]

        # Use provided version or schema version
        if not version:
            version = schema_version

        # Create title for validation rules
        title = f"{schema_title} Validation Rules"

        from bson import ObjectId

        # Check if validation_rules already exists
        existing = self._db.validation_rules.find_one(
            {"data_contract_id": data_contract_id, "version": version}
        )

        # Convert schema_id to ObjectId
        try:
            schema_obj_id: Any = ObjectId(schema_id)
        except Exception:
            schema_obj_id = schema_id  # type: ignore[assignment]

        if existing:
            # Update existing validation_rules
            rule_id = existing["_id"]
            self._db.validation_rules.update_one(
                {"_id": rule_id},
                {
                    "$set": {
                        "rules": validation_rules,
                        "title": title,
                        "schema_id": schema_obj_id,
                    }
                },
            )
        else:
            # Insert new validation_rules
            rule_id = ObjectId()
            doc = {
                "_id": rule_id,
                "title": title,
                "data_contract_id": data_contract_id,
                "version": version,
                "rules": validation_rules,
                "schema_id": schema_obj_id,
            }
            self._db.validation_rules.insert_one(doc)

        # Update data_contract with validation_rules_id
        self._db.data_contracts.update_one(
            {"_id": data_contract_id},
            {
                "$set": {
                    "validation_rules_id": rule_id,
                    "validation_rules_version": version,
                }
            },
        )

        return f"validation:{schema_id}" + (f":{version}" if version else "")

    def get_validation_rules(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve validation rules for a schema.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, uses schema version)

        Returns:
            Dictionary of validation rules, or None if not found
        """
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Get data_contract_id from schema
        schema_info = self._get_schema_info(schema_id, raise_if_not_found=False)
        if not schema_info:
            return None

        data_contract_id = schema_info["data_contract_id"]
        schema_version = schema_info["version"]

        # Use provided version or schema version
        if not version:
            version = schema_version

        # Get validation rules
        query = {"data_contract_id": data_contract_id}
        if version:
            query["version"] = version

        doc = self._db.validation_rules.find_one(query)

        if not doc and version:
            # If version specified but not found, try without version filter
            doc = self._db.validation_rules.find_one(
                {"data_contract_id": data_contract_id},
                sort=[("version", -1)],  # Sort by version descending (latest first)
            )

        if doc:
            return doc.get("rules")
        return None

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the current database schema.

        Returns:
            Dictionary with schema information:
            {
                "revision": str or None,
                "initialized": bool,
                "message": str
            }
        """
        if self._db is None:
            raise RuntimeError("Not connected. Call connect() first.")

        # Check if collections exist (equivalent to "initialized")
        initialized = (
            "data_contracts" in self._db.list_collection_names()
            and "schemas" in self._db.list_collection_names()
        )

        # MongoDB doesn't have migrations like Postgres, so no revision
        revision = None

        return {
            "revision": revision,
            "initialized": initialized,
            "message": f"Schema initialized: {initialized}"
            + (f" (revision: {revision})" if revision else ""),
        }
