"""
Tests for x-validators format support.
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from pycharter import from_dict


class TestXValidatorsFormat:
    """Test x-validators array format."""

    def test_x_validators_pre_coercion(self):
        """Test pre-validation coercion via x-validators."""
        schema = {
            "type": "object",
            "properties": {
                "notes": {
                    "type": "string",
                    "x-validators": [{"name": "coerce_to_lowercase", "pre": True}],
                }
            },
        }

        Model = from_dict(schema, "TestModel")
        instance = Model(notes="HELLO WORLD")
        assert instance.notes == "hello world"

    def test_x_validators_post_validation(self):
        """Test post-validation via x-validators."""
        schema = {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "x-validators": [{"name": "non_empty_string"}],
                }
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(order_id="123")
        assert instance.order_id == "123"

        # Invalid - empty string
        with pytest.raises(PydanticValidationError):
            Model(order_id="")

    def test_x_validators_with_params(self):
        """Test x-validators with parameters."""
        schema = {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "x-validators": [
                        {"name": "is_positive", "params": {"threshold": 0}}
                    ],
                }
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(customer_id=1)
        assert instance.customer_id == 1

        # Invalid - negative
        with pytest.raises(PydanticValidationError):
            Model(customer_id=-1)

    def test_x_validators_matches_regex(self):
        """Test matches_regex validator via x-validators."""
        schema = {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "x-validators": [
                        {
                            "name": "matches_regex",
                            "params": {"pattern": "^[A-Z0-9]{3}-[A-Z0-9]{6}$"},
                        }
                    ],
                }
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(sku="ABC-123456")
        assert instance.sku == "ABC-123456"

        # Invalid - doesn't match pattern
        with pytest.raises(PydanticValidationError):
            Model(sku="abc-123")

        # Invalid - wrong format
        with pytest.raises(PydanticValidationError):
            Model(sku="ABC123456")

    def test_x_validators_multiple(self):
        """Test multiple validators in x-validators array."""
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "x-validators": [
                        {"name": "non_empty_string"},
                        {"name": "min_length", "params": {"threshold": 3}},
                        {"name": "no_capital_characters"},
                    ],
                }
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(code="abc123")
        assert instance.code == "abc123"

        # Invalid - empty
        with pytest.raises(PydanticValidationError):
            Model(code="")

        # Invalid - too short
        with pytest.raises(PydanticValidationError):
            Model(code="ab")

        # Invalid - has capitals
        with pytest.raises(PydanticValidationError):
            Model(code="ABC123")

    def test_x_validators_pre_and_post(self):
        """Test both pre and post validators."""
        schema = {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "x-validators": [
                        {"name": "coerce_to_lowercase", "pre": True},
                        {"name": "min_length", "params": {"threshold": 3}},
                    ],
                }
            },
        }

        Model = from_dict(schema, "TestModel")

        # Coerce then validate
        instance = Model(text="HELLO")
        assert instance.text == "hello"

        # After coercion, should fail min_length
        with pytest.raises(PydanticValidationError):
            Model(text="HI")  # "hi" after coercion is too short


class TestXValidatorsWithRefs:
    """Test x-validators with $ref and definitions."""

    def test_x_validators_in_definitions(self):
        """Test x-validators in definitions."""
        schema = {
            "type": "object",
            "properties": {"product": {"$ref": "#/definitions/Product"}},
            "definitions": {
                "Product": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "x-validators": [
                                {
                                    "name": "matches_regex",
                                    "params": {"pattern": "^[A-Z0-9]{3}-[A-Z0-9]{6}$"},
                                }
                            ],
                        },
                        "quantity": {
                            "type": "integer",
                            "x-validators": [{"name": "is_positive"}],
                        },
                    },
                }
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(product={"sku": "ABC-123456", "quantity": 2})
        assert instance.product.sku == "ABC-123456"
        assert instance.product.quantity == 2

        # Invalid SKU
        with pytest.raises(PydanticValidationError):
            Model(product={"sku": "abc-123", "quantity": 2})

        # Invalid quantity
        with pytest.raises(PydanticValidationError):
            Model(product={"sku": "ABC-123456", "quantity": -1})

    def test_x_validators_in_array_items(self):
        """Test x-validators in array items via $ref."""
        schema = {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"$ref": "#/definitions/Product"}}
            },
            "definitions": {
                "Product": {
                    "type": "object",
                    "properties": {
                        "sku": {
                            "type": "string",
                            "x-validators": [
                                {
                                    "name": "matches_regex",
                                    "params": {"pattern": "^[A-Z]{3}$"},
                                }
                            ],
                        }
                    },
                }
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(items=[{"sku": "ABC"}, {"sku": "DEF"}])
        assert len(instance.items) == 2
        assert instance.items[0].sku == "ABC"

        # Invalid - one item fails validation
        with pytest.raises(PydanticValidationError):
            Model(items=[{"sku": "ABC"}, {"sku": "abc"}])
