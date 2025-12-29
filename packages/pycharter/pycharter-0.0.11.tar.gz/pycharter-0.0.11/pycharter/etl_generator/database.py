"""
Database connection and loading utilities for ETL orchestrator.

This module handles:
- Database type detection
- SSH tunnel creation
- Database connection management
- Database-specific write operations
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from pycharter.utils.value_injector import resolve_values

# Optional dependency for SSH tunnels
try:
    from sshtunnel import SSHTunnelForwarder  # type: ignore
    SSH_TUNNEL_AVAILABLE = True
except ImportError:
    SSH_TUNNEL_AVAILABLE = False
    SSHTunnelForwarder = None  # type: ignore


# Database type constants
DB_POSTGRESQL = "postgresql"
DB_MYSQL = "mysql"
DB_SQLITE = "sqlite"
DB_MSSQL = "mssql"
DB_ORACLE = "oracle"

# Default ports for SSH tunnel
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_MYSQL_PORT = 3306
DEFAULT_SSH_PORT = 22
DEFAULT_TUNNEL_LOCAL_PORT = 5433


def detect_database_type(db_url: str) -> str:
    """
    Detect database type from connection string.
    
    Supports both sync and async database URL formats (e.g., postgresql+asyncpg://).
    
    Args:
        db_url: Database connection string
        
    Returns:
        Database type: 'postgresql', 'mysql', 'sqlite', 'mssql', etc.
        
    Raises:
        ValueError: If database type cannot be determined
    """
    db_url_lower = db_url.lower()
    
    # Handle async URL formats (e.g., postgresql+asyncpg://, mysql+aiomysql://)
    # Extract base database type by removing driver suffix
    if "+" in db_url_lower:
        base_url = db_url_lower.split("+", 1)[0] + "://"
    else:
        base_url = db_url_lower
    
    # Check for PostgreSQL variants
    if base_url.startswith(("postgresql://", "postgres://")):
        return DB_POSTGRESQL
    # Check for MySQL variants
    elif base_url.startswith(("mysql://", "mariadb://")):
        return DB_MYSQL
    # Check for SQLite
    elif base_url.startswith("sqlite://"):
        return DB_SQLITE
    # Check for MSSQL variants
    elif base_url.startswith(("mssql://", "sqlserver://")):
        return DB_MSSQL
    # Check for Oracle
    elif base_url.startswith("oracle://"):
        return DB_ORACLE
    else:
        raise ValueError(
            f"Cannot detect database type from connection string. "
            f"Supported formats: postgresql://, mysql://, sqlite://, mssql://, oracle:// "
            f"(async variants like postgresql+asyncpg:// are also supported). "
            f"Got: {db_url[:50]}..."
        )


def create_ssh_tunnel(ssh_config: Dict[str, Any]) -> Optional[Any]:
    """
    Create SSH tunnel for database connection.
    
    Args:
        ssh_config: SSH tunnel configuration dictionary
        
    Returns:
        SSHTunnelForwarder instance if tunnel is created, None otherwise
        
    Raises:
        ImportError: If sshtunnel package is not installed
        ValueError: If SSH configuration is invalid
    """
    if not ssh_config.get('enabled', False):
        return None
    
    if not SSH_TUNNEL_AVAILABLE:
        raise ImportError(
            "sshtunnel package required for SSH tunnels. "
            "Install with: pip install sshtunnel or pip install pycharter[etl]"
        )
    
    # Validate required SSH config
    required_fields = ['host', 'username', 'remote_host', 'remote_port']
    missing_fields = [field for field in required_fields if not ssh_config.get(field)]
    if missing_fields:
        raise ValueError(
            f"SSH tunnel configuration missing required fields: {', '.join(missing_fields)}"
        )
    
    # Get SSH credentials
    ssh_host = ssh_config['host']
    ssh_port = int(ssh_config.get('port', DEFAULT_SSH_PORT))
    ssh_username = ssh_config['username']
    ssh_password = ssh_config.get('password')
    ssh_key_file = ssh_config.get('key_file')
    
    # Get remote database connection details
    remote_host = ssh_config['remote_host']
    remote_port = int(ssh_config['remote_port'])
    local_port = int(ssh_config.get('local_port', DEFAULT_TUNNEL_LOCAL_PORT))
    
    # Create tunnel
    tunnel = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        ssh_pkey=ssh_key_file if ssh_key_file and not ssh_password else None,
        remote_bind_address=(remote_host, remote_port),
        local_bind_address=('127.0.0.1', local_port),
    )
    
    tunnel.start()
    return tunnel


def modify_url_for_tunnel(db_url: str, local_port: int, db_type: str) -> str:
    """
    Modify database URL to use local tunnel port.
    
    Args:
        db_url: Original database URL
        local_port: Local tunnel port
        db_type: Database type
        
    Returns:
        Modified database URL
    """
    if db_type == DB_POSTGRESQL:
        return re.sub(r'@[^:]+:\d+/', f'@127.0.0.1:{local_port}/', db_url)
    elif db_type == DB_MYSQL:
        return re.sub(r'@[^:]+:\d+/', f'@127.0.0.1:{local_port}/', db_url)
    # Add other database types as needed
    return db_url


def get_database_connection(
    load_config: Dict[str, Any],
    contract_dir: Optional[Any] = None,
    config_context: Optional[Dict[str, Any]] = None,
) -> Tuple[Any, Session, str, Optional[Any]]:
    """
    Get database connection from load configuration.
    
    Handles:
    - Database URL resolution (with variable injection)
    - SSH tunnel creation if configured
    - Database type detection
    - Engine and session creation
    
    Args:
        load_config: Load configuration dictionary
        contract_dir: Contract directory path (for variable resolution)
        config_context: Optional context dictionary for value injection
        
    Returns:
        Tuple of (engine, session, db_type, tunnel)
        - engine: SQLAlchemy engine
        - session: SQLAlchemy session
        - db_type: Database type string
        - tunnel: SSH tunnel instance (or None)
        
    Raises:
        ValueError: If database configuration is invalid
    """
    # Get database configuration
    db_config = load_config.get('database', {})
    
    # Get database URL (with variable injection)
    db_url = db_config.get('url')
    if not db_url:
        raise ValueError(
            "Database URL not specified in load.yaml. "
            "Add 'database.url' to your load configuration."
        )
    
    # Resolve variables in database URL
    source_file = str(contract_dir / "load.yaml") if contract_dir else None
    db_url = resolve_values(db_url, context=config_context, source_file=source_file)
    
    # Resolve SSH tunnel config if present
    ssh_config = db_config.get('ssh_tunnel', {})
    if ssh_config:
        ssh_config = resolve_values(ssh_config, context=config_context, source_file=source_file)
    
    # Handle SSH tunnel if configured
    tunnel = None
    if ssh_config.get('enabled', False):
        tunnel = create_ssh_tunnel(ssh_config)
        
        # Modify database URL to use local tunnel port
        if tunnel:
            db_type_from_url = detect_database_type(db_url)
            local_port = int(ssh_config.get('local_port', DEFAULT_TUNNEL_LOCAL_PORT))
            db_url = modify_url_for_tunnel(db_url, local_port, db_type_from_url)
    
    # Detect database type
    db_type = db_config.get('type')
    if not db_type:
        db_type = detect_database_type(db_url)
    
    # Create engine
    engine = create_engine(db_url, echo=False)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return engine, session, db_type, tunnel


def build_table_name(schema_name: str, table_name: str, db_type: str) -> str:
    """
    Build fully qualified table name for database-specific syntax.
    
    Args:
        schema_name: Database schema name
        table_name: Table name
        db_type: Database type
        
    Returns:
        Fully qualified table name
    """
    if db_type == DB_POSTGRESQL:
        return f'"{schema_name}"."{table_name}"' if schema_name else f'"{table_name}"'
    elif db_type == DB_MYSQL:
        return f'`{schema_name}`.`{table_name}`' if schema_name else f'`{table_name}`'
    elif db_type == DB_SQLITE:
        # SQLite doesn't support schemas
        return f'"{table_name}"'
    elif db_type == DB_MSSQL:
        return f'[{schema_name}].[{table_name}]' if schema_name else f'[{table_name}]'
    else:
        # Generic fallback
        return f'"{schema_name}"."{table_name}"' if schema_name else f'"{table_name}"'


def build_column_list(columns: List[str], db_type: str) -> str:
    """
    Build column list with database-specific quoting.
    
    Args:
        columns: List of column names
        db_type: Database type
        
    Returns:
        Quoted column list string
    """
    if db_type == DB_POSTGRESQL:
        return ', '.join([f'"{col}"' for col in columns])
    elif db_type == DB_MYSQL:
        return ', '.join([f'`{col}`' for col in columns])
    elif db_type == DB_SQLITE:
        return ', '.join([f'"{col}"' for col in columns])
    elif db_type == DB_MSSQL:
        return ', '.join([f'[{col}]' for col in columns])
    else:
        return ', '.join([f'"{col}"' for col in columns])


def build_placeholder_list(columns: List[str]) -> str:
    """Build placeholder list for parameterized queries."""
    return ', '.join([f':{col}' for col in columns])


def load_data_postgresql(
    data: List[Dict[str, Any]],
    session: Session,
    schema_name: str,
    table_name: str,
    write_method: str,
    primary_key: Optional[str],
    batch_size: int,
) -> Dict[str, Any]:
    """Load data into PostgreSQL using database-specific optimizations."""
    from sqlalchemy import Table, MetaData, Column, String
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    
    # Create table metadata for SQLAlchemy
    metadata = MetaData()
    # Use reflection to get actual table structure, or create a generic table reference
    # For now, use raw SQL approach which is more flexible
    full_table_name = build_table_name(schema_name, table_name, DB_POSTGRESQL)
    inserted = 0
    updated = 0
    
    # Get column names from first record
    if not data:
        return {'inserted': 0, 'updated': 0, 'total': 0}
    
    columns = list(data[0].keys())
    columns_str = ', '.join([f'"{col}"' for col in columns])
    values_placeholders = ', '.join([f':{col}' for col in columns])
    
    # Handle truncate_and_load first (before processing data)
    if write_method == 'truncate_and_load':
        session.execute(text(f'TRUNCATE TABLE {full_table_name}'))
        session.commit()
        write_method = 'insert'  # After truncate, use insert method
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        if write_method == 'upsert' and primary_key:
            for record in batch:
                # Build INSERT ... ON CONFLICT statement
                set_clause = ', '.join([f'"{k}" = EXCLUDED."{k}"' for k in columns if k != primary_key])
                sql = f"""
                    INSERT INTO {full_table_name} ({columns_str})
                    VALUES ({values_placeholders})
                    ON CONFLICT ("{primary_key}") DO UPDATE SET {set_clause}
                """
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'insert' or write_method == 'append':
            # Batch insert
            sql = f"""
                INSERT INTO {full_table_name} ({columns_str})
                VALUES ({values_placeholders})
            """
            session.execute(text(sql), batch)
            inserted += len(batch)
        elif write_method == 'replace':
            for record in batch:
                if primary_key and primary_key in record:
                    session.execute(
                        text(f'DELETE FROM {full_table_name} WHERE "{primary_key}" = :pk'),
                        {'pk': record[primary_key]}
                    )
                sql = f"""
                    INSERT INTO {full_table_name} ({columns_str})
                    VALUES ({values_placeholders})
                """
                session.execute(text(sql), record)
                inserted += 1
        elif write_method == 'update' and primary_key:
            # Update existing records only
            for record in batch:
                if primary_key not in record:
                    continue
                set_clause = ', '.join([f'"{k}" = :{k}' for k in columns if k != primary_key])
                sql = f"""
                    UPDATE {full_table_name}
                    SET {set_clause}
                    WHERE "{primary_key}" = :{primary_key}
                """
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'delete' and primary_key:
            # Delete records by primary key
            for record in batch:
                if primary_key not in record:
                    continue
                sql = f'DELETE FROM {full_table_name} WHERE "{primary_key}" = :pk'
                session.execute(text(sql), {'pk': record[primary_key]})
                updated += 1  # Using updated count for deleted count
        
        session.commit()
    
    return {'inserted': inserted, 'updated': updated, 'total': len(data)}


def load_data_mysql(
    data: List[Dict[str, Any]],
    session: Session,
    schema_name: str,
    table_name: str,
    write_method: str,
    primary_key: Optional[str],
    batch_size: int,
) -> Dict[str, Any]:
    """Load data into MySQL using database-specific optimizations."""
    full_table_name = build_table_name(schema_name, table_name, DB_MYSQL)
    inserted = 0
    updated = 0
    
    # Handle truncate_and_load first (before processing data)
    if write_method == 'truncate_and_load':
        session.execute(text(f'TRUNCATE TABLE {full_table_name}'))
        session.commit()
        write_method = 'insert'  # After truncate, use insert method
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        if write_method == 'upsert' and primary_key:
            for record in batch:
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_MYSQL)
                placeholders = build_placeholder_list(columns)
                updates = ', '.join([
                    f'`{k}` = VALUES(`{k}`)' 
                    for k in columns if k != primary_key
                ])
                
                sql = f"""
                    INSERT INTO {full_table_name} ({columns_str})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {updates}
                """
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'insert' or write_method == 'append':
            for record in batch:
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_MYSQL)
                placeholders = build_placeholder_list(columns)
                sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
                session.execute(text(sql), record)
                inserted += 1
        elif write_method == 'replace':
            for record in batch:
                if primary_key and primary_key in record:
                    session.execute(
                        text(f'DELETE FROM {full_table_name} WHERE `{primary_key}` = :pk'),
                        {'pk': record[primary_key]}
                    )
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_MYSQL)
                placeholders = build_placeholder_list(columns)
                sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
                session.execute(text(sql), record)
                inserted += 1
        elif write_method == 'update' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                columns = list(record.keys())
                set_clause = ', '.join([f'`{k}` = :{k}' for k in columns if k != primary_key])
                sql = f"""
                    UPDATE {full_table_name}
                    SET {set_clause}
                    WHERE `{primary_key}` = :{primary_key}
                """
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'delete' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                sql = f'DELETE FROM {full_table_name} WHERE `{primary_key}` = :pk'
                session.execute(text(sql), {'pk': record[primary_key]})
                updated += 1
        
        session.commit()
    
    return {'inserted': inserted, 'updated': updated, 'total': len(data)}


def load_data_sqlite(
    data: List[Dict[str, Any]],
    session: Session,
    schema_name: str,
    table_name: str,
    write_method: str,
    primary_key: Optional[str],
    batch_size: int,
) -> Dict[str, Any]:
    """Load data into SQLite using database-specific optimizations."""
    # SQLite doesn't support schemas
    full_table_name = build_table_name('', table_name, DB_SQLITE)
    inserted = 0
    updated = 0
    
    # Handle truncate_and_load first (before processing data)
    if write_method == 'truncate_and_load':
        session.execute(text(f'DELETE FROM {full_table_name}'))  # SQLite doesn't have TRUNCATE
        session.commit()
        write_method = 'insert'  # After truncate, use insert method
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        if write_method == 'upsert' and primary_key:
            for record in batch:
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_SQLITE)
                placeholders = build_placeholder_list(columns)
                sql = f"INSERT OR REPLACE INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'insert' or write_method == 'append':
            for record in batch:
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_SQLITE)
                placeholders = build_placeholder_list(columns)
                sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
                session.execute(text(sql), record)
                inserted += 1
        elif write_method == 'replace':
            for record in batch:
                if primary_key and primary_key in record:
                    session.execute(
                        text(f'DELETE FROM {full_table_name} WHERE "{primary_key}" = :pk'),
                        {'pk': record[primary_key]}
                    )
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_SQLITE)
                placeholders = build_placeholder_list(columns)
                sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
                session.execute(text(sql), record)
                inserted += 1
        elif write_method == 'update' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                columns = list(record.keys())
                set_clause = ', '.join([f'"{k}" = :{k}' for k in columns if k != primary_key])
                sql = f"""
                    UPDATE {full_table_name}
                    SET {set_clause}
                    WHERE "{primary_key}" = :{primary_key}
                """
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'delete' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                sql = f'DELETE FROM {full_table_name} WHERE "{primary_key}" = :pk'
                session.execute(text(sql), {'pk': record[primary_key]})
                updated += 1
        
        session.commit()
    
    return {'inserted': inserted, 'updated': updated, 'total': len(data)}


def load_data_mssql(
    data: List[Dict[str, Any]],
    session: Session,
    schema_name: str,
    table_name: str,
    write_method: str,
    primary_key: Optional[str],
    batch_size: int,
) -> Dict[str, Any]:
    """Load data into Microsoft SQL Server using database-specific optimizations."""
    full_table_name = build_table_name(schema_name, table_name, DB_MSSQL)
    inserted = 0
    updated = 0
    
    # Handle truncate_and_load first (before processing data)
    if write_method == 'truncate_and_load':
        session.execute(text(f'TRUNCATE TABLE {full_table_name}'))
        session.commit()
        write_method = 'insert'  # After truncate, use insert method
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        if write_method == 'upsert' and primary_key:
            for record in batch:
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_MSSQL)
                placeholders = build_placeholder_list(columns)
                updates = ', '.join([
                    f'[{k}] = source.[{k}]' 
                    for k in columns if k != primary_key
                ])
                
                sql = f"""
                    MERGE {full_table_name} AS target
                    USING (SELECT {placeholders}) AS source ({columns_str})
                    ON target.[{primary_key}] = source.[{primary_key}]
                    WHEN MATCHED THEN UPDATE SET {updates}
                    WHEN NOT MATCHED THEN INSERT ({columns_str}) VALUES ({placeholders});
                """
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'insert' or write_method == 'append':
            for record in batch:
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_MSSQL)
                placeholders = build_placeholder_list(columns)
                sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
                session.execute(text(sql), record)
                inserted += 1
        elif write_method == 'replace':
            for record in batch:
                if primary_key and primary_key in record:
                    session.execute(
                        text(f'DELETE FROM {full_table_name} WHERE [{primary_key}] = :pk'),
                        {'pk': record[primary_key]}
                    )
                columns = list(record.keys())
                columns_str = build_column_list(columns, DB_MSSQL)
                placeholders = build_placeholder_list(columns)
                sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
                session.execute(text(sql), record)
                inserted += 1
        elif write_method == 'update' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                columns = list(record.keys())
                set_clause = ', '.join([f'[{k}] = :{k}' for k in columns if k != primary_key])
                sql = f"""
                    UPDATE {full_table_name}
                    SET {set_clause}
                    WHERE [{primary_key}] = :{primary_key}
                """
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'delete' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                sql = f'DELETE FROM {full_table_name} WHERE [{primary_key}] = :pk'
                session.execute(text(sql), {'pk': record[primary_key]})
                updated += 1
        
        session.commit()
    
    return {'inserted': inserted, 'updated': updated, 'total': len(data)}


def load_data_generic(
    data: List[Dict[str, Any]],
    session: Session,
    schema_name: str,
    table_name: str,
    write_method: str,
    primary_key: Optional[str],
    batch_size: int,
) -> Dict[str, Any]:
    """Generic load data using SQLAlchemy Table reflection (fallback)."""
    from sqlalchemy import Table, MetaData
    
    metadata = MetaData()
    try:
        table = Table(
            table_name,
            metadata,
            schema=schema_name,
            autoload_with=session.bind if hasattr(session, 'bind') else None
        )
    except Exception:
        # If table can't be autoloaded, use raw SQL
        return load_data_raw_sql(data, session, schema_name, table_name, write_method, primary_key, batch_size)
    
    inserted = 0
    updated = 0
    
    # Build table name for truncate operation
    full_table_name = f'"{schema_name}"."{table_name}"' if schema_name else f'"{table_name}"'
    
    # Handle truncate_and_load first (before processing data)
    if write_method == 'truncate_and_load':
        session.execute(text(f'TRUNCATE TABLE {full_table_name}'))
        session.commit()
        write_method = 'insert'  # After truncate, use insert method
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        if write_method == 'upsert' and primary_key:
            for record in batch:
                existing = session.query(table).filter(
                    getattr(table.c, primary_key) == record[primary_key]
                ).first()
                
                if existing:
                    for key, value in record.items():
                        setattr(existing, key, value)
                    updated += 1
                else:
                    session.add(table(**record))
                    inserted += 1
        elif write_method == 'insert' or write_method == 'append':
            for record in batch:
                session.add(table(**record))
                inserted += 1
        elif write_method == 'replace':
            for record in batch:
                if primary_key and primary_key in record:
                    existing = session.query(table).filter(
                        getattr(table.c, primary_key) == record[primary_key]
                    ).first()
                    if existing:
                        session.delete(existing)
                session.add(table(**record))
                inserted += 1
        elif write_method == 'update' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                existing = session.query(table).filter(
                    getattr(table.c, primary_key) == record[primary_key]
                ).first()
                if existing:
                    for key, value in record.items():
                        setattr(existing, key, value)
                    updated += 1
        elif write_method == 'delete' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                existing = session.query(table).filter(
                    getattr(table.c, primary_key) == record[primary_key]
                ).first()
                if existing:
                    session.delete(existing)
                    updated += 1
        
        session.commit()
    
    return {'inserted': inserted, 'updated': updated, 'total': len(data)}


def load_data_raw_sql(
    data: List[Dict[str, Any]],
    session: Session,
    schema_name: str,
    table_name: str,
    write_method: str,
    primary_key: Optional[str],
    batch_size: int,
) -> Dict[str, Any]:
    """Load data using raw SQL (fallback when table can't be autoloaded)."""
    full_table_name = f'"{schema_name}"."{table_name}"' if schema_name else f'"{table_name}"'
    inserted = 0
    updated = 0
    
    # Handle truncate_and_load first (before processing data)
    if write_method == 'truncate_and_load':
        session.execute(text(f'TRUNCATE TABLE {full_table_name}'))
        session.commit()
        write_method = 'insert'  # After truncate, use insert method
    
    if not data:
        return {'inserted': 0, 'updated': 0, 'total': 0}
    
    columns = list(data[0].keys())
    columns_str = build_column_list(columns, DB_POSTGRESQL)
    placeholders = build_placeholder_list(columns)
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        if write_method == 'insert' or write_method == 'append':
            for record in batch:
                sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
                session.execute(text(sql), record)
                inserted += 1
        elif write_method == 'update' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                set_clause = ', '.join([f'"{k}" = :{k}' for k in columns if k != primary_key])
                sql = f"""
                    UPDATE {full_table_name}
                    SET {set_clause}
                    WHERE "{primary_key}" = :{primary_key}
                """
                session.execute(text(sql), record)
                updated += 1
        elif write_method == 'delete' and primary_key:
            for record in batch:
                if primary_key not in record:
                    continue
                sql = f'DELETE FROM {full_table_name} WHERE "{primary_key}" = :pk'
                session.execute(text(sql), {'pk': record[primary_key]})
                updated += 1
        
        session.commit()
    
    return {'inserted': inserted, 'updated': updated, 'total': len(data)}


# Database-specific load function mapping
LOAD_FUNCTIONS = {
    DB_POSTGRESQL: load_data_postgresql,
    DB_MYSQL: load_data_mysql,
    DB_SQLITE: load_data_sqlite,
    DB_MSSQL: load_data_mssql,
}


def load_data(
    data: List[Dict[str, Any]],
    session: Session,
    schema_name: str,
    table_name: str,
    write_method: str,
    primary_key: Optional[str],
    batch_size: int,
    db_type: str,
) -> Dict[str, Any]:
    """
    Load data using database-specific methods.
    
    Args:
        data: Data to load
        session: Database session
        schema_name: Database schema name
        table_name: Target table name
        write_method: Write method (insert, upsert, replace, merge)
        primary_key: Primary key column name
        batch_size: Batch size for loading
        db_type: Database type (postgresql, mysql, sqlite, mssql)
        
    Returns:
        Loading statistics dictionary
    """
    load_func = LOAD_FUNCTIONS.get(db_type, load_data_generic)
    return load_func(
        data, session, schema_name, table_name, write_method, primary_key, batch_size
    )

