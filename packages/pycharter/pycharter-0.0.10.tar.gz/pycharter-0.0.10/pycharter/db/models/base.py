"""
Base SQLAlchemy configuration
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateTable

Base = declarative_base()


def get_engine(connection_string: str):
    """
    Create SQLAlchemy engine from connection string.
    
    For SQLite, configures the engine to handle schema references properly.
    SQLite doesn't support schemas, so we need to ensure schema prefixes
    are ignored when creating tables and foreign keys.
    """
    # For SQLite, we need special handling
    if connection_string.startswith("sqlite://"):
        # SQLite-specific configuration
        # This ensures that schema references in table_args are ignored
        engine = create_engine(
            connection_string,
            echo=False,
            connect_args={"check_same_thread": False} if connection_string != "sqlite:///:memory:" else {},
        )
        
        # Add event listener to handle schema references for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Set SQLite pragmas for better compatibility."""
            cursor = dbapi_conn.cursor()
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        # Override table compilation to remove schema for SQLite
        @event.listens_for(engine, "before_cursor_execute", retval=True)
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Remove schema prefixes from SQL statements for SQLite."""
            if connection_string.startswith("sqlite://"):
                # Replace "pycharter." schema prefix with empty string
                statement = statement.replace('"pycharter".', "").replace("pycharter.", "")
            return statement, parameters
        
        return engine
    else:
        return create_engine(connection_string, echo=False)


def get_session(connection_string: str):
    """Create SQLAlchemy session from connection string."""
    engine = get_engine(connection_string)
    Session = sessionmaker(bind=engine)
    return Session()
