"""
SQLite Metadata Store Implementation

Stores metadata in SQLite database file.
"""

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import create_engine, inspect, text

from pycharter.metadata_store.client import MetadataStoreClient

if TYPE_CHECKING:
    from sqlite3 import Connection as SQLiteConnection
else:
    SQLiteConnection = Any

try:
    from pycharter.config import get_database_url
except ImportError:
    def get_database_url() -> Optional[str]:  # type: ignore[misc]
        return None


class SQLiteMetadataStore(MetadataStoreClient):
    """
    SQLite metadata store implementation.

    Stores metadata in SQLite database file:
    - schemas: JSON Schema definitions
    - metadata_records: Metadata including governance rules
    - coercion_rules: Coercion rules for data transformation
    - validation_rules: Validation rules for data validation
    - data_contracts: Central table linking all components

    Connection string format: sqlite:///path/to/database.db
    Or: sqlite:///:memory: (for in-memory database)

    The database file is created automatically if it doesn't exist.
    Tables are initialized using SQLAlchemy models (same as PostgreSQL).

    Example:
        >>> # First, initialize the database schema
        >>> # Run: pycharter db init sqlite:///pycharter.db
        >>>
        >>> # Then connect
        >>> store = SQLiteMetadataStore("sqlite:///pycharter.db")
        >>> store.connect()  # Only connects and validates schema
        >>> schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
        >>> store.store_coercion_rules(schema_id, {"age": "coerce_to_integer"}, version="1.0")
        >>> store.store_validation_rules(schema_id, {"age": {"is_positive": {}}}, version="1.0")
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize SQLite metadata store.

        Args:
            connection_string: Optional SQLite connection string.
                            If not provided, will use configuration from:
                            - PYCHARTER__DATABASE__SQL_ALCHEMY_CONN env var
                            - PYCHARTER_DATABASE_URL env var
                            - pycharter.cfg config file
                            - alembic.ini config file

        Connection string formats:
            - sqlite:///path/to/database.db (absolute or relative path)
            - sqlite:///:memory: (in-memory database)
        """
        # Try to get connection string from config if not provided
        if not connection_string:
            connection_string = get_database_url()

        if not connection_string:
            raise ValueError(
                "connection_string is required. Provide it directly, or configure it via:\n"
                "  - Environment variable: PYCHARTER__DATABASE__SQL_ALCHEMY_CONN or PYCHARTER_DATABASE_URL\n"
                "  - Config file: pycharter.cfg [database] sql_alchemy_conn\n"
                "  - Config file: alembic.ini sqlalchemy.url"
            )

        # Normalize SQLite connection string
        # sqlite:///path/to/db -> sqlite:///path/to/db
        # sqlite:///:memory: -> sqlite:///:memory:
        if connection_string.startswith("sqlite:///"):
            # Extract the path part
            db_path = connection_string[10:]  # Remove "sqlite:///"
            if db_path != ":memory:":
                # Ensure parent directory exists
                db_file = Path(db_path)
                if db_file.parent and not db_file.parent.exists():
                    db_file.parent.mkdir(parents=True, exist_ok=True)
        elif not connection_string.startswith("sqlite://"):
            # If it's just a path, convert to sqlite:/// format
            db_path = Path(connection_string)
            if db_path.parent and not db_path.parent.exists():
                db_path.parent.mkdir(parents=True, exist_ok=True)
            connection_string = f"sqlite:///{db_path.absolute()}"

        super().__init__(connection_string)
        self._connection: Optional[SQLiteConnection] = None

    def connect(self, validate_schema_on_connect: bool = True, auto_initialize: bool = False) -> None:
        """
        Connect to SQLite and validate schema.

        Args:
            validate_schema_on_connect: If True, validate that tables exist after connection
            auto_initialize: If True, automatically create tables if they don't exist (default: False)

        Raises:
            ValueError: If connection_string is missing
            RuntimeError: If schema validation fails (tables don't exist) and auto_initialize is False

        Note:
            This method only connects and validates. To initialize the database schema,
            run 'pycharter db init' first, or set auto_initialize=True.
        """
        if not self.connection_string:
            raise ValueError("connection_string is required for SQLite")

        # Extract database path from connection string
        if self.connection_string.startswith("sqlite:///"):
            db_path = self.connection_string[10:]  # Remove "sqlite:///"
        else:
            db_path = self.connection_string

        # Connect to SQLite
        self._connection = sqlite3.connect(
            db_path,
            check_same_thread=False,  # Allow use from multiple threads
            isolation_level=None,  # Autocommit mode
        )
        # Enable foreign keys
        self._connection.execute("PRAGMA foreign_keys = ON")

        if validate_schema_on_connect:
            if not self._is_schema_initialized():
                if auto_initialize:
                    self._initialize_schema()
                else:
                    raise RuntimeError(
                        "Database schema is not initialized. "
                        "Please run 'pycharter db init' to initialize the schema first.\n"
                        f"Example: pycharter db init {self.connection_string}"
                    )

    def disconnect(self) -> None:
        """Close SQLite connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    # ============================================================================
    # Connection Management Helpers
    # ============================================================================

    def _is_schema_initialized(self) -> bool:
        """Check if the database schema is initialized."""
        if self._connection is None:
            return False

        try:
            cursor = self._connection.cursor()
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schemas'
                """
            )
            return cursor.fetchone() is not None
        except Exception:
            return False

    def _initialize_schema(self) -> None:
        """Initialize database schema using SQLAlchemy models."""
        try:
            from pycharter.db.models.base import Base

            # Create all tables
            engine = create_engine(self.connection_string)
            Base.metadata.create_all(engine)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize schema: {e}")

    def _require_connection(self) -> None:
        """Raise error if not connected."""
        if self._connection is None:
            raise RuntimeError("Not connected. Call connect() first.")

    def _get_connection(self) -> SQLiteConnection:
        """Get connection, raising error if not connected."""
        if self._connection is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._connection

    def _table_name(self, table: str) -> str:
        """Get table name (SQLite doesn't use schemas)."""
        return table

    # ============================================================================
    # Schema Info
    # ============================================================================

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
        self._require_connection()

        initialized = self._is_schema_initialized()
        revision = None

        if initialized:
            try:
                # Check if alembic_version table exists
                cursor = self._connection.cursor()
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='alembic_version'
                    """
                )
                if cursor.fetchone():
                    cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
                    row = cursor.fetchone()
                    if row:
                        revision = row[0]
            except Exception:
                pass

        message = f"Schema initialized: {initialized}"
        if revision:
            message += f" (revision: {revision})"

        return {
            "revision": revision,
            "initialized": initialized,
            "message": message,
        }

    # ============================================================================
    # Schema Operations
    # ============================================================================

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
            Data contract ID (UUID as string)
        """
        self._require_connection()
        conn = self._get_connection()

        cursor = conn.cursor()

        # Try to get existing data contract
        cursor.execute(
            """
            SELECT id FROM data_contracts
            WHERE name = ? AND version = ?
            """,
            (contract_name, version),
        )

        row = cursor.fetchone()
        if row:
            return row[0]

        # Generate UUID (SQLite doesn't have gen_random_uuid(), so we use Python's uuid)
        import uuid
        data_contract_id = str(uuid.uuid4())

        # Create new data contract
        cursor.execute(
            """
            INSERT INTO data_contracts 
                (id, name, version, status, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (data_contract_id, contract_name, version, status, description),
        )

        return data_contract_id

    def store_schema(
        self,
        schema_name: str,
        schema: Dict[str, Any],
        version: str,
    ) -> str:
        """
        Store a schema in SQLite.

        Args:
            schema_name: Name/identifier for the schema (used as data_contract name)
            schema: JSON Schema dictionary
            version: Required version string (must match schema["version"] if present)

        Returns:
            Schema ID as string

        Raises:
            ValueError: If version is missing or doesn't match schema version
        """
        self._require_connection()
        conn = self._get_connection()

        # Ensure schema has version
        if "version" not in schema:
            schema = dict(schema)
            schema["version"] = version
        elif schema.get("version") != version:
            raise ValueError(
                f"Version mismatch: provided version '{version}' does not match "
                f"schema version '{schema.get('version')}'"
            )

        # Get or create data contract
        data_contract_id = self._get_or_create_data_contract(
            contract_name=schema_name,
            version=version,
            description=schema.get("description"),
        )

        # Get title from schema or use schema_name
        title = schema.get("title") or schema_name

        cursor = conn.cursor()

        # Check if schema already exists for this data_contract_id and version
        cursor.execute(
            """
            SELECT id FROM schemas
            WHERE data_contract_id = ? AND version = ?
            """,
            (data_contract_id, version),
        )

        existing = cursor.fetchone()

        if existing:
            # Prevent overwriting existing schemas - raise error instead
            raise ValueError(
                f"Schema with version '{version}' already exists for contract '{schema_name}'. "
                f"Cannot overwrite existing contracts. Use a different version number."
            )
        else:
            # Generate UUID for new schema
            import uuid
            schema_id = str(uuid.uuid4())

            # Insert new schema
            cursor.execute(
                """
                INSERT INTO schemas 
                    (id, title, data_contract_id, version, schema_data)
                VALUES (?, ?, ?, ?, ?)
                """,
                (schema_id, title, data_contract_id, version, json.dumps(schema)),
            )

        # Update data_contract with schema_id
        cursor.execute(
            """
            UPDATE data_contracts
            SET schema_id = ?, schema_version = ?
            WHERE id = ?
            """,
            (schema_id, version, data_contract_id),
        )

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
        """
        self._require_connection()
        conn = self._get_connection()

        cursor = conn.cursor()

        if version:
            cursor.execute(
                """
                SELECT schema_data, version 
                FROM schemas
                WHERE id = ? AND version = ?
                """,
                (schema_id, version),
            )
        else:
            cursor.execute(
                """
                SELECT schema_data, version 
                FROM schemas
                WHERE id = ? 
                ORDER BY version DESC 
                LIMIT 1
                """,
                (schema_id,),
            )

        row = cursor.fetchone()
        if not row:
            return None

        schema_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        stored_version = row[1]

        # Ensure schema has version
        if "version" not in schema_data:
            schema_data = dict(schema_data)
            schema_data["version"] = stored_version or "1.0.0"

        return schema_data

    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all stored schemas."""
        self._require_connection()
        conn = self._get_connection()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.id, s.title, s.version, dc.name as data_contract_name
            FROM schemas s
            LEFT JOIN data_contracts dc 
                ON s.data_contract_id = dc.id
            ORDER BY s.title, s.version
            """
        )

        return [
            {
                "id": str(row[0]),
                "name": row[3] or row[1],  # data_contract_name or title
                "title": row[1],
                "version": row[2],
            }
            for row in cursor.fetchall()
        ]

    # ============================================================================
    # Metadata Operations
    # ============================================================================

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
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id, name, and version from schema/data_contract
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.data_contract_id, s.version, dc.name as data_contract_name
            FROM schemas s
            JOIN data_contracts dc 
                ON s.data_contract_id = dc.id
            WHERE s.id = ?
            """,
            (schema_id,),
        )

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Schema {schema_id} not found")

        data_contract_id = row[0]
        schema_version = row[1]
        data_contract_name = row[2]

        # Use provided version or schema version
        if version is None:
            version = schema_version

        # Extract metadata fields
        title = metadata.get("title") or data_contract_name
        status = metadata.get("status", "active")
        description = metadata.get("description")
        governance_rules = metadata.get("governance_rules")

        # Check if metadata_record already exists
        cursor.execute(
            """
            SELECT id FROM metadata_records
            WHERE data_contract_id = ? AND version = ?
            """,
            (data_contract_id, version),
        )

        existing = cursor.fetchone()

        if existing:
            # Update existing metadata_record
            metadata_id = existing[0]
            cursor.execute(
                """
                UPDATE metadata_records
                SET title = ?,
                    status = ?,
                    description = ?,
                    governance_rules = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    title,
                    status,
                    description,
                    json.dumps(governance_rules) if governance_rules else None,
                    metadata_id,
                ),
            )
        else:
            # Generate UUID for new metadata_record
            import uuid
            metadata_id = str(uuid.uuid4())

            # Insert new metadata_record
            cursor.execute(
                """
                INSERT INTO metadata_records 
                    (id, title, data_contract_id, version, status, description, governance_rules)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata_id,
                    title,
                    data_contract_id,
                    version,
                    status,
                    description,
                    json.dumps(governance_rules) if governance_rules else None,
                ),
            )

        # Update data_contract with metadata_record_id
        cursor.execute(
            """
            UPDATE data_contracts
            SET metadata_record_id = ?, metadata_version = ?
            WHERE id = ?
            """,
            (metadata_id, version, data_contract_id),
        )

        return metadata_id

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
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id from schema
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data_contract_id FROM schemas
            WHERE id = ?
            """,
            (schema_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        data_contract_id = row[0]

        # Get metadata_record
        if version:
            cursor.execute(
                """
                SELECT title, status, description, governance_rules, version
                FROM metadata_records
                WHERE data_contract_id = ? AND version = ?
                """,
                (data_contract_id, version),
            )
        else:
            cursor.execute(
                """
                SELECT title, status, description, governance_rules, version
                FROM metadata_records
                WHERE data_contract_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (data_contract_id,),
            )

        row = cursor.fetchone()
        if not row:
            return None

        governance_rules = (
            json.loads(row[3]) if isinstance(row[3], str) else row[3]
            if row[3] else None
        )

        return {
            "title": row[0],
            "status": row[1],
            "description": row[2],
            "governance_rules": governance_rules,
            "version": row[4],
        }

    # ============================================================================
    # Coercion Rules Operations
    # ============================================================================

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
            version: Optional version string

        Returns:
            Coercion rules ID
        """
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id and version from schema
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data_contract_id, version, title
            FROM schemas
            WHERE id = ?
            """,
            (schema_id,),
        )

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Schema {schema_id} not found")

        data_contract_id = row[0]
        schema_version = row[1]
        schema_title = row[2]

        # Use provided version or schema version
        if version is None:
            version = schema_version

        title = f"{schema_title} Coercion Rules"

        # Check if coercion_rules already exists
        cursor.execute(
            """
            SELECT id FROM coercion_rules
            WHERE data_contract_id = ? AND version = ?
            """,
            (data_contract_id, version),
        )

        existing = cursor.fetchone()

        if existing:
            # Update existing coercion_rules
            rule_id = existing[0]
            cursor.execute(
                """
                UPDATE coercion_rules
                SET rules = ?,
                    title = ?,
                    schema_id = ?
                WHERE id = ?
                """,
                (json.dumps(coercion_rules), title, schema_id, rule_id),
            )
        else:
            # Generate UUID for new coercion_rules
            import uuid
            rule_id = str(uuid.uuid4())

            # Insert new coercion_rules
            cursor.execute(
                """
                INSERT INTO coercion_rules 
                    (id, title, data_contract_id, version, rules, schema_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rule_id, title, data_contract_id, version, json.dumps(coercion_rules), schema_id),
            )

        # Update data_contract with coercion_rules_id
        cursor.execute(
            """
            UPDATE data_contracts
            SET coercion_rules_id = ?, coercion_rules_version = ?
            WHERE id = ?
            """,
            (rule_id, version, data_contract_id),
        )

        return rule_id

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
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id from schema
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data_contract_id FROM schemas
            WHERE id = ?
            """,
            (schema_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        data_contract_id = row[0]

        # Get coercion_rules
        if version:
            cursor.execute(
                """
                SELECT rules FROM coercion_rules
                WHERE data_contract_id = ? AND version = ?
                """,
                (data_contract_id, version),
            )
        else:
            cursor.execute(
                """
                SELECT rules FROM coercion_rules
                WHERE data_contract_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (data_contract_id,),
            )

        row = cursor.fetchone()
        if not row:
            return None

        return json.loads(row[0]) if isinstance(row[0], str) else row[0]

    # ============================================================================
    # Validation Rules Operations
    # ============================================================================

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
            version: Optional version string

        Returns:
            Validation rules ID
        """
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id and version from schema
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data_contract_id, version, title
            FROM schemas
            WHERE id = ?
            """,
            (schema_id,),
        )

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Schema {schema_id} not found")

        data_contract_id = row[0]
        schema_version = row[1]
        schema_title = row[2]

        # Use provided version or schema version
        if version is None:
            version = schema_version

        title = f"{schema_title} Validation Rules"

        # Check if validation_rules already exists
        cursor.execute(
            """
            SELECT id FROM validation_rules
            WHERE data_contract_id = ? AND version = ?
            """,
            (data_contract_id, version),
        )

        existing = cursor.fetchone()

        if existing:
            # Update existing validation_rules
            rule_id = existing[0]
            cursor.execute(
                """
                UPDATE validation_rules
                SET rules = ?,
                    title = ?,
                    schema_id = ?
                WHERE id = ?
                """,
                (json.dumps(validation_rules), title, schema_id, rule_id),
            )
        else:
            # Generate UUID for new validation_rules
            import uuid
            rule_id = str(uuid.uuid4())

            # Insert new validation_rules
            cursor.execute(
                """
                INSERT INTO validation_rules 
                    (id, title, data_contract_id, version, rules, schema_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rule_id, title, data_contract_id, version, json.dumps(validation_rules), schema_id),
            )

        # Update data_contract with validation_rules_id
        cursor.execute(
            """
            UPDATE data_contracts
            SET validation_rules_id = ?, validation_rules_version = ?
            WHERE id = ?
            """,
            (rule_id, version, data_contract_id),
        )

        return rule_id

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
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id from schema
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data_contract_id FROM schemas
            WHERE id = ?
            """,
            (schema_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        data_contract_id = row[0]

        # Get validation_rules
        if version:
            cursor.execute(
                """
                SELECT rules FROM validation_rules
                WHERE data_contract_id = ? AND version = ?
                """,
                (data_contract_id, version),
            )
        else:
            cursor.execute(
                """
                SELECT rules FROM validation_rules
                WHERE data_contract_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (data_contract_id,),
            )

        row = cursor.fetchone()
        if not row:
            return None

        return json.loads(row[0]) if isinstance(row[0], str) else row[0]



