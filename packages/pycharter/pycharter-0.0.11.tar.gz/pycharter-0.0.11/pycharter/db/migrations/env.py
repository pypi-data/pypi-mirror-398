from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from pycharter.db.models import (  # GovernanceRuleModel removed - governance rules stored as JSON in metadata_records
    CoercionRuleModel,
    DataContractModel,
    DomainModel,
    MetadataRecordBusinessOwner,
    MetadataRecordBUSME,
    MetadataRecordDomain,
    MetadataRecordITApplicationOwner,
    MetadataRecordITSME,
    MetadataRecordModel,
    MetadataRecordSupportLead,
    MetadataRecordSystemPull,
    MetadataRecordSystemPush,
    MetadataRecordSystemSource,
    OwnerModel,
    SchemaModel,
    SystemModel,
    ValidationRuleModel,
)

# add your model's MetaData object here
# for 'autogenerate' support
from pycharter.db.models.base import Base

# Import all models so Alembic can detect them
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get URL from environment variable or config
    import os

    url = os.getenv("PYCHARTER_DATABASE_URL") or config.get_main_option(
        "sqlalchemy.url"
    )
    
    # Determine if this is PostgreSQL (has schemas) or SQLite (no schemas)
    # For PostgreSQL, use "pycharter" schema; for SQLite, use None
    version_table_schema = None
    if url and url.startswith(("postgresql://", "postgres://")):
        version_table_schema = "pycharter"
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=version_table_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get URL from environment variable or config
    import os

    database_url = os.getenv("PYCHARTER_DATABASE_URL")
    if database_url:
        # Override config with environment variable
        configuration = config.get_section(config.config_ini_section, {})
        configuration["sqlalchemy.url"] = database_url
    else:
        configuration = config.get_section(config.config_ini_section, {})
    
    # Get the actual URL for schema detection
    url = database_url or configuration.get("sqlalchemy.url", "")
    
    # Determine if this is PostgreSQL (has schemas) or SQLite (no schemas)
    # For PostgreSQL, use "pycharter" schema; for SQLite, use None
    version_table_schema = None
    if url and url.startswith(("postgresql://", "postgres://")):
        version_table_schema = "pycharter"

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=version_table_schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
