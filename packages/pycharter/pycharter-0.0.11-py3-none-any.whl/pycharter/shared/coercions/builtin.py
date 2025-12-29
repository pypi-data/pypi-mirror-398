"""
Built-in coercion functions for common type conversions.
"""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

import numpy as np  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]


def _is_null_value(data: Any) -> bool:
    """
    Check if a value is null/NaN/NaT.

    Handles pandas types (pd.NA, pd.NaT), numpy nan, None, and string representations.

    Args:
        data: The value to check

    Returns:
        True if the value is null/NaN/NaT, False otherwise
    """
    if data is None:
        return True
    try:
        return pd.isnull(data)
    except (TypeError, ValueError):
        # pd.isnull can raise TypeError for some types (e.g., dict, list)
        # Check for string representations of null
        if isinstance(data, str):
            return data.strip().lower() in ("nan", "nat", "null", "none", "")
    return False


def coerce_to_string(data: Any) -> str:
    """
    Coerce various types to string.

    Converts: int, float, bool, datetime, dict, list -> str
    Raises ValueError if conversion fails or if data is null.

    Note: This is a strict coercion - must succeed or error.
    Use coerce_to_nullable_string for optional fields that can be None.

    Raises:
        ValueError: If data cannot be converted to string or is null
    """
    if _is_null_value(data):
        raise ValueError(f"Cannot coerce null value to string: {data}")

    if isinstance(data, str):
        return data
    elif isinstance(data, (int, float, bool)):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, pd.Timestamp):
        return data.isoformat()
    elif isinstance(data, (dict, list)):
        return json.dumps(data)
    else:
        raise ValueError(f"Cannot coerce {type(data).__name__} to string: {data}")


def coerce_to_integer(data: Any) -> int:
    """
    Coerce various types to integer.

    Converts: float, str (numeric), bool, datetime -> int
    Raises ValueError if conversion fails or if data is null.

    Note: This is a strict coercion - must succeed or error.
    Use coerce_to_nullable_integer for optional fields that can be None.

    Raises:
        ValueError: If data cannot be converted to integer or is null
    """
    if _is_null_value(data):
        raise ValueError(f"Cannot coerce null value to integer: {data}")

    if isinstance(data, int):
        return data
    elif isinstance(data, float):
        if _is_null_value(data):
            raise ValueError(f"Cannot coerce null value to integer: {data}")
        return int(data)
    elif isinstance(data, bool):
        return int(data)
    elif isinstance(data, str):
        if _is_null_value(data):
            raise ValueError(f"Cannot coerce null value to integer: {data}")
        try:
            return int(float(data))  # Handle "3.14" -> 3
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot coerce '{data}' to integer: {e}")
    elif isinstance(data, datetime):
        return int(data.timestamp())
    elif isinstance(data, pd.Timestamp):
        return int(data.timestamp())
    else:
        raise ValueError(f"Cannot coerce {type(data).__name__} to integer: {data}")


def coerce_to_float(data: Any) -> float:
    """
    Coerce various types to float.

    Converts: int, str (numeric), bool -> float
    Raises ValueError if conversion fails or if data is null.

    Note: This is a strict coercion - must succeed or error.
    Use coerce_to_nullable_float for optional fields that can be None.

    Raises:
        ValueError: If data cannot be converted to float or is null
    """
    if _is_null_value(data):
        raise ValueError(f"Cannot coerce null value to float: {data}")

    if isinstance(data, (int, float)):
        if _is_null_value(data):
            raise ValueError(f"Cannot coerce null value to float: {data}")
        return float(data)
    elif isinstance(data, bool):
        return float(data)
    elif isinstance(data, str):
        if _is_null_value(data):
            raise ValueError(f"Cannot coerce null value to float: {data}")
        try:
            return float(data)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot coerce '{data}' to float: {e}")
    else:
        raise ValueError(f"Cannot coerce {type(data).__name__} to float: {data}")


def coerce_to_boolean(data: Any) -> bool:
    """
    Coerce various types to boolean.

    Converts: int (0/1), str ("true"/"false"), str ("1"/"0") -> bool
    Raises ValueError if conversion fails or if data is null.

    Note: This is a strict coercion - must succeed or error.
    Use coerce_to_nullable_boolean for optional fields that can be None.

    Raises:
        ValueError: If data cannot be converted to boolean or is null
    """
    if _is_null_value(data):
        raise ValueError(f"Cannot coerce null value to boolean: {data}")

    if isinstance(data, bool):
        return data
    elif isinstance(data, int):
        return bool(data)
    elif isinstance(data, float):
        if _is_null_value(data):
            raise ValueError(f"Cannot coerce null value to boolean: {data}")
        return bool(data)
    elif isinstance(data, str):
        lower = data.lower().strip()
        if lower in ("true", "1", "yes", "on"):
            return True
        elif lower in ("false", "0", "no", "off"):
            return False
        elif lower == "":
            return False  # Empty string -> False
        else:
            raise ValueError(f"Cannot coerce '{data}' to boolean: unrecognized value")
    else:
        raise ValueError(f"Cannot coerce {type(data).__name__} to boolean: {data}")


