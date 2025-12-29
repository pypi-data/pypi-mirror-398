"""
CLI commands for database management (pycharter db init, pycharter db upgrade)

Following Airflow's pattern: airflow db init, airflow db upgrade
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore[import-untyped]
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect, text
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False

from pycharter.config import get_database_url, set_database_url
from pycharter.db.models import DomainModel, OwnerModel, SystemModel
from pycharter.db.models.base import Base, get_session


# Helper functions
def _require_alembic() -> None:
    """Raise error if Alembic is not available."""
    if not ALEMBIC_AVAILABLE:
        raise ImportError("alembic and sqlalchemy are required. Install with: pip install alembic sqlalchemy")


def _get_db_url(database_url: Optional[str] = None, required: bool = True) -> Optional[str]:
    """
    Get database URL from argument or configuration.
    
    Defaults to SQLite (sqlite:///pycharter.db) if no database URL is provided.
    """
    db_url = database_url or get_database_url() or os.getenv("PYCHARTER_DATABASE_URL")
    
    # Default to SQLite if no database URL is configured
    if not db_url:
        default_db_path = Path.cwd() / "pycharter.db"
        db_url = f"sqlite:///{default_db_path}"
        if required:
            print(f"ℹ Using default SQLite database: {db_url}")
    
    return db_url


def _get_migrations_dir() -> Path:
    """Find migrations directory relative to installed package."""
    try:
        import pycharter
        migrations_dir = Path(pycharter.__file__).parent / "db" / "migrations"
    except (ImportError, AttributeError):
        migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    
    if not migrations_dir.exists():
        cwd_migrations = Path(os.getcwd()) / "pycharter" / "db" / "migrations"
        if cwd_migrations.exists():
            return cwd_migrations
        raise FileNotFoundError(
            f"Migrations directory not found. Tried:\n  - {migrations_dir}\n  - {cwd_migrations}"
        )
    return migrations_dir


def get_alembic_config(database_url: Optional[str] = None) -> Config:
    """
    Get Alembic configuration programmatically (like Airflow).
    
    Defaults to SQLite (sqlite:///pycharter.db) if no database URL is provided.
    """
    config = Config()
    config.set_main_option("script_location", str(_get_migrations_dir()))
    config.set_main_option("prepend_sys_path", ".")
    config.set_main_option("version_path_separator", "os")
    config.set_main_option(
        "file_template",
        "%%(year)d%%(month).2d%%(day).2d%%(hour).2d%%(minute).2d%%(second).2d_%%(rev)s_%%(slug)s"
    )
    
    db_url = database_url or get_database_url() or os.getenv("PYCHARTER_DATABASE_URL")
    
    # Default to SQLite if no database URL is configured
    if not db_url:
        default_db_path = Path.cwd() / "pycharter.db"
        db_url = f"sqlite:///{default_db_path}"
    
    config.set_main_option("sqlalchemy.url", db_url)
    set_database_url(db_url)
    
    return config


def _detect_db_type(database_url: str) -> str:
    """Auto-detect database type from connection string."""
    if database_url.startswith(("mongodb://", "mongodb+srv://")):
        return "mongodb"
    elif database_url.startswith(("postgresql://", "postgres://")):
        return "postgresql"
    elif database_url.startswith("sqlite://"):
        return "sqlite"
    # Default to SQLite (since we default to SQLite when no URL is provided)
    return "sqlite"


def _cleanup_stale_alembic_version(engine) -> None:
    """
    Remove stale alembic_version table from pycharter schema (where it should be).
    Also removes from public schema if found (shouldn't happen, but cleanup is safe).
    This ensures we only work with pycharter schema going forward.
    """
    with engine.connect() as conn:
        # Drop from pycharter schema (where it should be)
        try:
            conn.execute(text('DROP TABLE IF EXISTS "pycharter".alembic_version CASCADE'))
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        
        # Also clean up from public schema if it exists (shouldn't happen, but safe to remove)
        # This ensures public schema is untouched by PyCharter
        try:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass


def _check_and_cleanup_invalid_alembic_version(engine, config) -> bool:
    """
    Check if alembic_version exists in pycharter schema and has a valid revision.
    If found in public schema, warns and cleans it up (we only work with pycharter schema).
    If it exists but revision is invalid, clean it up.
    Returns True if alembic_version exists in pycharter schema and is valid, False otherwise.
    """
    # Only check pycharter schema (where it should be)
    has_alembic_version = False
    db_revision = None
    
    try:
        with engine.connect() as conn:
            # Check pycharter schema (where Alembic should put it)
            try:
                result = conn.execute(text('SELECT version_num FROM "pycharter".alembic_version LIMIT 1'))
                db_revision = result.fetchone()
                has_alembic_version = True
            except Exception:
                # Table doesn't exist in pycharter schema - this is fine
                # Check if it exists in public schema (shouldn't happen, but clean it up if found)
                try:
                    result = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                    db_revision = result.fetchone()
                    print("⚠ Warning: Found alembic_version in public schema (should be in pycharter schema)")
                    print("   Cleaning up from public schema...")
                    _cleanup_stale_alembic_version(engine)
                    return False  # Don't use public schema version
                except Exception:
                    # Table doesn't exist anywhere - this is fine
                    return False
    except Exception:
        # Can't check - assume it doesn't exist
        return False
    
    if not has_alembic_version:
        return False
    
    # We found alembic_version in pycharter schema - check if revision is valid
    if not db_revision or not db_revision[0]:
        # Table exists but is empty - safe to drop
        print("ℹ Found empty alembic_version table in pycharter schema, cleaning up...")
        _cleanup_stale_alembic_version(engine)
        return False
    
    # Check if revision exists in migration files
    try:
        from alembic.script import ScriptDirectory
        script = ScriptDirectory.from_config(config)
        script.get_revision(db_revision[0])
        # Revision is valid
        return True
    except Exception:
        # Revision is invalid - clean it up
        print(f"ℹ Found stale alembic_version with invalid revision '{db_revision[0]}' in pycharter schema")
        print("   Cleaning up stale alembic_version table...")
        _cleanup_stale_alembic_version(engine)
        return False


# Command functions
def cmd_init(database_url: Optional[str] = None, db_type: Optional[str] = None, force: bool = False) -> int:
    """Initialize the database schema from scratch."""
    try:
        db_url = _get_db_url(database_url)
        if not db_url:
            return 1
        
        db_type = db_type or _detect_db_type(db_url)
        if db_type == "mongodb":
            return _init_mongodb(db_url, force)
        elif db_type == "sqlite":
            return _init_sqlite(db_url, force)
        else:
            return _init_postgresql(db_url, force)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _init_mongodb(database_url: str, force: bool = False) -> int:
    """Initialize MongoDB database (create indexes)."""
    try:
        from pycharter.metadata_store.mongodb import MongoDBMetadataStore
        
        database_name = "pycharter"
        if "/" in database_url.split("@")[-1]:
            db_part = database_url.split("/")[-1].split("?")[0]
            if db_part and db_part != database_url.split("@")[-1]:
                database_name = db_part
        
        print(f"Initializing MongoDB database: {database_name}")
        store = MongoDBMetadataStore(connection_string=database_url, database_name=database_name)
        store.connect(ensure_indexes=True)
        print("✓ MongoDB initialized successfully!")
        store.disconnect()
        return 0
    except ImportError:
        print("❌ Error: pymongo is required. Install with: pip install pymongo")
        return 1
    except Exception as e:
        print(f"❌ Error initializing MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _init_sqlite(database_url: str, force: bool = False) -> int:
    """Initialize SQLite database."""
    _require_alembic()
    
    try:
        db_path = database_url[10:] if database_url.startswith("sqlite:///") else database_url
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        engine = create_engine(database_url)
        existing_tables = inspect(engine).get_table_names()
        
        if existing_tables and not force:
            print(f"⚠ Warning: Database already contains {len(existing_tables)} tables.")
            print("   Use --force to reinitialize, or run 'pycharter db upgrade' to apply migrations.")
            return 1
        
        Base.metadata.create_all(engine)
        print("✓ Created tables using SQLAlchemy models")
        
        versions_dir = Path(__file__).parent.parent / "migrations" / "versions"
        if versions_dir.exists() and any(versions_dir.iterdir()):
            set_database_url(database_url)
            config = get_alembic_config(database_url)
            command.upgrade(config, "head")
            print("✓ Migrations complete")
        
        print("✓ SQLite initialization complete!")
        return 0
    except Exception as e:
        print(f"❌ Error initializing SQLite: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _init_postgresql(database_url: str, force: bool = False) -> int:
    """Initialize PostgreSQL database - simple and straightforward like Airflow."""
    _require_alembic()
    
    try:
        set_database_url(database_url)
        config = get_alembic_config(database_url)
        engine = create_engine(database_url)
        
        # Create schema
        with engine.connect() as conn:
            conn.execute(text('CREATE SCHEMA IF NOT EXISTS "pycharter"'))
            conn.commit()
        print("✓ Created 'pycharter' schema (if it didn't exist)")
        
        # Run migrations - that's it!
        print("Running migrations to initialize database...")
        command.upgrade(config, "head")
        print("✓ Database initialized successfully!")
        return 0
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_upgrade(database_url: Optional[str] = None, revision: str = "head") -> int:
    """Upgrade database to the latest revision."""
    _require_alembic()
    
    try:
        db_url = _get_db_url(database_url)
        if not db_url:
            return 1
        
        if database_url:
            set_database_url(database_url)
        
        config = get_alembic_config(db_url)
        print(f"Upgrading database to revision: {revision}...")
        command.upgrade(config, revision)
        print("✓ Database upgraded successfully!")
        return 0
    except Exception as e:
        print(f"❌ Error upgrading database: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_downgrade(database_url: Optional[str] = None, revision: str = "-1") -> int:
    """Downgrade database to a previous revision."""
    _require_alembic()
    
    try:
        db_url = _get_db_url(database_url)
        if not db_url:
            return 1
        
        if database_url:
            set_database_url(database_url)
        
        config = get_alembic_config(db_url)
        print(f"Downgrading database to revision: {revision}...")
        command.downgrade(config, revision)
        print("✓ Database downgraded successfully!")
        return 0
    except Exception as e:
        print(f"❌ Error downgrading database: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_current(database_url: Optional[str] = None) -> int:
    """Show current database revision."""
    _require_alembic()
    
    try:
        db_url = _get_db_url(database_url)
        if not db_url:
            return 1
        
        if database_url:
            set_database_url(database_url)
        
        # Check alembic_version directly in pycharter schema
        engine = create_engine(db_url)
        with engine.connect() as connection:
            try:
                result = connection.execute(text('SELECT version_num FROM "pycharter".alembic_version LIMIT 1'))
                version = result.fetchone()
                if version:
                    print(f"Current database revision: {version[0]}")
                    return 0
            except Exception:
                pass
            
            # Fallback: try MigrationContext (might not work if schema isn't configured)
            from alembic.runtime.migration import MigrationContext
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            if current_rev:
                print(f"Current database revision: {current_rev}")
                return 0
        
        print("Database is not initialized. Run 'pycharter db init' first.")
        return 1
    except Exception as e:
        print(f"❌ Error getting current revision: {e}")
        return 1


def cmd_stamp(database_url: Optional[str] = None, revision: str = "head") -> int:
    """Stamp the database with a specific revision without running migrations."""
    _require_alembic()
    
    try:
        db_url = _get_db_url(database_url)
        if not db_url:
            return 1
        
        if database_url:
            set_database_url(database_url)
        
        config = get_alembic_config(db_url)
        print(f"Stamping database with revision: {revision}...")
        command.stamp(config, revision)
        print(f"✓ Database stamped successfully with revision: {revision}")
        return 0
    except Exception as e:
        print(f"❌ Error stamping database: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_history(database_url: Optional[str] = None) -> int:
    """Show migration history."""
    _require_alembic()
    
    try:
        if database_url:
            set_database_url(database_url)
        config = get_alembic_config()
        command.history(config)
        return 0
    except Exception as e:
        print(f"❌ Error showing history: {e}")
        return 1


def _seed_model(session, model_class, seed_file: Path, model_name: str, id_field: str = "id") -> int:
    """Generic function to seed a model from YAML file."""
    if not seed_file.exists():
        print(f"⚠ No {seed_file.name} file found, skipping {model_name}")
        return 0
    
    print(f"Loading {model_name}...")
    with open(seed_file, "r") as f:
        data = yaml.safe_load(f) or []
    
    count = 0
    for item_data in data:
        item_id = item_data.get(id_field)
        if not item_id:
            print(f"⚠ Warning: Skipping {model_name} entry without '{id_field}' field")
            continue
        
        existing = session.query(model_class).filter_by(**{id_field: item_id}).first()
        if existing:
            for key, value in item_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            print(f"  Updated {model_name}: {item_id}")
        else:
            item = model_class(**item_data)
            session.add(item)
            print(f"  Created {model_name}: {item_id}")
        count += 1
    
    session.commit()
    print(f"✓ Loaded {count} {model_name}(s)")
    return count


def cmd_seed(seed_dir: Optional[str] = None, database_url: Optional[str] = None) -> int:
    """Seed the database with initial data from YAML files."""
    if not YAML_AVAILABLE:
        print("❌ Error: PyYAML is required. Install with: pip install pyyaml")
        return 1
    
    try:
        # Handle swapped arguments
        if seed_dir and any(seed_dir.startswith(prefix) for prefix in 
                           ("postgresql://", "postgres://", "mysql://", "sqlite://", "mongodb://", "mongodb+srv://")):
            database_url, seed_dir = seed_dir, None
        
        db_url = _get_db_url(database_url)
        if not db_url:
            return 1
        
        # Determine seed directory
        if seed_dir:
            seed_path = Path(seed_dir)
        else:
            project_root = Path(__file__).resolve().parent.parent.parent
            seed_path = project_root / "data" / "seed"
        
        if not seed_path.exists():
            print(f"❌ Error: Seed directory not found: {seed_path}")
            return 1
        
        print(f"Loading seed data from: {seed_path}")
        
        if db_url.startswith(("mongodb://", "mongodb+srv://")):
            return _seed_mongodb(seed_path, db_url)
        else:
            return _seed_postgresql(seed_path, db_url)
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _seed_postgresql(seed_path: Path, db_url: str) -> int:
    """Seed PostgreSQL database with data from YAML files."""
    _require_alembic()
    
    session = get_session(db_url)
    try:
        _seed_model(session, OwnerModel, seed_path / "owners.yaml", "owners")
        _seed_model(session, DomainModel, seed_path / "domains.yaml", "domains", "name")
        _seed_model(session, SystemModel, seed_path / "systems.yaml", "systems", "name")
        print("\n✓ Seed data loaded successfully!")
        return 0
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def _seed_mongodb(seed_path: Path, db_url: str) -> int:
    """Seed MongoDB database with data from YAML files."""
    try:
        from datetime import datetime
        from bson import ObjectId
        from pymongo import MongoClient
        
        database_name = "pycharter"
        if "/" in db_url.rsplit("@", 1)[-1]:
            database_name = db_url.rsplit("/", 1)[-1].split("?")[0]
        
        client = MongoClient(db_url)
        db = client[database_name]
        
        try:
            for collection_name, model_name, id_field in [
                ("owners", "owners", "id"),
                ("domains", "domains", "name"),
                ("systems", "systems", "name"),
            ]:
                seed_file = seed_path / f"{collection_name}.yaml"
                if not seed_file.exists():
                    print(f"⚠ No {seed_file.name} file found, skipping {model_name}")
                    continue
                
                print(f"Loading {model_name}...")
                with open(seed_file, "r") as f:
                    data = yaml.safe_load(f) or []
                
                collection = db[collection_name]
                count_created = count_updated = 0
                now = datetime.utcnow()
                
                for item_data in data:
                    item_id = item_data.get(id_field)
                    if not item_id:
                        print(f"⚠ Warning: Skipping {model_name} entry without '{id_field}' field")
                        continue
                    
                    existing = collection.find_one({id_field: item_id})
                    doc = dict(item_data)
                    
                    if existing:
                        doc["updated_at"] = now
                        doc["created_at"] = existing.get("created_at", now)
                        collection.update_one({id_field: item_id}, {"$set": doc})
                        count_updated += 1
                    else:
                        if collection_name != "owners":
                            doc["_id"] = ObjectId()
                        doc["created_at"] = doc["updated_at"] = now
                        collection.insert_one(doc)
                        count_created += 1
                
                print(f"✓ Loaded {len(data)} {model_name}(s) ({count_created} created, {count_updated} updated)")
            
            print("\n✓ Seed data loaded successfully!")
            return 0
        finally:
            client.close()
    except ImportError:
        print("❌ Error: pymongo is required. Install with: pip install pymongo")
        return 1
    except Exception as e:
        print(f"❌ Error seeding MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_truncate(database_url: Optional[str] = None, force: bool = False) -> int:
    """Truncate all PyCharter database tables."""
    _require_alembic()
    
    try:
        db_url = _get_db_url(database_url)
        if not db_url:
            return 1
        
        if database_url:
            set_database_url(database_url)
        
        engine = create_engine(db_url)
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names(schema="pycharter"))
        
        # Tables to truncate in order
        tables = [
            "metadata_record_business_owners", "metadata_record_bu_sme",
            "metadata_record_it_application_owners", "metadata_record_it_sme",
            "metadata_record_support_lead", "metadata_record_system_pulls",
            "metadata_record_system_pushes", "metadata_record_system_sources",
            "metadata_record_domains", "coercion_rules", "validation_rules",
            "schemas", "metadata_records", "data_contracts", "owners", "systems", "domains"
        ]
        
        existing_tables_to_truncate = [t for t in tables if t in existing_tables]
        
        if not existing_tables_to_truncate:
            print("⚠ No PyCharter tables found to truncate.")
            return 0
        
        print(f"\n⚠ WARNING: This will truncate {len(existing_tables_to_truncate)} table(s):")
        print(f"   {', '.join(existing_tables_to_truncate)}")
        print("\n⚠ ALL DATA IN THESE TABLES WILL BE PERMANENTLY DELETED!")
        
        if not force:
            try:
                confirmation = input("\nType 'yes' to confirm: ").strip().lower()
                if confirmation not in ["yes", "y"]:
                    print("❌ Truncate cancelled.")
                    return 1
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Truncate cancelled.")
                return 1
        
        with engine.begin() as conn:
            conn.execute(text("SET session_replication_role = 'replica'"))
            for table in existing_tables_to_truncate:
                conn.execute(text(f'TRUNCATE TABLE pycharter."{table}" CASCADE'))
                print(f"  ✓ Truncated {table}")
            conn.execute(text("SET session_replication_role = 'origin'"))
        
        print("\n✓ Successfully truncated all existing PyCharter tables!")
        return 0
    except Exception as e:
        print(f"❌ Error truncating database: {e}")
        import traceback
        traceback.print_exc()
        return 1






def main():
    """Main CLI entry point for pycharter db commands."""
    parser = argparse.ArgumentParser(
        description="PyCharter database management commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # init
    init_parser = subparsers.add_parser("init", help="Initialize database schema from scratch")
    init_parser.add_argument("database_url", nargs="?", help="Database connection string (defaults to sqlite:///pycharter.db)")
    init_parser.add_argument("--db", "--database-type", dest="db_type", 
                            choices=["postgresql", "postgres", "mongodb", "sqlite"],
                            default=None, help="Database type (auto-detected from URL if not provided)")
    init_parser.add_argument("--force", action="store_true", help="Proceed even if initialized")
    
    # upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database to latest revision")
    upgrade_parser.add_argument("database_url", nargs="?", help="Database connection string")
    upgrade_parser.add_argument("--revision", default="head", help="Target revision")
    
    # downgrade
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument("database_url", nargs="?", help="Database connection string")
    downgrade_parser.add_argument("--revision", default="-1", help="Target revision")
    
    # current
    current_parser = subparsers.add_parser("current", help="Show current database revision")
    current_parser.add_argument("database_url", nargs="?", help="Database connection string")
    
    # history
    history_parser = subparsers.add_parser("history", help="Show migration history")
    history_parser.add_argument("database_url", nargs="?", help="Database connection string")
    
    # stamp
    stamp_parser = subparsers.add_parser("stamp", help="Stamp database with revision")
    stamp_parser.add_argument("revision", nargs="?", default="head", help="Revision to stamp")
    stamp_parser.add_argument("database_url", nargs="?", help="Database connection string")
    
    # seed
    seed_parser = subparsers.add_parser("seed", help="Seed database with initial data")
    seed_parser.add_argument("seed_dir", nargs="?", help="Directory with seed YAML files")
    seed_parser.add_argument("database_url", nargs="?", help="Database connection string")
    
    # truncate
    truncate_parser = subparsers.add_parser("truncate", help="Truncate all tables")
    truncate_parser.add_argument("database_url", nargs="?", help="Database connection string")
    truncate_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        "init": lambda: cmd_init(args.database_url, db_type=args.db_type, force=args.force),
        "upgrade": lambda: cmd_upgrade(args.database_url, args.revision),
        "downgrade": lambda: cmd_downgrade(args.database_url, args.revision),
        "current": lambda: cmd_current(args.database_url),
        "history": lambda: cmd_history(args.database_url),
        "stamp": lambda: cmd_stamp(args.database_url, args.revision),
        "seed": lambda: cmd_seed(args.seed_dir, args.database_url),
        "truncate": lambda: cmd_truncate(args.database_url, force=args.force),
    }
    
    return commands.get(args.command, lambda: (parser.print_help(), 1)[1])()


if __name__ == "__main__":
    sys.exit(main())
