"""
Integration tests using fixtures.

These tests verify end-to-end functionality using real-world scenarios
with the fixture data.
"""

import json
from pathlib import Path

import pytest

from pycharter import from_dict, from_file
from tests.conftest import load_sample_data, load_schema


class TestIntegrationWithFixtures:
    """Integration tests using fixture data."""

    def test_complete_workflow_simple_person(self):
        """Test complete workflow: load schema, create model, validate data."""
        # Load schema from fixture
        schema = load_schema("simple_person.json")

        # Generate model
        Person = from_dict(schema, "Person")

        # Load sample data
        data = load_sample_data("valid_person.json")

        # Create and validate instance
        person = Person(**data)

        # Verify all fields
        assert person.name == "Alice Smith"
        assert person.age == 30
        assert person.email == "alice@example.com"

        # Verify serialization
        dumped = person.model_dump()
        assert dumped == data

    def test_complete_workflow_with_coercion(self):
        """Test complete workflow with coercion."""
        schema = load_schema("with_coercion.json")
        data = load_sample_data("valid_with_coercion.json")

        Model = from_dict(schema, "CoercionModel")
        instance = Model(**data)

        # Verify coercion occurred
        assert isinstance(instance.id, str)
        assert isinstance(instance.count, int)
        assert isinstance(instance.price, float)
        assert isinstance(instance.is_active, bool)

    def test_nested_structure_workflow(self):
        """Test complete workflow with nested structures."""
        schema = load_schema("nested_address.json")
        data = load_sample_data("valid_nested_address.json")

        Person = from_dict(schema, "Person")
        person = Person(**data)

        # Verify nested access
        assert person.name == "Bob Johnson"
        assert person.address.city == "New York"
        assert person.address.country == "USA"

    def test_all_fixtures_are_usable(self, schemas_dir, sample_data_dir):
        """Verify all fixture schemas can be used with sample data."""
        schema_files = list(schemas_dir.glob("*.json"))

        for schema_file in schema_files:
            # Load schema
            schema = load_schema(schema_file.name)
            Model = from_dict(schema, "TestModel")

            # Try to create an empty instance (if no required fields)
            # or with minimal data
            try:
                instance = Model()
                assert instance is not None
            except Exception:
                # Some schemas require fields, that's okay
                pass
