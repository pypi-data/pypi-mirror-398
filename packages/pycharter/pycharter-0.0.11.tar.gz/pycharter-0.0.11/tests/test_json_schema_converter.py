"""
Tests for JSON Schema Converter service.

Tests the reverse conversion: Pydantic models → JSON Schema.
"""

import json
import tempfile
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from pycharter.json_schema_converter import (
    model_to_schema,
    to_dict,
    to_file,
    to_json,
)
from pycharter.pydantic_generator import from_dict


class TestToDict:
    """Tests for to_dict function."""

    def test_convert_simple_model(self):
        """Test converting a simple Pydantic model to JSON Schema."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        Person = from_dict(schema, "Person")
        result = to_dict(Person)

        assert result["type"] == "object"
        assert "properties" in result
        # Properties may be wrapped in anyOf for optional fields
        name_prop = result["properties"]["name"]
        age_prop = result["properties"]["age"]
        # Check if it's wrapped in anyOf or direct type
        if "anyOf" in name_prop:
            assert any(item.get("type") == "string" for item in name_prop["anyOf"])
        else:
            assert name_prop.get("type") == "string"
        if "anyOf" in age_prop:
            assert any(item.get("type") == "integer" for item in age_prop["anyOf"])
        else:
            assert age_prop.get("type") == "integer"

    def test_convert_model_with_required_fields(self):
        """Test converting model with required fields."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["name", "email"],
        }
        User = from_dict(schema, "User")
        result = to_dict(User)

        assert "required" in result
        assert "name" in result["required"]
        assert "email" in result["required"]

    def test_convert_model_with_defaults(self):
        """Test converting model with default values."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "active": {"type": "boolean", "default": True},
            },
        }
        User = from_dict(schema, "User")
        result = to_dict(User)

        assert result["properties"]["active"]["default"] is True

    def test_convert_model_with_constraints(self):
        """Test converting model with field constraints."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
        }
        Person = from_dict(schema, "Person")
        result = to_dict(Person)

        assert result["properties"]["name"]["minLength"] == 1
        assert result["properties"]["name"]["maxLength"] == 100
        assert result["properties"]["age"]["minimum"] == 0
        assert result["properties"]["age"]["maximum"] == 150

    def test_convert_model_with_enum(self):
        """Test converting model with enum field."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
            },
        }
        Status = from_dict(schema, "Status")
        result = to_dict(Status)

        assert "enum" in result["properties"]["status"]
        assert set(result["properties"]["status"]["enum"]) == {
            "active",
            "inactive",
            "pending",
        }

    def test_convert_nested_model(self):
        """Test converting model with nested objects."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                    },
                },
            },
        }
        Person = from_dict(schema, "Person")
        result = to_dict(Person)

        assert result["properties"]["address"]["type"] == "object"
        assert "properties" in result["properties"]["address"]
        assert "street" in result["properties"]["address"]["properties"]

    def test_convert_model_with_array(self):
        """Test converting model with array fields."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }
        Model = from_dict(schema, "Model")
        result = to_dict(Model)

        assert result["properties"]["tags"]["type"] == "array"
        assert result["properties"]["tags"]["items"]["type"] == "string"

    def test_convert_model_with_array_of_objects(self):
        """Test converting model with array of objects."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                        },
                    },
                },
            },
        }
        Model = from_dict(schema, "Model")
        result = to_dict(Model)

        assert result["properties"]["items"]["type"] == "array"
        assert result["properties"]["items"]["items"]["type"] == "object"
        assert "name" in result["properties"]["items"]["items"]["properties"]

    def test_convert_manual_pydantic_model(self):
        """Test converting a manually defined Pydantic model."""

        class ManualModel(BaseModel):
            name: str = Field(description="Name field")
            age: int = Field(ge=0, le=150, description="Age field")

        result = to_dict(ManualModel)

        assert result["type"] == "object"
        assert result["properties"]["name"]["type"] == "string"
        assert result["properties"]["age"]["type"] == "integer"
        assert result["properties"]["age"]["minimum"] == 0
        assert result["properties"]["age"]["maximum"] == 150

    def test_round_trip_conversion(self):
        """Test round-trip: schema → model → schema."""
        original_schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0},
            },
            "required": ["name"],
        }

        # Convert to model
        Person = from_dict(original_schema, "Person")

        # Convert back to schema
        result_schema = to_dict(Person)

        # Verify key properties are preserved
        assert result_schema["type"] == "object"
        assert "name" in result_schema["properties"]
        assert "age" in result_schema["properties"]
        assert result_schema["properties"]["name"]["type"] == "string"
        assert result_schema["properties"]["age"]["type"] == "integer"


class TestToJson:
    """Tests for to_json function."""

    def test_convert_to_json_string(self):
        """Test converting model to JSON string."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }
        Person = from_dict(schema, "Person")
        json_str = to_json(Person)

        assert isinstance(json_str, str)
        result = json.loads(json_str)
        assert result["type"] == "object"
        assert "name" in result["properties"]

    def test_json_string_is_valid(self):
        """Test that generated JSON string is valid JSON."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        Person = from_dict(schema, "Person")
        json_str = to_json(Person)

        # Should not raise
        result = json.loads(json_str)
        assert isinstance(result, dict)


class TestToFile:
    """Tests for to_file function."""

    def test_convert_to_file(self):
        """Test converting model to JSON file."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }
        Person = from_dict(schema, "Person")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            to_file(Person, temp_path)

            # Verify file exists and contains valid JSON
            assert Path(temp_path).exists()
            with open(temp_path) as f:
                result = json.load(f)
            assert result["type"] == "object"
        finally:
            Path(temp_path).unlink()

    def test_convert_to_file_overwrites(self):
        """Test that to_file overwrites existing file."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }
        Person = from_dict(schema, "Person")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"old": "data"}')
            temp_path = f.name

        try:
            to_file(Person, temp_path)

            # Verify old content is gone
            with open(temp_path) as f:
                result = json.load(f)
            assert "old" not in result
            assert "type" in result
        finally:
            Path(temp_path).unlink()


class TestModelToSchema:
    """Tests for model_to_schema function (alias)."""

    def test_model_to_schema_alias(self):
        """Test that model_to_schema is an alias for to_dict."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }
        Person = from_dict(schema, "Person")

        result1 = to_dict(Person)
        result2 = model_to_schema(Person)

        assert result1 == result2


class TestComplexScenarios:
    """Tests for complex conversion scenarios."""

    def test_convert_model_with_coercion(self):
        """Test converting model that was generated with coercion rules."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "age": {
                    "type": "integer",
                    "coercion": "coerce_to_integer",
                },
            },
        }
        Model = from_dict(schema, "Model")
        result = to_dict(Model)

        # Coercion should be preserved in the schema
        assert "coercion" in result["properties"]["age"]
        assert result["properties"]["age"]["coercion"] == "coerce_to_integer"

    def test_convert_model_with_validations(self):
        """Test converting model that was generated with validation rules."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {
                    "type": "string",
                    "validations": {
                        "min_length": {"threshold": 1},
                    },
                },
            },
        }
        Model = from_dict(schema, "Model")
        result = to_dict(Model)

        # Validations should be preserved
        assert "validations" in result["properties"]["name"]

    def test_convert_model_with_nullable_fields(self):
        """Test converting model with nullable/optional fields."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "email": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                },
            },
        }
        User = from_dict(schema, "User")
        result = to_dict(User)

        # Email should be optional/nullable
        assert "email" in result["properties"]
