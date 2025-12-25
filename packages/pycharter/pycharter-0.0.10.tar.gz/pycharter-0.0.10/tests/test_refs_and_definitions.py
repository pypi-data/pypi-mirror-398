"""
Tests for $ref references and definitions/$defs support.
"""

import pytest

from pycharter import from_dict


class TestRefsAndDefinitions:
    """Test $ref and definitions support."""

    def test_ref_to_definitions(self):
        """Test $ref to definitions section."""
        schema = {
            "type": "object",
            "properties": {"customer": {"$ref": "#/definitions/Customer"}},
            "definitions": {
                "Customer": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                    "required": ["name", "email"],
                }
            },
        }

        Model = from_dict(schema, "TestModel")
        instance = Model(customer={"name": "Alice", "email": "alice@example.com"})
        assert instance.customer.name == "Alice"
        assert instance.customer.email == "alice@example.com"

    def test_ref_to_defs(self):
        """Test $ref to $defs section (Draft 2020-12)."""
        schema = {
            "type": "object",
            "properties": {"customer": {"$ref": "#/$defs/Customer"}},
            "$defs": {
                "Customer": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }

        Model = from_dict(schema, "TestModel")
        instance = Model(customer={"name": "Bob"})
        assert instance.customer.name == "Bob"

    def test_ref_in_array_items(self):
        """Test $ref in array items."""
        schema = {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"$ref": "#/definitions/Product"}}
            },
            "definitions": {
                "Product": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "price": {"type": "number"},
                    },
                }
            },
        }

        Model = from_dict(schema, "TestModel")
        instance = Model(
            items=[{"name": "Item1", "price": 10.5}, {"name": "Item2", "price": 20.0}]
        )
        assert len(instance.items) == 2
        assert instance.items[0].name == "Item1"
        assert instance.items[1].price == 20.0

    def test_nested_refs(self):
        """Test nested $ref references."""
        schema = {
            "type": "object",
            "properties": {"order": {"$ref": "#/definitions/Order"}},
            "definitions": {
                "Order": {
                    "type": "object",
                    "properties": {
                        "customer": {"$ref": "#/definitions/Customer"},
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/Product"},
                        },
                    },
                },
                "Customer": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                },
                "Product": {
                    "type": "object",
                    "properties": {"sku": {"type": "string"}},
                },
            },
        }

        Model = from_dict(schema, "TestModel")
        instance = Model(
            order={"customer": {"name": "Alice"}, "items": [{"sku": "ABC-123"}]}
        )
        assert instance.order.customer.name == "Alice"
        assert instance.order.items[0].sku == "ABC-123"

    def test_ref_with_other_properties(self):
        """Test $ref with additional properties (should merge)."""
        schema = {
            "type": "object",
            "properties": {
                "customer": {
                    "$ref": "#/definitions/Customer",
                    "description": "The customer",
                }
            },
            "definitions": {
                "Customer": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }

        Model = from_dict(schema, "TestModel")
        instance = Model(customer={"name": "Bob"})
        assert instance.customer.name == "Bob"

    def test_definitions_and_defs_together(self):
        """Test schema with both definitions and $defs."""
        schema = {
            "type": "object",
            "properties": {
                "customer1": {"$ref": "#/definitions/Customer"},
                "customer2": {"$ref": "#/$defs/Customer"},
            },
            "definitions": {
                "Customer": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "default": "Default"}},
                }
            },
            "$defs": {
                "Customer": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }

        Model = from_dict(schema, "TestModel")
        # Both should work - note: nested objects with defaults need explicit values
        # The default is only applied when the field itself has a default, not nested fields
        instance = Model(customer1={"name": "Default"}, customer2={"name": "Bob"})
        assert instance.customer1.name == "Default"
        assert instance.customer2.name == "Bob"


class TestFormatField:
    """Test format field support."""

    def test_uuid_format(self):
        """Test UUID format validation."""
        schema = {
            "type": "object",
            "properties": {"order_id": {"type": "string", "format": "uuid"}},
        }

        Model = from_dict(schema, "TestModel")

        # Valid UUID
        instance = Model(order_id="123e4567-e89b-12d3-a456-426614174000")
        assert instance.order_id == "123e4567-e89b-12d3-a456-426614174000"

        # Invalid UUID format
        with pytest.raises(Exception):
            Model(order_id="not-a-uuid")

    def test_email_format(self):
        """Test email format validation."""
        schema = {
            "type": "object",
            "properties": {"email": {"type": "string", "format": "email"}},
        }

        Model = from_dict(schema, "TestModel")

        # Valid email
        instance = Model(email="test@example.com")
        assert instance.email == "test@example.com"

        # Invalid email format
        with pytest.raises(Exception):
            Model(email="not-an-email")

    def test_format_with_x_validators(self):
        """Test format field with x-validators."""
        schema = {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "format": "uuid",
                    "x-validators": [{"name": "non_empty_string"}],
                }
            },
        }

        Model = from_dict(schema, "TestModel")

        # Valid
        instance = Model(order_id="123e4567-e89b-12d3-a456-426614174000")
        assert instance.order_id == "123e4567-e89b-12d3-a456-426614174000"

        # Invalid - empty (x-validator)
        with pytest.raises(Exception):
            Model(order_id="")

        # Invalid - wrong format
        with pytest.raises(Exception):
            Model(order_id="not-a-uuid")
