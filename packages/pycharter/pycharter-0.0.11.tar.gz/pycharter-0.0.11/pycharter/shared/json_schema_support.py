"""
Support for standard JSON Schema validation keywords.

This module maps standard JSON Schema keywords to Pydantic field constraints
and validators, ensuring full JSON Schema compliance.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field, ValidationInfo


def apply_json_schema_constraints(
    schema: Dict[str, Any], field_name: str
) -> Dict[str, Any]:
    """
    Apply standard JSON Schema validation keywords to Pydantic Field.

    Maps JSON Schema standard keywords to Pydantic Field constraints:
    - minLength/maxLength -> Field constraints
    - minimum/maximum -> Field constraints
    - pattern -> Field constraints
    - enum -> Field constraints
    - format -> Field constraints (where applicable)

    Args:
        schema: The field schema dictionary
        field_name: Name of the field

    Returns:
        Dictionary of Field kwargs with constraints applied
    """
    field_kwargs: Dict[str, Any] = {}

    # String constraints
    if schema.get("type") == "string":
        if "minLength" in schema:
            field_kwargs["min_length"] = schema["minLength"]
        if "maxLength" in schema:
            field_kwargs["max_length"] = schema["maxLength"]
        if "pattern" in schema:
            field_kwargs["pattern"] = schema["pattern"]
        if "format" in schema:
            # Format validation - store in json_schema_extra for reference
            # Common formats: uuid, email, date-time, etc.
            field_kwargs["json_schema_extra"] = field_kwargs.get(
                "json_schema_extra", {}
            )
            field_kwargs["json_schema_extra"]["format"] = schema["format"]
            # For some formats, we can add pattern validation
            if schema["format"] == "uuid":
                # UUID format validation (basic pattern)
                field_kwargs["pattern"] = (
                    "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                )
            elif schema["format"] == "email":
                # Email format validation (basic pattern)
                field_kwargs["pattern"] = "^[^@]+@[^@]+\\.[^@]+$"

    # Number constraints
    if schema.get("type") in ["number", "integer"]:
        if "minimum" in schema:
            field_kwargs["ge"] = schema["minimum"]
        if "maximum" in schema:
            field_kwargs["le"] = schema["maximum"]
        if "exclusiveMinimum" in schema:
            field_kwargs["gt"] = schema["exclusiveMinimum"]
        if "exclusiveMaximum" in schema:
            field_kwargs["lt"] = schema["exclusiveMaximum"]
        if "multipleOf" in schema:
            field_kwargs["multiple_of"] = schema["multipleOf"]

    # Array constraints
    if schema.get("type") == "array":
        if "minItems" in schema:
            field_kwargs["min_length"] = schema["minItems"]
        if "maxItems" in schema:
            field_kwargs["max_length"] = schema["maxItems"]
        if "uniqueItems" in schema and schema["uniqueItems"]:
            field_kwargs["json_schema_extra"] = {"uniqueItems": True}

    # Enum constraint
    if "enum" in schema:
        # Enum is handled via Literal type, but we store it for reference
        field_kwargs["json_schema_extra"] = field_kwargs.get("json_schema_extra", {})
        field_kwargs["json_schema_extra"]["enum"] = schema["enum"]

    # Const constraint (single allowed value)
    if "const" in schema:
        field_kwargs["json_schema_extra"] = field_kwargs.get("json_schema_extra", {})
        field_kwargs["json_schema_extra"]["const"] = schema["const"]

    # Description
    if "description" in schema:
        field_kwargs["description"] = schema["description"]

    # Title
    if "title" in schema:
        field_kwargs["title"] = schema["title"]

    # Examples
    if "examples" in schema:
        field_kwargs["json_schema_extra"] = field_kwargs.get("json_schema_extra", {})
        field_kwargs["json_schema_extra"]["examples"] = schema["examples"]

    return field_kwargs


def create_enum_validator(enum_values: List[Any]):
    """
    Create a validator for JSON Schema enum constraint.

    Args:
        enum_values: List of allowed enum values

    Returns:
        Validation function
    """

    def _enum_validator(value: Any, info: ValidationInfo) -> Any:
        if value not in enum_values:
            raise ValueError(f"Value must be one of {enum_values}, got {value}")
        return value

    return _enum_validator


def create_const_validator(const_value: Any):
    """
    Create a validator for JSON Schema const constraint.

    Args:
        const_value: The single allowed value

    Returns:
        Validation function
    """

    def _const_validator(value: Any, info: ValidationInfo) -> Any:
        if value != const_value:
            raise ValueError(f"Value must be exactly {const_value}, got {value}")
        return value

    return _const_validator


def create_pattern_validator(pattern: str):
    """
    Create a validator for JSON Schema pattern constraint.

    Args:
        pattern: Regular expression pattern

    Returns:
        Validation function
    """
    import re

    compiled_pattern = re.compile(pattern)

    def _pattern_validator(value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return value
        if isinstance(value, str):
            if not compiled_pattern.match(value):
                raise ValueError(f"Value must match pattern '{pattern}', got '{value}'")
        return value

    return _pattern_validator


def create_unique_items_validator(value: Any, info: ValidationInfo) -> Any:
    """
    Validator for uniqueItems constraint on arrays.

    Args:
        value: The array value
        info: Validation info

    Returns:
        Validated value

    Raises:
        ValidationError: If array contains duplicate items
    """
    if value is None:
        return value
    if isinstance(value, list):
        if len(value) != len(set(value)):
            raise ValueError("Array must contain unique items")
    return value
