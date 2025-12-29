"""
Coercion functions for pre-validation data transformation.
These functions are applied before Pydantic validation (mode='before').
"""

from typing import Any, Callable, Dict

from pycharter.shared.coercions.builtin import (
    coerce_empty_to_null,
    coerce_to_boolean,
    coerce_to_date,
    coerce_to_datetime,
    coerce_to_float,
    coerce_to_integer,
    coerce_to_json,
    coerce_to_list,
    coerce_to_lowercase,
    coerce_to_none,
    coerce_to_nullable_boolean,
    coerce_to_nullable_datetime,
    coerce_to_nullable_float,
    coerce_to_nullable_integer,
    coerce_to_nullable_json,
    coerce_to_nullable_string,
    coerce_to_nullable_uuid,
    coerce_to_string,
    coerce_to_stripped_string,
    coerce_to_uppercase,
    coerce_to_uuid,
)

# Registry of available coercion functions
COERCION_REGISTRY: Dict[str, Callable[[Any], Any]] = {
    # Standard coercions
    "coerce_to_string": coerce_to_string,
    "coerce_to_integer": coerce_to_integer,
    "coerce_to_float": coerce_to_float,
    "coerce_to_boolean": coerce_to_boolean,
    "coerce_to_datetime": coerce_to_datetime,
    "coerce_to_date": coerce_to_date,
    "coerce_to_uuid": coerce_to_uuid,
    "coerce_to_lowercase": coerce_to_lowercase,
    "coerce_to_uppercase": coerce_to_uppercase,
    "coerce_to_stripped_string": coerce_to_stripped_string,
    "coerce_to_list": coerce_to_list,
    "coerce_empty_to_null": coerce_empty_to_null,
    # New coercions
    "coerce_to_none": coerce_to_none,
    "coerce_to_json": coerce_to_json,
    # Nullable variants (explicitly handle null values for optional fields)
    "coerce_to_nullable_string": coerce_to_nullable_string,
    "coerce_to_nullable_integer": coerce_to_nullable_integer,
    "coerce_to_nullable_float": coerce_to_nullable_float,
    "coerce_to_nullable_boolean": coerce_to_nullable_boolean,
    "coerce_to_nullable_datetime": coerce_to_nullable_datetime,
    "coerce_to_nullable_uuid": coerce_to_nullable_uuid,
    "coerce_to_nullable_json": coerce_to_nullable_json,
}


def get_coercion(name: str) -> Callable[[Any], Any]:
    """
    Get a coercion function by name.

    Args:
        name: Name of the coercion function

    Returns:
        The coercion function

    Raises:
        ValueError: If coercion function not found
    """
    if name not in COERCION_REGISTRY:
        raise ValueError(
            f"Coercion function '{name}' not found. "
            f"Available: {list(COERCION_REGISTRY.keys())}"
        )
    return COERCION_REGISTRY[name]


def register_coercion(name: str, func: Callable[[Any], Any]) -> None:
    """
    Register a custom coercion function.

    Args:
        name: Name to register the function under
        func: The coercion function
    """
    COERCION_REGISTRY[name] = func
