"""
Runtime Validator - Lightweight validation utility.

Uses generated Pydantic models to validate data in data processing scripts.
"""

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ValidationError


class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed
        data: Validated data (Pydantic model instance) if valid
        errors: List of validation errors if invalid
    """

    def __init__(
        self,
        is_valid: bool,
        data: Optional[BaseModel] = None,
        errors: Optional[List[str]] = None,
    ):
        self.is_valid = is_valid
        self.data = data
        self.errors = errors or []

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid


def validate(
    model: Type[BaseModel],
    data: Dict[str, Any],
    strict: bool = False,
) -> ValidationResult:
    """
    Validate data against a Pydantic model.

    Args:
        model: Pydantic model class (generated from JSON Schema)
        data: Data dictionary to validate
        strict: If True, raise exceptions on validation errors

    Returns:
        ValidationResult object

    Raises:
        ValidationError: If strict=True and validation fails

    Example:
        >>> from pycharter.pydantic_generator import from_dict
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> Person = from_dict(schema, "Person")
        >>> result = validate(Person, {"name": "Alice"})
        >>> result.is_valid
        True
        >>> result.data.name
        'Alice'
    """
    try:
        instance = model(**data)
        return ValidationResult(is_valid=True, data=instance)
    except ValidationError as e:
        errors = [str(err) for err in e.errors()]
        if strict:
            raise
        return ValidationResult(is_valid=False, errors=errors)
    except Exception as e:
        errors = [f"Unexpected error: {str(e)}"]
        if strict:
            raise
        return ValidationResult(is_valid=False, errors=errors)


def validate_batch(
    model: Type[BaseModel],
    data_list: List[Dict[str, Any]],
    strict: bool = False,
) -> List[ValidationResult]:
    """
    Validate a batch of data items against a Pydantic model.

    Args:
        model: Pydantic model class
        data_list: List of data dictionaries to validate
        strict: If True, stop on first validation error

    Returns:
        List of ValidationResult objects

    Example:
        >>> results = validate_batch(Person, [{"name": "Alice"}, {"name": "Bob"}])
        >>> all(r.is_valid for r in results)
        True
    """
    results = []
    for data in data_list:
        result = validate(model, data, strict=strict)
        results.append(result)
        if strict and not result.is_valid:
            break
    return results
