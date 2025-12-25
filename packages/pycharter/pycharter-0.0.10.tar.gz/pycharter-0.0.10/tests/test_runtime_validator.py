"""
Tests for Runtime Validator service.

Tests the functionality of validating data against Pydantic models
in both database-backed and contract-based modes.
"""

import pytest
from pydantic import ValidationError

from pycharter import (
    ValidationResult,
    get_model_from_contract,
    get_model_from_store,
    validate,
    validate_batch,
    validate_batch_with_contract,
    validate_batch_with_store,
    validate_with_contract,
    validate_with_store,
)
from pycharter.metadata_store import InMemoryMetadataStore
from pycharter.pydantic_generator import from_dict


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_validation_result_valid(self):
        """Test ValidationResult for valid data."""
        result = ValidationResult(is_valid=True, data=None)

        assert result.is_valid is True
        assert result.errors == []
        assert bool(result) is True

    def test_validation_result_invalid(self):
        """Test ValidationResult for invalid data."""
        errors = ["Error 1", "Error 2"]
        result = ValidationResult(is_valid=False, errors=errors)

        assert result.is_valid is False
        assert result.errors == errors
        assert bool(result) is False

    def test_validation_result_bool_conversion(self):
        """Test ValidationResult boolean conversion."""
        valid_result = ValidationResult(is_valid=True)
        invalid_result = ValidationResult(is_valid=False)

        assert bool(valid_result) is True
        assert bool(invalid_result) is False


class TestValidate:
    """Tests for validate function."""

    def test_validate_success(self):
        """Test successful validation."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        Person = from_dict(schema, "Person")
        result = validate(Person, {"name": "Alice", "age": 30})

        assert result.is_valid is True
        assert result.data is not None
        assert result.data.name == "Alice"
        assert result.data.age == 30
        assert result.errors == []

    def test_validate_failure(self):
        """Test validation failure."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "age": {"type": "integer", "minimum": 0},
            },
            "required": ["age"],
        }
        Person = from_dict(schema, "Person")
        result = validate(Person, {"age": -5})

        assert result.is_valid is False
        assert result.data is None
        assert len(result.errors) > 0

    def test_validate_missing_required_field(self):
        """Test validation with missing required field."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"],
        }
        Person = from_dict(schema, "Person")
        result = validate(Person, {})

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_strict_mode(self):
        """Test validation in strict mode (raises exceptions)."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "age": {"type": "integer", "minimum": 0},
            },
        }
        Person = from_dict(schema, "Person")

        with pytest.raises(ValidationError):
            validate(Person, {"age": -5}, strict=True)

    def test_validate_with_coercion(self):
        """Test validation with coercion rules."""
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
        Person = from_dict(schema, "Person")
        result = validate(Person, {"age": "30"})

        assert result.is_valid is True
        assert result.data.age == 30
        assert isinstance(result.data.age, int)


class TestValidateBatch:
    """Tests for validate_batch function."""

    def test_validate_batch_success(self):
        """Test successful batch validation."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
            },
        }
        Person = from_dict(schema, "Person")
        data_list = [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Charlie"},
        ]

        results = validate_batch(Person, data_list)

        assert len(results) == 3
        assert all(r.is_valid for r in results)
        assert results[0].data.name == "Alice"
        assert results[1].data.name == "Bob"
        assert results[2].data.name == "Charlie"

    def test_validate_batch_mixed_results(self):
        """Test batch validation with mixed valid/invalid data."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "age": {"type": "integer", "minimum": 0},
            },
        }
        Person = from_dict(schema, "Person")
        data_list = [
            {"age": 25},  # Valid
            {"age": -5},  # Invalid
            {"age": 30},  # Valid
        ]

        results = validate_batch(Person, data_list)

        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is False
        assert results[2].is_valid is True

    def test_validate_batch_empty_list(self):
        """Test batch validation with empty list."""
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }
        Person = from_dict(schema, "Person")

        results = validate_batch(Person, [])

        assert len(results) == 0


