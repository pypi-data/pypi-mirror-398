"""
Built-in validation functions for common validation rules.
"""

import re
from typing import Any, List

from pydantic import ValidationInfo


def min_length(threshold: int):
    """
    Factory function to create a min_length validator.

    Args:
        threshold: Minimum length required

    Returns:
        Validation function
    """

    def _min_length(value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return value
        if isinstance(value, str):
            if len(value) < threshold:
                raise ValueError(
                    f"String must be at least {threshold} characters long, got {len(value)}"
                )
        elif isinstance(value, (list, dict)):
            if len(value) < threshold:
                raise ValueError(
                    f"Value must have at least {threshold} items, got {len(value)}"
                )
        return value

    return _min_length


def max_length(threshold: int):
    """
    Factory function to create a max_length validator.

    Args:
        threshold: Maximum length allowed

    Returns:
        Validation function
    """

    def _max_length(value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return value
        if isinstance(value, str):
            if len(value) > threshold:
                raise ValueError(
                    f"String must be at most {threshold} characters long, got {len(value)}"
                )
        elif isinstance(value, (list, dict)):
            if len(value) > threshold:
                raise ValueError(
                    f"Value must have at most {threshold} items, got {len(value)}"
                )
        return value

    return _max_length


def only_allow(allowed_values: List[Any]):
    """
    Factory function to create an only_allow validator.

    Args:
        allowed_values: List of allowed values

    Returns:
        Validation function
    """

    def _only_allow(value: Any, info: ValidationInfo) -> Any:
        if value not in allowed_values:
            raise ValueError(f"Value must be one of {allowed_values}, got {value}")
        return value

    return _only_allow


def only_allow_if(condition: dict):
    """
    Factory function to create a conditional only_allow validator.

    Args:
        condition: Dict with 'field' and 'value' keys for conditional check

    Returns:
        Validation function
    """

    def _only_allow_if(value: Any, info: ValidationInfo) -> Any:
        # This is a simplified version - full implementation would check other fields
        # For now, just return the value
        return value

    return _only_allow_if


def greater_than_or_equal_to(threshold: float):
    """
    Factory function to create a greater_than_or_equal_to validator.

    Args:
        threshold: Minimum value allowed

    Returns:
        Validation function
    """

    def _gte(value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return value
        if isinstance(value, (int, float)):
            if value < threshold:
                raise ValueError(f"Value must be >= {threshold}, got {value}")
        return value

    return _gte


def less_than_or_equal_to(threshold: float):
    """
    Factory function to create a less_than_or_equal_to validator.

    Args:
        threshold: Maximum value allowed

    Returns:
        Validation function
    """

    def _lte(value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return value
        if isinstance(value, (int, float)):
            if value > threshold:
                raise ValueError(f"Value must be <= {threshold}, got {value}")
        return value

    return _lte


def no_capital_characters():
    """
    Factory function to create a no_capital_characters validator.

    Returns:
        Validation function
    """

    def _no_capital_characters(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that string contains no capital characters.

        Returns:
            Validated value

        Raises:
            ValidationError: If string contains capital characters
        """
        if value is None:
            return value
        if isinstance(value, str):
            if any(c.isupper() for c in value):
                raise ValueError("String must not contain capital characters")
        return value

    return _no_capital_characters


def is_positive(threshold: int = 0):
    """
    Factory function to create an is_positive validator.

    Args:
        threshold: Minimum value (default 0, meaning must be > 0)

    Returns:
        Validation function
    """

    def _is_positive(value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return value
        if isinstance(value, (int, float)):
            if value <= threshold:
                raise ValueError(f"Value must be greater than {threshold}, got {value}")
        return value

    return _is_positive


def non_empty_string():
    """
    Factory function to create a non_empty_string validator.

    Returns:
        Validation function
    """

    def _non_empty_string(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that string is not empty.

        Returns:
            Validated value

        Raises:
            ValidationError: If string is empty
        """
        if value is None:
            return value
        if isinstance(value, str):
            if len(value.strip()) == 0:
                raise ValueError("String must not be empty")
        return value

    return _non_empty_string


def no_special_characters():
    """
    Factory function to create a no_special_characters validator.

    Returns:
        Validation function
    """

    def _no_special_characters(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that string contains no special characters (only alphanumeric).

        Returns:
            Validated value

        Raises:
            ValidationError: If string contains special characters
        """
        if value is None:
            return value
        if isinstance(value, str):
            if not re.match(r"^[a-zA-Z0-9\s]*$", value):
                raise ValueError(
                    "String must contain only alphanumeric characters and spaces"
                )
        return value

    return _no_special_characters


def matches_regex(pattern: str):
    """
    Factory function to create a matches_regex validator.

    Args:
        pattern: Regular expression pattern to match

    Returns:
        Validation function
    """

    def _matches_regex(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that string matches the given regex pattern.

        Returns:
            Validated value

        Raises:
            ValidationError: If string doesn't match pattern
        """
        if value is None:
            return value
        if isinstance(value, str):
            if not re.match(pattern, value):
                raise ValueError(
                    f"String must match pattern '{pattern}', got '{value}'"
                )
        return value

    return _matches_regex


def is_email():
    """
    Factory function to create an is_email validator.

    Returns:
        Validation function
    """

    def _is_email(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that string is a valid email address.

        Returns:
            Validated value

        Raises:
            ValidationError: If string is not a valid email
        """
        if value is None:
            return value
        if isinstance(value, str):
            # Basic email regex (RFC 5322 simplified)
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, value):
                raise ValueError(f"String must be a valid email address, got '{value}'")
        return value

    return _is_email


def is_url():
    """
    Factory function to create an is_url validator.

    Returns:
        Validation function
    """

    def _is_url(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that string is a valid URL.

        Returns:
            Validated value

        Raises:
            ValidationError: If string is not a valid URL
        """
        if value is None:
            return value
        if isinstance(value, str):
            # Basic URL pattern
            url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
            if not re.match(url_pattern, value):
                raise ValueError(f"String must be a valid URL, got '{value}'")
        return value

    return _is_url


def is_alphanumeric():
    """
    Factory function to create an is_alphanumeric validator.

    Returns:
        Validation function
    """

    def _is_alphanumeric(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that string contains only alphanumeric characters (no spaces or special chars).

        Returns:
            Validated value

        Raises:
            ValidationError: If string contains non-alphanumeric characters
        """
        if value is None:
            return value
        if isinstance(value, str):
            if not value.isalnum():
                raise ValueError(
                    f"String must contain only alphanumeric characters, got '{value}'"
                )
        return value

    return _is_alphanumeric


def is_numeric_string():
    """
    Factory function to create an is_numeric_string validator.

    Returns:
        Validation function
    """

    def _is_numeric_string(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that string contains only numeric characters (digits, optionally with decimal point).

        Returns:
            Validated value

        Raises:
            ValidationError: If string is not numeric
        """
        if value is None:
            return value
        if isinstance(value, str):
            if not re.match(r"^-?\d+(\.\d+)?$", value):
                raise ValueError(f"String must be numeric, got '{value}'")
        return value

    return _is_numeric_string


def is_unique():
    """
    Factory function to create an is_unique validator for arrays.

    Returns:
        Validation function
    """

    def _is_unique(value: Any, info: ValidationInfo) -> Any:
        """
        Validate that all items in a list are unique.

        Returns:
            Validated value

        Raises:
            ValidationError: If list contains duplicate items
        """
        if value is None:
            return value
        if isinstance(value, list):
            if len(value) != len(set(value)):
                raise ValueError("List must contain only unique items")
        return value

    return _is_unique
