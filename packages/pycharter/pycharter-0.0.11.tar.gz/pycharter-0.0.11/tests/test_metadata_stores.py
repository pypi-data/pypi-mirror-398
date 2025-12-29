#!/usr/bin/env python3
"""
Test script for all metadata store implementations.

Tests InMemory, MongoDB, PostgreSQL, and Redis implementations.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pycharter import (
    InMemoryMetadataStore,
    MongoDBMetadataStore,
    PostgresMetadataStore,
    RedisMetadataStore,
    parse_contract,
)


def test_in_memory_store():
    """Test InMemoryMetadataStore."""
    print("=" * 70)
    print("Testing InMemoryMetadataStore")
    print("=" * 70)

    try:
        store = InMemoryMetadataStore()
        store.connect()
        print("✓ Connected to in-memory store")

        # Test schema storage
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name"],
        }
        schema_id = store.store_schema("test_user", schema, version="1.0")
        print(f"✓ Stored schema (ID: {schema_id})")

        # Test schema retrieval
        retrieved_schema = store.get_schema(schema_id)
        assert retrieved_schema == schema, "Schema mismatch"
        print("✓ Retrieved schema matches")

        # Test ownership and governance rules via metadata
        metadata = {
            "title": "Test Schema Metadata",
            "business_owners": ["test-user@example.com"],
            "governance_rules": {"test_rule": {"type": "validation", "enabled": True}},
        }
        store.store_metadata(schema_id, metadata)
        retrieved_metadata = store.get_metadata(schema_id)
        assert retrieved_metadata["business_owners"] == ["test-user@example.com"]
        assert "test_rule" in retrieved_metadata["governance_rules"]
        print("✓ Stored and retrieved ownership and governance rules via metadata")

        # Test list schemas
        schemas = store.list_schemas()
        assert len(schemas) == 1
        print(f"✓ Listed schemas ({len(schemas)} found)")

        # Test metadata
        store.store_metadata(schema_id, {"description": "Test schema"})
        metadata = store.get_metadata(schema_id)
        assert metadata["description"] == "Test schema"
        print("✓ Stored and retrieved metadata")

        store.disconnect()
        print("\n✓ InMemoryMetadataStore: ALL TESTS PASSED\n")
        return True

    except Exception as e:
        print(f"✗ InMemoryMetadataStore test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_mongodb_store():
    """Test MongoDBMetadataStore."""
    print("=" * 70)
    print("Testing MongoDBMetadataStore")
    print("=" * 70)

    if MongoDBMetadataStore is None:
        print("✗ MongoDBMetadataStore not available (pymongo not installed)")
        return False

    try:
        # Try to connect to local MongoDB
        # Docker MongoDB connection (username: rootUser, password: rootPassword)
        store = MongoDBMetadataStore(
            connection_string="mongodb://rootUser:rootPassword@localhost:27017",
            database_name="pycharter_test",
        )
        store.connect()
        print("✓ Connected to MongoDB")

        # Clean up test data (optional)
        if hasattr(store, "_db"):
            store._db.schemas.delete_many({})
            store._db.governance_rules.delete_many({})
            store._db.ownership.delete_many({})
            store._db.metadata.delete_many({})
            store._db.coercion_rules.delete_many({})
            store._db.validation_rules.delete_many({})
            print("✓ Cleaned up test data")

        # Test schema storage
        schema = {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "price": {"type": "number"},
            },
        }
        schema_id = store.store_schema("test_product", schema, version="1.0")
        print(f"✓ Stored schema (ID: {schema_id})")

        # Test schema retrieval
        retrieved_schema = store.get_schema(schema_id)
        assert retrieved_schema == schema, "Schema mismatch"
        print("✓ Retrieved schema matches")

        # Test ownership and governance rules via metadata
        metadata = {
            "title": "Product Schema Metadata",
            "business_owners": ["product-team@example.com"],
            "governance_rules": {
                "pii_rule": {"type": "encrypt", "fields": ["product_id"]}
            },
        }
        store.store_metadata(schema_id, metadata)
        retrieved_metadata = store.get_metadata(schema_id)
        assert "product-team@example.com" in retrieved_metadata.get(
            "business_owners", []
        )
        assert "pii_rule" in retrieved_metadata.get("governance_rules", {})
        print("✓ Stored and retrieved ownership and governance rules via metadata")

        # Test list schemas
        schemas = store.list_schemas()
        assert len(schemas) >= 1
        print(f"✓ Listed schemas ({len(schemas)} found)")

        # Test coercion rules
        coercion_rules = {"price": "coerce_to_float"}
        store.store_coercion_rules(schema_id, coercion_rules, version="1.0")
        retrieved_coercion = store.get_coercion_rules(schema_id, version="1.0")
        assert retrieved_coercion == coercion_rules
        print("✓ Stored and retrieved coercion rules")

        # Test validation rules
        validation_rules = {"price": {"is_positive": {}}}
        store.store_validation_rules(schema_id, validation_rules, version="1.0")
        retrieved_validation = store.get_validation_rules(schema_id, version="1.0")
        assert retrieved_validation == validation_rules
        print("✓ Stored and retrieved validation rules")

        # Test metadata
        store.store_metadata(schema_id, {"description": "Product schema"})
        metadata = store.get_metadata(schema_id)
        assert metadata["description"] == "Product schema"
        print("✓ Stored and retrieved metadata")

        store.disconnect()
        print("\n✓ MongoDBMetadataStore: ALL TESTS PASSED\n")
        return True

    except Exception as e:
        print(f"✗ MongoDBMetadataStore test failed: {e}")
        print("  Make sure MongoDB is running: docker ps | grep mongo")
        import traceback

        traceback.print_exc()
        return False


def test_postgres_store():
    """Test PostgresMetadataStore."""
    print("=" * 70)
    print("Testing PostgresMetadataStore")
    print("=" * 70)

    if PostgresMetadataStore is None:
        print("✗ PostgresMetadataStore not available (psycopg2 not installed)")
        return False

    try:
        # Try to connect to local PostgreSQL
        # Docker PostgreSQL connection (password from container env: 1234567890)
        store = PostgresMetadataStore(
            connection_string="postgresql://postgres:1234567890@localhost:5432/postgres"
        )
        store.connect()
        print("✓ Connected to PostgreSQL")

        # Test schema storage
        schema = {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "total": {"type": "number", "minimum": 0},
            },
            "required": ["order_id", "total"],
        }
        schema_id = store.store_schema("test_order", schema, version="1.0")
        print(f"✓ Stored schema (ID: {schema_id})")

        # Test schema retrieval
        retrieved_schema = store.get_schema(schema_id)
        assert retrieved_schema == schema, "Schema mismatch"
        print("✓ Retrieved schema matches")

        # Test ownership and governance rules via metadata
        metadata = {
            "title": "Order Schema Metadata",
            "business_owners": ["orders-team@example.com"],
            "governance_rules": {"retention_rule": {"type": "retention", "days": 365}},
        }
        store.store_metadata(schema_id, metadata)
        retrieved_metadata = store.get_metadata(schema_id)
        assert "orders-team@example.com" in retrieved_metadata.get(
            "business_owners", []
        )
        assert "retention_rule" in retrieved_metadata.get("governance_rules", {})
        print("✓ Stored and retrieved ownership and governance rules via metadata")

        # Test list schemas
        schemas = store.list_schemas()
        assert len(schemas) >= 1
        print(f"✓ Listed schemas ({len(schemas)} found)")

        # Test metadata
        store.store_metadata(schema_id, {"description": "Order schema"})
        metadata = store.get_metadata(schema_id)
        assert metadata["description"] == "Order schema"
        print("✓ Stored and retrieved metadata")

        store.disconnect()
        print("\n✓ PostgresMetadataStore: ALL TESTS PASSED\n")
        return True

    except Exception as e:
        print(f"✗ PostgresMetadataStore test failed: {e}")
        print("  Make sure PostgreSQL is running: docker ps | grep postgres")
        print(
            "  Connection string: postgresql://postgres:postgres@localhost:5432/postgres"
        )
        print(
            "  You may need to adjust the connection string based on your Docker setup"
        )
        import traceback

        traceback.print_exc()
        return False


def test_redis_store():
    """Test RedisMetadataStore."""
    print("=" * 70)
    print("Testing RedisMetadataStore")
    print("=" * 70)

    if RedisMetadataStore is None:
        print("✗ RedisMetadataStore not available (redis not installed)")
        return False

    try:
        # Try to connect to local Redis
        store = RedisMetadataStore(
            connection_string="redis://localhost:6379/0", key_prefix="pycharter_test"
        )
        store.connect()
        print("✓ Connected to Redis")

        # Clean up test keys (optional)
        if hasattr(store, "_client"):
            keys = store._client.keys("pycharter_test:*")
            if keys:
                store._client.delete(*keys)
                print("✓ Cleaned up test keys")

        # Test schema storage
        schema = {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "email": {"type": "string", "pattern": "^[^@]+@[^@]+\\.[^@]+$"},
            },
            "required": ["user_id", "email"],
        }
        schema_id = store.store_schema("test_user", schema, version="1.0")
        print(f"✓ Stored schema (ID: {schema_id})")

        # Test schema retrieval
        retrieved_schema = store.get_schema(schema_id)
        assert retrieved_schema == schema, "Schema mismatch"
        print("✓ Retrieved schema matches")

        # Test ownership and governance rules via metadata
        metadata = {
            "title": "User Schema Metadata",
            "business_owners": ["user-team@example.com"],
            "governance_rules": {
                "email_validation": {"type": "validation", "field": "email"}
            },
        }
        store.store_metadata(schema_id, metadata)
        retrieved_metadata = store.get_metadata(schema_id)
        assert "user-team@example.com" in retrieved_metadata.get("business_owners", [])
        assert "email_validation" in retrieved_metadata.get("governance_rules", {})
        print("✓ Stored and retrieved ownership and governance rules via metadata")

        # Test list schemas
        schemas = store.list_schemas()
        assert len(schemas) >= 1
        print(f"✓ Listed schemas ({len(schemas)} found)")

        # Test metadata
        store.store_metadata(schema_id, {"tags": ["user", "authentication"]})
        metadata = store.get_metadata(schema_id)
        assert "tags" in metadata
        print("✓ Stored and retrieved metadata")

        store.disconnect()
        print("\n✓ RedisMetadataStore: ALL TESTS PASSED\n")
        return True

    except Exception as e:
        print(f"✗ RedisMetadataStore test failed: {e}")
        print("  Make sure Redis is running: docker ps | grep redis")
        import traceback

        traceback.print_exc()
        return False


def test_complete_workflow():
    """Test complete workflow with contract parsing and metadata storage."""
    print("=" * 70)
    print("Testing Complete Workflow (Contract → Store → Retrieve)")
    print("=" * 70)

    try:
        # Create a contract
        contract = {
            "schema": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "customer_id": {"type": "string"},
                    "total": {"type": "number", "minimum": 0},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1},
                            },
                        },
                    },
                },
                "required": ["order_id", "customer_id", "total"],
            },
            "ownership": {"owner": "orders-team", "team": "data-engineering"},
            "governance_rules": {"retention_days": 365, "pii_fields": ["customer_id"]},
            "metadata": {"version": "1.0", "description": "Order data contract"},
        }

        # Parse contract
        metadata = parse_contract(contract)
        print("✓ Parsed contract")

        # Store in in-memory store
        store = InMemoryMetadataStore()
        store.connect()

        schema_id = store.store_schema("order", metadata.schema, version="1.0")
        print(f"✓ Stored schema (ID: {schema_id})")

        # Store metadata with ownership and governance rules
        metadata_dict = (
            metadata.metadata.copy() if hasattr(metadata, "metadata") else {}
        )

        # Add ownership fields
        if hasattr(metadata, "ownership") and metadata.ownership:
            metadata_dict["business_owners"] = (
                [metadata.ownership.get("owner")]
                if metadata.ownership.get("owner")
                else []
            )

        # Add governance rules
        if hasattr(metadata, "governance_rules") and metadata.governance_rules:
            metadata_dict["governance_rules"] = metadata.governance_rules

        store.store_metadata(schema_id, metadata_dict)
        print("✓ Stored metadata with ownership and governance rules")

        # Retrieve everything
        retrieved_schema = store.get_schema(schema_id)
        retrieved_metadata = store.get_metadata(schema_id)

        assert retrieved_schema == metadata.schema
        if hasattr(metadata, "ownership") and metadata.ownership.get("owner"):
            assert metadata.ownership["owner"] in retrieved_metadata.get(
                "business_owners", []
            )
        if hasattr(metadata, "governance_rules") and metadata.governance_rules:
            assert len(retrieved_metadata.get("governance_rules", {})) >= 1
        if hasattr(metadata, "metadata") and metadata.metadata.get("version"):
            assert retrieved_metadata.get("version") == metadata.metadata["version"]

        print("✓ Retrieved all components")
        print(f"  Schema: {len(retrieved_schema.get('properties', {}))} properties")
        if retrieved_metadata.get("business_owners"):
            print(f"  Business Owners: {retrieved_metadata['business_owners']}")
        if retrieved_metadata.get("governance_rules"):
            print(
                f"  Governance Rules: {len(retrieved_metadata['governance_rules'])} rules"
            )
        if retrieved_metadata.get("version"):
            print(f"  Version: {retrieved_metadata['version']}")

        store.disconnect()
        print("\n✓ Complete Workflow: ALL TESTS PASSED\n")
        return True

    except Exception as e:
        print(f"✗ Complete workflow test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PYCHARTER METADATA STORE TESTS")
    print("=" * 70 + "\n")

    results = {}

    # Test in-memory (always available)
    results["InMemory"] = test_in_memory_store()

    # Test MongoDB
    results["MongoDB"] = test_mongodb_store()

    # Test PostgreSQL
    results["PostgreSQL"] = test_postgres_store()

    # Test Redis
    results["Redis"] = test_redis_store()

    # Test complete workflow
    results["Complete Workflow"] = test_complete_workflow()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:20s} {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
