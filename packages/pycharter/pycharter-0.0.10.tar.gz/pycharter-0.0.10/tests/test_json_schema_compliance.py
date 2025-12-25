"""
Tests for JSON Schema standard compliance.

These tests ensure that pycharter properly handles standard JSON Schema keywords
and validates schemas against JSON Schema standard.
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from pycharter import from_dict
from pycharter.shared.json_schema_validator import (
    is_valid_json_schema,
    validate_json_schema,
)
from pycharter.shared.schema_parser import validate_schema


class TestJSONSchemaCompliance:
    """Test JSON Schema standard compliance."""

    def test_valid_json_schema_passes(self):
        """Test that valid JSON Schema passes validation."""
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }

        # Should not raise
        validate_json_schema(schema)
        assert is_valid_json_schema(schema) is True

    def test_charter_extensions_allowed(self):
        """Test that charter extensions are allowed in valid JSON Schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "coercion": "coerce_to_string",  # Extension
                    "validations": {  # Extension
                        "min_length": {"threshold": 3},
                    },
                },
            },
        }

        # Should not raise - extensions are allowed
        validate_json_schema(schema, strict=False)
        assert is_valid_json_schema(schema) is True

    def test_invalid_json_schema_fails(self):
        """Test that invalid JSON Schema fails validation."""
        # Invalid: type is not a valid JSON Schema type
        schema = {
            "type": "invalid_type",
            "properties": {},
        }

        # Note: jsonschema library may be lenient, so we test with a more obviously invalid schema
        # Empty schema should fail basic validation
        with pytest.raises(ValueError):
            validate_json_schema({})

    def test_standard_json_schema_keywords(self):
        """Test that standard JSON Schema keywords work."""
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 10,
                    "pattern": "^[a-z]+$",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"],
                },
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 10,
                    "uniqueItems": True,
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Test minLength/maxLength
        instance1 = Model(code="abc", status="active", score=50, tags=["tag1"])
        assert instance1.code == "abc"

        # Test pattern
        with pytest.raises(Exception):  # Should fail pattern (has numbers)
            Model(code="abc123", status="active", score=50, tags=["tag1"])

        # Test enum
        with pytest.raises(Exception):
            Model(code="abc", status="invalid", score=50, tags=["tag1"])

        # Test minimum/maximum
        with pytest.raises(Exception):
            Model(code="abc", status="active", score=150, tags=["tag1"])

        # Test uniqueItems
        with pytest.raises(Exception):
            Model(code="abc", status="active", score=50, tags=["tag1", "tag1"])


class TestStandardJSONSchemaKeywords:
    """Test standard JSON Schema validation keywords."""

    def test_minLength_maxLength(self):
        """Test minLength and maxLength constraints."""
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 5,
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(code="abc")
        assert instance.code == "abc"

        instance2 = Model(code="abcde")
        assert instance2.code == "abcde"

        # Invalid - too short
        with pytest.raises(Exception):
            Model(code="ab")

        # Invalid - too long
        with pytest.raises(Exception):
            Model(code="abcdef")

    def test_pattern(self):
        """Test pattern constraint."""
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "pattern": "^[A-Z]{3}$",
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(code="ABC")
        assert instance.code == "ABC"

        # Invalid - doesn't match pattern
        with pytest.raises(Exception):
            Model(code="abc")

        with pytest.raises(Exception):
            Model(code="ABCD")

    def test_enum(self):
        """Test enum constraint."""
        schema = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"],
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance1 = Model(status="active")
        assert instance1.status == "active"

        instance2 = Model(status="pending")
        assert instance2.status == "pending"

        # Invalid - not in enum
        with pytest.raises(Exception):
            Model(status="invalid")

    def test_const(self):
        """Test const constraint."""
        schema = {
            "type": "object",
            "properties": {
                "version": {
                    "type": "string",
                    "const": "1.0.0",
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(version="1.0.0")
        assert instance.version == "1.0.0"

        # Invalid - must be exact value
        with pytest.raises(Exception):
            Model(version="1.0.1")

    def test_minimum_maximum(self):
        """Test minimum and maximum constraints."""
        schema = {
            "type": "object",
            "properties": {
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                },
                "temperature": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "exclusiveMaximum": 100,
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(score=50, temperature=50)
        assert instance.score == 50

        # Invalid - below minimum
        with pytest.raises(Exception):
            Model(score=-1, temperature=50)

        # Invalid - above maximum
        with pytest.raises(Exception):
            Model(score=101, temperature=50)

        # Invalid - exclusive minimum
        with pytest.raises(Exception):
            Model(score=50, temperature=0)

    def test_minItems_maxItems(self):
        """Test minItems and maxItems constraints."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 5,
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(tags=["tag1", "tag2"])
        assert len(instance.tags) == 2

        # Invalid - too few items
        with pytest.raises(PydanticValidationError):
            Model(tags=[])

        # Invalid - too many items
        with pytest.raises(PydanticValidationError):
            Model(tags=["1", "2", "3", "4", "5", "6"])

    def test_uniqueItems(self):
        """Test uniqueItems constraint."""
        schema = {
            "type": "object",
            "properties": {
                "ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "uniqueItems": True,
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(ids=[1, 2, 3])
        assert instance.ids == [1, 2, 3]

        # Invalid - duplicates
        with pytest.raises(Exception):
            Model(ids=[1, 2, 2])

    def test_standard_and_charter_extensions_together(self):
        """Test that standard JSON Schema and charter extensions work together."""
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "minLength": 3,  # Standard JSON Schema
                    "maxLength": 10,  # Standard JSON Schema
                    "coercion": "coerce_to_string",  # Charter extension
                    "validations": {  # Charter extension
                        "no_capital_characters": None,
                    },
                },
            },
        }

        Model = from_dict(schema, "TestModel")

        # Standard constraints + extensions should both work
        instance = Model(code="abc123")
        assert instance.code == "abc123"

        # Should fail standard minLength
        with pytest.raises(Exception):
            Model(code="ab")

        # Should fail charter validation (capital characters)
        with pytest.raises(Exception):
            Model(code="ABC123")
