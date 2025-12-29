"""
Validation functions for post-validation checks.
These functions are applied after Pydantic validation (mode='after').
"""

from typing import Any, Callable, Dict

from pydantic import ValidationInfo

from pycharter.shared.validations.builtin import (
    greater_than_or_equal_to,
    is_alphanumeric,
    is_email,
    is_numeric_string,
    is_positive,
    is_unique,
    is_url,
    less_than_or_equal_to,
    matches_regex,
    max_length,
    min_length,
    no_capital_characters,
    no_special_characters,
    non_empty_string,
    only_allow,
    only_allow_if,
)

# Registry of available validation functions
VALIDATION_REGISTRY: Dict[str, Callable] = {
    "min_length": min_length,
    "max_length": max_length,
    "only_allow": only_allow,
    "only_allow_if": only_allow_if,
    "greater_than_or_equal_to": greater_than_or_equal_to,
    "less_than_or_equal_to": less_than_or_equal_to,
    "no_capital_characters": no_capital_characters,
    "no_special_characters": no_special_characters,
    "is_positive": is_positive,
    "non_empty_string": non_empty_string,
    "matches_regex": matches_regex,
    "is_email": is_email,
    "is_url": is_url,
    "is_alphanumeric": is_alphanumeric,
    "is_numeric_string": is_numeric_string,
    "is_unique": is_unique,
}


def get_validation(name: str) -> Callable:
    """
    Get a validation function factory by name.

    Args:
        name: Name of the validation function

    Returns:
        The validation function factory

    Raises:
        ValueError: If validation function not found
    """
    if name not in VALIDATION_REGISTRY:
        raise ValueError(
            f"Validation function '{name}' not found. "
            f"Available: {list(VALIDATION_REGISTRY.keys())}"
        )
    return VALIDATION_REGISTRY[name]


def register_validation(name: str, func: Callable) -> None:
    """
    Register a custom validation function.

    Args:
        name: Name to register the function under
        func: The validation function factory
    """
    VALIDATION_REGISTRY[name] = func