def coerce_to_datetime(data: Any) -> datetime:
    """
    Coerce various types to datetime.

    Converts: str (ISO format), int/float (timestamp) -> datetime
    Raises ValueError if conversion fails or if data is null.

    Note: This is a strict coercion - must succeed or error.
    Use coerce_to_nullable_datetime for optional fields that can be None.

    Raises:
        ValueError: If data cannot be converted to datetime or is null
    """
    if _is_null_value(data):
        raise ValueError(f"Cannot coerce null value to datetime: {data}")

    if isinstance(data, datetime):
        return data
    elif isinstance(data, pd.Timestamp):
        # Convert pandas Timestamp to datetime
        return data.to_pydatetime()
    elif isinstance(data, str):
        # Handle empty/null strings
        if _is_null_value(data) or len(data.strip()) == 0:
            raise ValueError(f"Cannot coerce empty/null string to datetime: {data}")
        try:
            # Try ISO format first
            return datetime.fromisoformat(data.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(data, fmt)
                except ValueError:
                    continue
            # Try pandas parsing (more flexible, handles many date formats)
            try:
                dt = pd.to_datetime(data)
                if pd.isnull(dt):
                    raise ValueError(
                        f"Cannot coerce '{data}' to datetime: result is null"
                    )
                return dt.to_pydatetime()
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cannot coerce '{data}' to datetime: {e}")
    elif isinstance(data, (int, float)):
        if _is_null_value(data):
            raise ValueError(f"Cannot coerce null value to datetime: {data}")
        try:
            return datetime.fromtimestamp(data)
        except (ValueError, OSError) as e:
            raise ValueError(f"Cannot coerce timestamp {data} to datetime: {e}")
    else:
        raise ValueError(f"Cannot coerce {type(data).__name__} to datetime: {data}")


def coerce_to_lowercase(data: Any) -> Any:
    """
    Coerce string to lowercase.

    Args:
        data: The data to coerce

    Returns:
        Lowercase string if input is string, None if None, otherwise original value

    Note: None values are preserved (not converted).
    """
    if data is None:
        return None
    if isinstance(data, str):
        return data.lower()
    return data


def coerce_to_uuid(data: Any) -> UUID:
    """
    Coerce string to UUID.

    Converts: str (UUID format) -> UUID
    Raises ValueError if conversion fails or if data is null.

    Note: This is a strict coercion - must succeed or error.
    Use coerce_to_nullable_uuid for optional fields that can be None.

    Raises:
        ValueError: If data cannot be converted to UUID or is null
    """
    if _is_null_value(data):
        raise ValueError(f"Cannot coerce null value to UUID: {data}")

    if isinstance(data, UUID):
        return data
    elif isinstance(data, str):
        if _is_null_value(data) or len(data.strip()) == 0:
            raise ValueError(f"Cannot coerce empty/null string to UUID: {data}")
        try:
            return UUID(data)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Cannot coerce '{data}' to UUID: {e}")
    else:
        raise ValueError(f"Cannot coerce {type(data).__name__} to UUID: {data}")


def coerce_to_uppercase(data: Any) -> Any:
    """
    Coerce string to uppercase.

    Args:
        data: The data to coerce

    Returns:
        Uppercase string if input is string, None if None, otherwise original value

    Note: None values are preserved (not converted).
    """
    if data is None:
        return None
    if isinstance(data, str):
        return data.upper()
    return data


def coerce_to_stripped_string(data: Any) -> Any:
    """
    Coerce string by stripping leading and trailing whitespace.

    Args:
        data: The data to coerce

    Returns:
        Stripped string if input is string, None if None, otherwise original value

    Note: None values are preserved (not converted).
    """
    if data is None:
        return None
    if isinstance(data, str):
        return data.strip()
    return data


def coerce_to_list(data: Any) -> Any:
    """
    Coerce single value to list.

    Converts: single value -> [value]
    Returns lists as-is.

    Note: None values are preserved (not converted to []).
    This allows nullable fields to remain None.
    If you want None -> [], use coerce_to_list_allow_none or handle separately.
    """
    if data is None:
        return None
    if isinstance(data, list):
        return data
    else:
        return [data]


def coerce_to_date(data: Any) -> Any:
    """
    Coerce various types to date (date only, no time).

    Converts: str (date format), datetime -> date
    Returns None and other types as-is.

    Note: None values are preserved (not converted).
    For nullable date fields, None will pass through unchanged.
    Use coerce_empty_to_null if you want empty strings to become None.
    """
    from datetime import date

    if data is None:
        return None
    if isinstance(data, date):
        return data
    elif isinstance(data, datetime):
        return data.date()
    elif isinstance(data, str):
        # Handle empty strings - return as-is (don't try to parse)
        if len(data.strip()) == 0:
            return data
        try:
            # Try ISO format first
            return datetime.fromisoformat(data.replace("Z", "+00:00")).date()
        except (ValueError, AttributeError):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(data, fmt).date()
                except ValueError:
                    continue
    return data


def coerce_empty_to_null(data: Any) -> Any:
    """
    Coerce empty values to None (null).

    Converts empty strings, empty lists, empty dicts to None.
    Useful for nullable fields where empty values should be treated as null.

    Args:
        data: The data to coerce

    Returns:
        None if input is empty (empty string, empty list, empty dict),
        otherwise original value
    """
    if data is None:
        return None
    elif isinstance(data, str) and len(data.strip()) == 0:
        return None
    elif isinstance(data, list) and len(data) == 0:
        return None
    elif isinstance(data, dict) and len(data) == 0:
        return None
    return data


def coerce_to_none(data: Any) -> Any:
    """
    Coerce all null/NaN/NaT values to None.

    Converts pandas null types (pd.NA, pd.NaT), numpy nan, None, and string
    representations of null to Python None.

    Useful as a preprocessing step before validation to normalize all null types.

    Args:
        data: The data to coerce

    Returns:
        None if input is null/NaN/NaT, otherwise original value

    Examples:
        >>> coerce_to_none(pd.NA)
        None
        >>> coerce_to_none(pd.NaT)
        None
        >>> coerce_to_none(np.nan)
        None
        >>> coerce_to_none("nan")
        None
        >>> coerce_to_none("value")
        'value'
    """
    if _is_null_value(data):
        return None
    return data


def coerce_to_json(data: Any) -> Any:
    """
    Coerce dict or string to JSON string.

    Converts dict to JSON string, or evaluates string representation of dict
    to JSON string. Useful for fields that should store JSON data.

    Args:
        data: The data to coerce (dict or str)

    Returns:
        JSON string if input is dict or string representation of dict,
        otherwise original value

    Examples:
        >>> coerce_to_json({"key": "value"})
        '{"key": "value"}'
        >>> coerce_to_json('{"key": "value"}')
        '{"key": "value"}'
    """
    if isinstance(data, dict):
        return json.dumps(data)
    elif isinstance(data, str):
        # Try to parse as dict and convert to JSON
        try:
            import ast

            evaluated = ast.literal_eval(data)
            if isinstance(evaluated, dict):
                return json.dumps(evaluated)
        except (ValueError, SyntaxError):
            # If it's already valid JSON, return as-is
            try:
                json.loads(data)  # Validate it's JSON
                return data
            except (ValueError, TypeError):
                pass
    return data


def coerce_to_nullable_string(data: Any) -> str | None:
    """
    Coerce various types to string, returning None if conversion fails or data is null.

    Similar to coerce_to_string but returns None instead of raising errors.
    Use for optional fields that can be None.

    Args:
        data: The data to coerce

    Returns:
        String value if conversion succeeds, None if null or conversion fails
    """
    if _is_null_value(data):
        return None

    if isinstance(data, str):
        # Handle string representations of null
        if _is_null_value(data):
            return None
        return data
    elif isinstance(data, (int, float, bool)):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, pd.Timestamp):
        return data.isoformat()
    elif isinstance(data, (dict, list)):
        try:
            return json.dumps(data)
        except (TypeError, ValueError):
            return None
    else:
        return None  # Cannot convert, return None


