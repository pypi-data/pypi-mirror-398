"""
JSON Schema validator module.

Validates that schemas conform to JSON Schema standard before processing.
Supports both standard JSON Schema and charter extensions.
"""

from typing import Any, Dict

try:
    import jsonschema  # type: ignore[import-untyped]
    from jsonschema import (  # type: ignore[import-untyped]
        Draft202012Validator,
    )
    from jsonschema import (
        ValidationError as JSONSchemaValidationError,  # type: ignore[import-untyped]
    )

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    JSONSchemaValidationError = Exception


# Charter extension fields (allowed in addition to JSON Schema standard)
CHARTER_EXTENSIONS = {
    "coercion",  # Pre-validation type coercion
    "validations",  # Post-validation rules
}


def validate_json_schema(schema: Dict[str, Any], strict: bool = False) -> None:
    """
    Validate that a schema conforms to JSON Schema standard.

    This function validates that the schema follows JSON Schema Draft 2020-12
    specification, while allowing charter extension fields.

    Args:
        schema: The schema dictionary to validate
        strict: If True, only allow standard JSON Schema fields (no extensions)

    Raises:
        ValueError: If the schema is invalid
        jsonschema.ValidationError: If schema doesn't conform to JSON Schema standard

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {"type": "string"}
        ...     }
        ... }
        >>> validate_json_schema(schema)  # Valid JSON Schema
    """
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")

    if not JSONSCHEMA_AVAILABLE:
        # Fallback validation if jsonschema is not available
        _basic_validation(schema)
        return

    # Create a copy without charter extensions for validation
    if strict:
        schema_to_validate = schema
    else:
        schema_to_validate = _remove_charter_extensions(schema)

    # First do basic validation to catch obvious issues
    _basic_validation(schema)

    try:
        # Validate against JSON Schema Draft 2020-12
        Draft202012Validator.check_schema(schema_to_validate)
    except JSONSchemaValidationError as e:
        raise ValueError(
            f"Schema does not conform to JSON Schema standard: {e.message}"
        ) from e


def _remove_charter_extensions(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove charter extension fields from schema for JSON Schema validation.

    Args:
        schema: The schema dictionary

    Returns:
        Schema without charter extensions
    """
    if not isinstance(schema, dict):
        return schema

    cleaned = {}
    for key, value in schema.items():
        if key in CHARTER_EXTENSIONS:
            continue

        if isinstance(value, dict):
            cleaned[key] = _remove_charter_extensions(value)
        elif isinstance(value, list):
            cleaned[key] = [  # type: ignore[assignment]
                _remove_charter_extensions(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            cleaned[key] = value

    return cleaned


def _basic_validation(schema: Dict[str, Any]) -> None:
    """
    Basic validation when jsonschema library is not available.

    Args:
        schema: The schema dictionary to validate

    Raises:
        ValueError: If the schema is invalid
    """
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")

    # Check for required JSON Schema fields
    # Note: anyOf, oneOf, allOf are also valid JSON Schema constructs
    if (
        "type" not in schema
        and "properties" not in schema
        and "$ref" not in schema
        and "anyOf" not in schema
        and "oneOf" not in schema
        and "allOf" not in schema
    ):
        raise ValueError(
            "Schema must have 'type', 'properties', '$ref', 'anyOf', 'oneOf', or 'allOf' field to be valid JSON Schema"
        )

    # Validate properties if present
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise ValueError("'properties' must be a dictionary")

        # Validate each property
        for prop_name, prop_schema in schema["properties"].items():
            if not isinstance(prop_schema, dict):
                raise ValueError(f"Property '{prop_name}' must be a dictionary")

            # Skip PyCharter extension fields when recursively validating
            # (coercion and validations are not schema properties)
            if prop_name in ("coercion", "validations"):
                continue

            # Recursively validate nested schemas
            _basic_validation(prop_schema)

    # Validate items if present (for arrays)
    if "items" in schema:
        if isinstance(schema["items"], dict):
            _basic_validation(schema["items"])
        elif isinstance(schema["items"], list):
            for item_schema in schema["items"]:
                if isinstance(item_schema, dict):
                    _basic_validation(item_schema)


def is_valid_json_schema(schema: Dict[str, Any]) -> bool:
    """
    Check if a schema is valid JSON Schema without raising exceptions.

    Args:
        schema: The schema dictionary to check

    Returns:
        True if valid, False otherwise
    """
    try:
        validate_json_schema(schema)
        return True
    except (ValueError, JSONSchemaValidationError):
        return False


def get_charter_extensions(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract charter extension fields from a schema.

    Args:
        schema: The schema dictionary

    Returns:
        Dictionary of charter extensions found
    """
    extensions = {}

    if "coercion" in schema:
        extensions["coercion"] = schema["coercion"]

    if "validations" in schema:
        extensions["validations"] = schema["validations"]

    return extensions
