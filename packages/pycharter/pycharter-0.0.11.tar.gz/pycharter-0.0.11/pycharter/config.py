"""
Configuration management for PyCharter.

Follows Airflow's pattern for database configuration:
- Environment variables: PYCHARTER__DATABASE__SQL_ALCHEMY_CONN
- Config file: pycharter.cfg with [database] section
- Fallback: PYCHARTER_DATABASE_URL (simpler alternative)
"""

import os
from configparser import ConfigParser
from pathlib import Path
from typing import Optional


def get_database_url() -> Optional[str]:
    """
    Get database URL from configuration.

    Priority order:
    1. Environment variable: PYCHARTER__DATABASE__SQL_ALCHEMY_CONN (Airflow-style)
    2. Environment variable: PYCHARTER_DATABASE_URL (simpler)
    3. Config file: pycharter.cfg [database] sql_alchemy_conn
    4. Config file: alembic.ini sqlalchemy.url

    Returns:
        Database connection string, or None if not found
    """
    # 1. Try Airflow-style environment variable
    db_url = os.getenv("PYCHARTER__DATABASE__SQL_ALCHEMY_CONN")
    if db_url:
        return db_url

    # 2. Try simpler environment variable
    db_url = os.getenv("PYCHARTER_DATABASE_URL")
    if db_url:
        return db_url

    # 3. Try pycharter.cfg config file
    config_file = _find_config_file("pycharter.cfg")
    if config_file:
        config = ConfigParser()
        config.read(config_file)
        if config.has_section("database"):
            db_url = config.get("database", "sql_alchemy_conn", fallback=None)
            if db_url:
                return db_url

    # 4. Try alembic.ini
    alembic_ini = _find_config_file("alembic.ini")
    if alembic_ini:
        config = ConfigParser()
        config.read(alembic_ini)
        db_url = config.get("alembic", "sqlalchemy.url", fallback=None)
        if (
            db_url and db_url != "driver://user:pass@localhost/dbname"
        ):  # Skip default placeholder
            return db_url

    return None


def _find_config_file(filename: str) -> Optional[Path]:
    """
    Find config file in common locations.

    Search order:
    1. Current working directory
    2. User home directory (~/.pycharter/)
    3. Project root (where alembic.ini is)

    Args:
        filename: Name of config file to find

    Returns:
        Path to config file, or None if not found
    """
    # 1. Current working directory
    cwd_path = Path.cwd() / filename
    if cwd_path.exists():
        return cwd_path

    # 2. User home directory
    home_path = Path.home() / ".pycharter" / filename
    if home_path.exists():
        return home_path

    # 3. Project root (where alembic.ini typically is)
    # Try to find by looking for alembic.ini
    current = Path.cwd()
    for _ in range(5):  # Look up to 5 levels up
        alembic_path = current / "alembic.ini"
        if alembic_path.exists():
            config_path = current / filename
            if config_path.exists():
                return config_path
        current = current.parent

    return None


def set_database_url(database_url: str) -> None:
    """
    Set database URL in environment variable.

    Args:
        database_url: Database connection string
    """
    os.environ["PYCHARTER_DATABASE_URL"] = database_url


def get_config_variable(var_name: str, section: str = "variables") -> Optional[str]:
    """
    Get variable value from pycharter.cfg config file.
    
    Reads from the specified section (default: [variables]) in pycharter.cfg.
    This is used by the value injection engine to resolve variables from config files.
    
    Priority order:
    1. [variables] section (if section="variables")
    2. [etl] section (if section="etl")
    3. Other specified section
    
    Args:
        var_name: Variable name to look up
        section: Config file section to read from (default: "variables")
        
    Returns:
        Variable value from config file, or None if not found
        
    Example:
        >>> # In pycharter.cfg:
        >>> # [variables]
        >>> # FMP_API_KEY = your_api_key_here
        >>> value = get_config_variable("FMP_API_KEY")
        >>> # Returns: "your_api_key_here"
    """
    config_file = _find_config_file("pycharter.cfg")
    if not config_file:
        return None
    
    try:
        config = ConfigParser()
        config.read(config_file)
        
        if config.has_section(section):
            value = config.get(section, var_name, fallback=None)
            return value
    except Exception:
        # Silently fail if config file can't be read
        pass
    
    return None