class TestValidateWithContract:
    """Tests for validate_with_contract function."""

    def test_validate_with_contract_dict(self):
        """Test validation with contract dictionary."""
        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
            },
        }

        result = validate_with_contract(contract, {"name": "Alice", "age": 30})

        assert result.is_valid is True
        assert result.data.name == "Alice"
        assert result.data.age == 30

    def test_validate_with_contract_with_rules(self):
        """Test validation with contract including coercion/validation rules."""
        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "age": {
                        "type": "integer",
                        "coercion": "coerce_to_integer",
                    },
                },
            },
        }

        result = validate_with_contract(contract, {"age": "30"})

        assert result.is_valid is True
        assert result.data.age == 30
        assert isinstance(result.data.age, int)

    def test_validate_with_contract_file(self):
        """Test validation with contract file path."""
        import tempfile
        from pathlib import Path

        import yaml

        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "name": {"type": "string"},
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(contract, f)
            temp_path = f.name

        try:
            result = validate_with_contract(temp_path, {"name": "Alice"})

            assert result.is_valid is True
            assert result.data.name == "Alice"
        finally:
            Path(temp_path).unlink()

    def test_validate_with_contract_invalid_data(self):
        """Test validation with invalid data."""
        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "age": {"type": "integer", "minimum": 0},
                },
            },
        }

        result = validate_with_contract(contract, {"age": -5})

        assert result.is_valid is False
        assert len(result.errors) > 0


class TestValidateBatchWithContract:
    """Tests for validate_batch_with_contract function."""

    def test_validate_batch_with_contract(self):
        """Test batch validation with contract."""
        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "name": {"type": "string"},
                },
            },
        }

        data_list = [
            {"name": "Alice"},
            {"name": "Bob"},
        ]

        results = validate_batch_with_contract(contract, data_list)

        assert len(results) == 2
        assert all(r.is_valid for r in results)


class TestValidateWithStore:
    """Tests for validate_with_store function."""

    def test_validate_with_store(self):
        """Test validation using metadata store."""
        store = InMemoryMetadataStore()
        store.connect()

        # Store schema
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        schema_id = store.store_schema("test_schema", schema, version="1.0.0")

        # Validate
        result = validate_with_store(store, schema_id, {"name": "Alice", "age": 30})

        assert result.is_valid is True
        assert result.data.name == "Alice"
        assert result.data.age == 30

    def test_validate_with_store_with_rules(self):
        """Test validation with store including coercion rules."""
        store = InMemoryMetadataStore()
        store.connect()

        # Store schema
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "age": {"type": "integer"},
            },
        }
        schema_id = store.store_schema("test_schema", schema, version="1.0.0")

        # Store coercion rules
        coercion_rules = {
            "version": "1.0.0",
            "rules": {"age": "coerce_to_integer"},
        }
        store.store_coercion_rules(schema_id, coercion_rules, version="1.0.0")

        # Validate with string that should be coerced
        result = validate_with_store(store, schema_id, {"age": "30"})

        assert result.is_valid is True
        assert result.data.age == 30
        assert isinstance(result.data.age, int)

    def test_validate_with_store_schema_not_found(self):
        """Test validation when schema is not found in store."""
        store = InMemoryMetadataStore()
        store.connect()

        result = validate_with_store(store, "nonexistent_schema", {"name": "Alice"})

        assert result.is_valid is False
        assert len(result.errors) > 0


class TestValidateBatchWithStore:
    """Tests for validate_batch_with_store function."""

    def test_validate_batch_with_store(self):
        """Test batch validation using metadata store."""
        store = InMemoryMetadataStore()
        store.connect()

        # Store schema
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
            },
        }
        schema_id = store.store_schema("test_schema", schema, version="1.0.0")

        # Validate batch
        data_list = [
            {"name": "Alice"},
            {"name": "Bob"},
        ]

        results = validate_batch_with_store(store, schema_id, data_list)

        assert len(results) == 2
        assert all(r.is_valid for r in results)