def coerce_to_nullable_integer(data: Any) -> int | None:
    """
    Coerce various types to integer, returning None if conversion fails or data is null.

    Similar to coerce_to_integer but returns None instead of raising errors.
    Use for optional fields that can be None.

    Args:
        data: The data to coerce

    Returns:
        Integer value if conversion succeeds, None if null or conversion fails
    """
    if _is_null_value(data):
        return None

    if isinstance(data, int):
        return data
    elif isinstance(data, float):
        if _is_null_value(data):
            return None
        try:
            return int(data)
        except (ValueError, TypeError):
            return None
    elif isinstance(data, bool):
        return int(data)
    elif isinstance(data, str):
        if _is_null_value(data):
            return None
        try:
            return int(float(data))  # Handle "3.14" -> 3
        except (ValueError, TypeError):
            return None
    elif isinstance(data, datetime):
        return int(data.timestamp())
    elif isinstance(data, pd.Timestamp):
        return int(data.timestamp())
    else:
        return None  # Cannot convert, return None


def coerce_to_nullable_float(data: Any) -> float | None:
    """
    Coerce various types to float, returning None if conversion fails or data is null.

    Similar to coerce_to_float but returns None instead of raising errors.
    Use for optional fields that can be None.

    Args:
        data: The data to coerce

    Returns:
        Float value if conversion succeeds, None if null or conversion fails
    """
    if _is_null_value(data):
        return None

    if isinstance(data, (int, float)):
        if _is_null_value(data):
            return None
        try:
            return float(data)
        except (ValueError, TypeError):
            return None
    elif isinstance(data, bool):
        return float(data)
    elif isinstance(data, str):
        if _is_null_value(data):
            return None
        try:
            return float(data)
        except (ValueError, TypeError):
            return None
    else:
        return None  # Cannot convert, return None


