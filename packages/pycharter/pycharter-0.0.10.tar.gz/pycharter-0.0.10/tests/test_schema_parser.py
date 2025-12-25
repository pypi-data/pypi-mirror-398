"""
Tests for the schema parser module.
"""

import pytest

from pycharter.shared.schema_parser import (
    get_schema_type,
    is_required,
    normalize_schema,
    validate_schema,
)


def test_validate_schema_valid():
    """Test validation of valid schemas."""
    schema1 = {"type": "object", "properties": {}}
    validate_schema(schema1)  # Should not raise

    schema2 = {"properties": {}}
    validate_schema(schema2)  # Should not raise


def test_validate_schema_invalid():
    """Test validation of invalid schemas."""
    with pytest.raises(ValueError, match="Schema must be a dictionary"):
        validate_schema("not a dict")

    with pytest.raises(ValueError):
        validate_schema({})


def test_normalize_schema():
    """Test schema normalization."""
    schema = {"properties": {"name": {"type": "string"}}}
    normalized = normalize_schema(schema)
    assert normalized["type"] == "object"
    assert "properties" in normalized


def test_get_schema_type():
    """Test getting schema type."""
    assert get_schema_type({"type": "string"}) == "string"
    assert get_schema_type({"type": "object"}) == "object"
    assert get_schema_type({"properties": {}}) == "object"
    assert get_schema_type({"items": {}}) == "array"
    assert get_schema_type({}) == "string"  # Default


def test_is_required():
    """Test checking if a field is required."""
    schema = {
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name"],
    }

    assert is_required("name", schema) is True
    assert is_required("age", schema) is False
    assert is_required("email", schema) is False