class TestGetModelFromContract:
    """Tests for get_model_from_contract function."""

    def test_get_model_from_contract_dict(self):
        """Test getting model from contract dictionary."""
        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "name": {"type": "string"},
                },
            },
        }

        Model = get_model_from_contract(contract, "Person")

        assert Model.__name__ == "Person"
        person = Model(name="Alice")
        assert person.name == "Alice"

    def test_get_model_from_contract_with_rules(self):
        """Test getting model from contract with rules."""
        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "age": {
                        "type": "integer",
                        "coercion": "coerce_to_integer",
                    },
                },
            },
        }

        Model = get_model_from_contract(contract)

        # Coercion should work
        model = Model(age="30")
        assert model.age == 30
        assert isinstance(model.age, int)

    def test_get_model_from_contract_file(self):
        """Test getting model from contract file."""
        import tempfile
        from pathlib import Path

        import yaml

        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "name": {"type": "string"},
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(contract, f)
            temp_path = f.name

        try:
            Model = get_model_from_contract(temp_path, "Person")

            assert Model.__name__ == "Person"
            person = Model(name="Alice")
            assert person.name == "Alice"
        finally:
            Path(temp_path).unlink()


class TestGetModelFromStore:
    """Tests for get_model_from_store function."""

    def test_get_model_from_store(self):
        """Test getting model from metadata store."""
        store = InMemoryMetadataStore()
        store.connect()

        # Store schema
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        schema_id = store.store_schema("test_schema", schema, version="1.0.0")

        # Get model
        Model = get_model_from_store(store, schema_id, "Person")

        assert Model.__name__ == "Person"
        person = Model(name="Alice", age=30)
        assert person.name == "Alice"
        assert person.age == 30

    def test_get_model_from_store_with_rules(self):
        """Test getting model from store with coercion rules."""
        store = InMemoryMetadataStore()
        store.connect()

        # Store schema
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "age": {"type": "integer"},
            },
        }
        schema_id = store.store_schema("test_schema", schema, version="1.0.0")

        # Store coercion rules
        coercion_rules = {
            "version": "1.0.0",
            "rules": {"age": "coerce_to_integer"},
        }
        store.store_coercion_rules(schema_id, coercion_rules, version="1.0.0")

        # Get model
        Model = get_model_from_store(store, schema_id)

        # Coercion should work
        model = Model(age="30")
        assert model.age == 30
        assert isinstance(model.age, int)

    def test_get_model_from_store_with_version(self):
        """Test getting model from store with specific version."""
        store = InMemoryMetadataStore()
        store.connect()

        # Store multiple versions
        schema_v1 = {
            "type": "object",
            "version": "1.0.0",
            "properties": {"name": {"type": "string"}},
        }
        schema_id = store.store_schema("test", schema_v1, version="1.0.0")

        schema_v2 = {
            "type": "object",
            "version": "2.0.0",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        }
        store.store_schema("test", schema_v2, version="2.0.0")

        # Get v1 model
        ModelV1 = get_model_from_store(store, schema_id, version="1.0.0")
        person1 = ModelV1(name="Alice")
        assert not hasattr(person1, "age")

        # Get v2 model
        ModelV2 = get_model_from_store(store, schema_id, version="2.0.0")
        person2 = ModelV2(name="Bob", age=30)
        assert person2.age == 30


class TestComplexScenarios:
    """Tests for complex validation scenarios."""

    def test_end_to_end_workflow(self):
        """Test complete workflow: store → build → validate."""
        store = InMemoryMetadataStore()
        store.connect()

        # Store all components
        schema = {
            "type": "object",
            "version": "1.0.0",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }
        schema_id = store.store_schema("user", schema, version="1.0.0")

        coercion_rules = {
            "version": "1.0.0",
            "rules": {"age": "coerce_to_integer"},
        }
        store.store_coercion_rules(schema_id, coercion_rules, version="1.0.0")

        # Validate using store
        result = validate_with_store(store, schema_id, {"name": "Alice", "age": "30"})

        assert result.is_valid is True
        assert result.data.name == "Alice"
        assert result.data.age == 30

    def test_validate_with_nested_structures(self):
        """Test validation with nested object structures."""
        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {
                                "type": "object",
                                "properties": {
                                    "city": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        }

        result = validate_with_contract(
            contract,
            {
                "user": {
                    "name": "Alice",
                    "address": {"city": "New York"},
                },
            },
        )

        assert result.is_valid is True
        assert result.data.user.name == "Alice"
        assert result.data.user.address.city == "New York"
