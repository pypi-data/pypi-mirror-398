"""
Schema parser module for validating and normalizing JSON schemas.
"""

from typing import Any, Dict, List, Optional

from pycharter.shared.json_schema_validator import validate_json_schema


def validate_schema(schema: Dict[str, Any], strict_json_schema: bool = False) -> None:
    """
    Validate that a dictionary is a valid JSON Schema.

    This validates that the schema conforms to JSON Schema Draft 2020-12 standard,
    while allowing charter extension fields (coercion, validations).

    Args:
        schema: The schema dictionary to validate
        strict_json_schema: If True, only allow standard JSON Schema (no extensions)

    Raises:
        ValueError: If the schema is invalid or doesn't conform to JSON Schema standard
    """
    validate_json_schema(schema, strict=strict_json_schema)


def normalize_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a JSON schema to a standard format.

    Handles schemas that might be missing explicit type information
    by inferring types from other fields.

    Args:
        schema: The schema dictionary to normalize

    Returns:
        Normalized schema dictionary
    """
    if "properties" in schema:
        # This is an object schema
        normalized = schema.copy()
        if "type" not in normalized:
            normalized["type"] = "object"
        return normalized

    return schema.copy()


def get_schema_type(schema: Dict[str, Any]) -> str:
    """
    Get the type of a schema, with fallback inference.

    Args:
        schema: The schema dictionary

    Returns:
        The schema type (e.g., 'object', 'string', 'number', etc.)
    """
    if "type" in schema:
        return schema["type"]

    # Infer type from other fields
    if "properties" in schema:
        return "object"
    if "items" in schema:
        return "array"

    # Default to string if no type information
    return "string"


def is_required(field_name: str, schema: Dict[str, Any]) -> bool:
    """
    Check if a field is required based on the schema.

    Args:
        field_name: Name of the field to check
        schema: The parent schema (object schema with properties)

    Returns:
        True if the field is required, False otherwise
    """
    required_fields = schema.get("required", [])
    return field_name in required_fields
