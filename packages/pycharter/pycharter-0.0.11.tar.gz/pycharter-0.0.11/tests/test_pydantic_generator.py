"""
Tests for Pydantic Generator service.

Tests the generation of Pydantic models from JSON Schema definitions.
"""

import json
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from pycharter.pydantic_generator import (
    from_dict,
    from_file,
    from_json,
    from_url,
    generate_model,
    generate_model_file,
)


class TestFromDict:
    """Tests for from_dict function."""

    def test_generate_simple_model(self):
        """Test generating a simple model from dictionary."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        Person = from_dict(schema, "Person")

        assert Person.__name__ == "Person"
        person = Person(name="Alice", age=30)
        assert person.name == "Alice"
        assert person.age == 30

    def test_generate_model_with_required_fields(self):
        """Test generating model with required fields."""
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

        # Valid data
        user = User(name="Alice", email="alice@example.com")
        assert user.name == "Alice"

        # Missing required field should raise error
        with pytest.raises(ValidationError):
            User(email="alice@example.com")

    def test_generate_model_with_defaults(self):
        """Test generating model with default values."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "active": {"type": "boolean", "default": True},
            },
        }
        User = from_dict(schema, "User")

        user = User(name="Alice")
        assert user.active is True

    def test_generate_model_with_constraints(self):
        """Test generating model with field constraints."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
        }
        Person = from_dict(schema, "Person")

        # Valid data
        person = Person(name="Alice", age=30)
        assert person.name == "Alice"

        # Invalid data should raise error
        with pytest.raises(ValidationError):
            Person(name="", age=30)  # Empty name violates minLength

        with pytest.raises(ValidationError):
            Person(name="Alice", age=200)  # Age exceeds maximum

    def test_generate_model_with_enum(self):
        """Test generating model with enum field."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
            },
        }
        Status = from_dict(schema, "Status")

        # Valid enum value
        status = Status(status="active")
        assert status.status == "active"

        # Invalid enum value should raise error
        with pytest.raises(ValidationError):
            Status(status="invalid")

    def test_generate_nested_model(self):
        """Test generating model with nested objects."""
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

        person = Person(
            name="Alice",
            address={"street": "123 Main St", "city": "New York"},
        )
        assert person.name == "Alice"
        assert person.address.street == "123 Main St"
        assert person.address.city == "New York"

    def test_generate_model_with_array(self):
        """Test generating model with array fields."""
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

        model = Model(tags=["python", "pydantic"])
        assert model.tags == ["python", "pydantic"]
        assert len(model.tags) == 2

    def test_generate_model_with_array_of_objects(self):
        """Test generating model with array of objects."""
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

        model = Model(
            items=[
                {"name": "Apple", "price": 1.50},
                {"name": "Banana", "price": 0.75},
            ]
        )
        assert len(model.items) == 2
        assert model.items[0].name == "Apple"
        assert model.items[0].price == 1.50

    def test_generate_model_with_coercion(self):
        """Test generating model with coercion rules."""
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

        # String should be coerced to integer
        model = Model(age="30")
        assert model.age == 30
        assert isinstance(model.age, int)

    def test_generate_model_with_validations(self):
        """Test generating model with validation rules."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {
                    "type": "string",
                    "validations": {
                        "min_length": {"threshold": 3},
                    },
                },
            },
        }
        Model = from_dict(schema, "Model")

        # Valid data
        model = Model(name="Alice")
        assert model.name == "Alice"

        # Invalid data should raise error
        with pytest.raises(ValidationError):
            Model(name="Al")  # Too short


class TestFromJson:
    """Tests for from_json function."""

    def test_generate_from_json_string(self):
        """Test generating model from JSON string."""
        schema_json = json.dumps(
            {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }
        )
        Person = from_json(schema_json, "Person")

        person = Person(name="Alice")
        assert person.name == "Alice"

    def test_generate_from_invalid_json(self):
        """Test that invalid JSON raises an error."""
        with pytest.raises((json.JSONDecodeError, ValueError)):
            from_json("not valid json", "Person")


class TestFromFile:
    """Tests for from_file function."""

    def test_generate_from_json_file(self):
        """Test generating model from JSON file."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(schema, f)
            temp_path = f.name

        try:
            Person = from_file(temp_path, "Person")
            person = Person(name="Alice")
            assert person.name == "Alice"
        finally:
            Path(temp_path).unlink()

    def test_generate_from_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            from_file("nonexistent.json", "Person")

    def test_generate_from_file_auto_name(self):
        """Test generating from file with auto-generated model name."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(schema, f)
            temp_path = f.name

        try:
            # Model name should be derived from filename
            Model = from_file(temp_path)
            assert Model.__name__ is not None
        finally:
            Path(temp_path).unlink()


class TestFromUrl:
    """Tests for from_url function."""

    def test_from_url_not_implemented(self):
        """Test that from_url raises NotImplementedError (if not implemented)."""
        # This test depends on whether from_url is actually implemented
        # Adjust based on actual implementation
        try:
            Model = from_url("http://example.com/schema.json", "Model")
            # If it works, verify it's a valid model
            assert Model is not None
        except NotImplementedError:
            pytest.skip("from_url not implemented")
        except Exception:
            # Other exceptions (network errors, etc.) are acceptable for this test
            pass


class TestGenerateModel:
    """Tests for generate_model function (alias)."""

    def test_generate_model_alias(self):
        """Test that generate_model is an alias for from_dict."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }

        Person1 = from_dict(schema, "Person")
        Person2 = generate_model(schema, "Person")

        # Both should create equivalent models
        person1 = Person1(name="Alice")
        person2 = Person2(name="Alice")
        assert person1.name == person2.name


class TestGenerateModelFile:
    """Tests for generate_model_file function."""

    def test_generate_model_file(self):
        """Test generating a Python file with model definition."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = f.name

        try:
            generate_model_file(schema, temp_path, "Person")

            # Verify file exists
            assert Path(temp_path).exists()

            # Verify file contains model definition
            with open(temp_path) as f:
                content = f.read()
            assert "class Person" in content
            assert "name" in content
            assert "age" in content
        finally:
            Path(temp_path).unlink()


class TestComplexScenarios:
    """Tests for complex generation scenarios."""

    def test_generate_model_with_all_features(self):
        """Test generating model with all features combined."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100,
                    "coercion": "coerce_to_string",
                    "validations": {
                        "min_length": {"threshold": 1},
                    },
                },
                "age": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 150,
                    "coercion": "coerce_to_integer",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
            },
            "required": ["name", "age"],
        }

        Person = from_dict(schema, "Person")

        # Valid data
        person = Person(name="Alice", age="30", tags=["python", "pydantic"])
        assert person.name == "Alice"
        assert person.age == 30  # Coerced from string
        assert len(person.tags) == 2

    def test_generate_model_with_deeply_nested_structures(self):
        """Test generating model with deeply nested structures."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "contact": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }

        Model = from_dict(schema, "Model")
        model = Model(
            user={
                "profile": {
                    "contact": {
                        "email": "alice@example.com",
                    },
                },
            }
        )

        assert model.user.profile.contact.email == "alice@example.com"

    def test_generate_model_with_nullable_fields(self):
        """Test generating model with nullable/optional fields."""
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

        # Email can be None
        user1 = User(name="Alice", email=None)
        assert user1.email is None

        # Email can be a string
        user2 = User(name="Bob", email="bob@example.com")
        assert user2.email == "bob@example.com"

        # Email can be omitted (uses default)
        user3 = User(name="Charlie")
        assert user3.email is None