def coerce_to_nullable_boolean(data: Any) -> bool | None:
    """
    Coerce various types to boolean, returning None if conversion fails or data is null.

    Similar to coerce_to_boolean but returns None instead of raising errors.
    Use for optional fields that can be None.

    Args:
        data: The data to coerce

    Returns:
        Boolean value if conversion succeeds, None if null or conversion fails
    """
    if _is_null_value(data):
        return None

    if isinstance(data, bool):
        return data
    elif isinstance(data, int):
        return bool(data)
    elif isinstance(data, float):
        if _is_null_value(data):
            return None
        return bool(data)
    elif isinstance(data, str):
        lower = data.lower().strip()
        if lower in ("true", "1", "yes", "on"):
            return True
        elif lower in ("false", "0", "no", "off"):
            return False
        elif _is_null_value(data) or lower == "":
            return None
        else:
            return None  # Cannot convert, return None
    else:
        return None  # Cannot convert, return None


def coerce_to_nullable_datetime(data: Any) -> datetime | None:
    """
    Coerce various types to datetime, returning None if conversion fails or data is null.

    Similar to coerce_to_datetime but returns None instead of raising errors.
    Use for optional fields that can be None.

    Args:
        data: The data to coerce

    Returns:
        Datetime object if conversion succeeds, None if null or conversion fails
    """
    if _is_null_value(data):
        return None

    if isinstance(data, datetime):
        return data
    elif isinstance(data, pd.Timestamp):
        return data.to_pydatetime()
    elif isinstance(data, str):
        if _is_null_value(data) or len(data.strip()) == 0:
            return None
        try:
            # Try ISO format first
            return datetime.fromisoformat(data.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(data, fmt)
                except ValueError:
                    continue
            # Try pandas parsing (more flexible, handles many date formats)
            try:
                dt = pd.to_datetime(data)
                if pd.isnull(dt):
                    return None
                return dt.to_pydatetime()
            except (ValueError, TypeError):
                return None
    elif isinstance(data, (int, float)):
        if _is_null_value(data):
            return None
        try:
            return datetime.fromtimestamp(data)
        except (ValueError, OSError):
            return None
    else:
        return None  # Cannot convert, return None


def coerce_to_nullable_uuid(data: Any) -> UUID | None:
    """
    Coerce string to UUID, returning None if conversion fails or data is null.

    Similar to coerce_to_uuid but returns None instead of raising errors.
    Use for optional fields that can be None.

    Args:
        data: The data to coerce

    Returns:
        UUID object if conversion succeeds, None if null or conversion fails
    """
    if _is_null_value(data):
        return None

    if isinstance(data, UUID):
        return data
    elif isinstance(data, str):
        if _is_null_value(data) or len(data.strip()) == 0:
            return None
        try:
            return UUID(data)
        except (ValueError, AttributeError):
            return None
    else:
        return None  # Cannot convert, return None


def coerce_to_nullable_json(data: Any) -> str | None:
    """
    Coerce dict or string to JSON string, returning None if conversion fails or data is null.

    Similar to coerce_to_json but returns None instead of raising errors.
    Use for optional fields that can be None and need to store objects as JSON strings
    for database compatibility.

    Args:
        data: The data to coerce (dict, str, or None)

    Returns:
        JSON string if conversion succeeds, None if null or conversion fails
    """
    if _is_null_value(data):
        return None

    if isinstance(data, dict):
        try:
            return json.dumps(data)
        except (TypeError, ValueError):
            return None
    elif isinstance(data, str):
        # Handle string representations of null
        if _is_null_value(data):
            return None
        # Try to parse as JSON and return as-is if valid
        try:
            json.loads(data)  # Validate it's JSON
            return data
        except (ValueError, TypeError, json.JSONDecodeError):
            # Try ast.literal_eval as fallback
            try:
                import ast

                evaluated = ast.literal_eval(data)
                if isinstance(evaluated, dict):
                    return json.dumps(evaluated)
            except (ValueError, SyntaxError):
                pass
        return None
    else:
        return None  # Cannot convert, return None
