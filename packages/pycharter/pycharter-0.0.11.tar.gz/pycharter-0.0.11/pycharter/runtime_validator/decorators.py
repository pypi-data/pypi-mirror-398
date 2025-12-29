"""
Validation decorators for easy integration.

This module provides decorators that automatically validate function
arguments and return values against data contracts.
"""

import functools
from typing import Any, Callable, Dict, Optional, Type, Union

from pydantic import BaseModel

from pycharter.contract_parser import ContractMetadata
from pycharter.runtime_validator.validator_core import (
    ValidationResult,
    validate,
)
from pycharter.runtime_validator.wrappers import get_model_from_contract


def validate_input(
    contract: Union[str, Dict[str, Any], ContractMetadata, Type[BaseModel]],
    param_name: str = "data",
    strict: bool = False,
    on_error: Optional[Callable[[ValidationResult], Any]] = None,
):
    """
    Decorator to validate function input parameter against a contract.

    Args:
        contract: Contract file path, dict, ContractMetadata, or Pydantic model class
        param_name: Name of the parameter to validate (default: "data")
        strict: If True, raise exception on validation error
        on_error: Optional callback function called when validation fails

    Returns:
        Decorated function

    Example:
        >>> @validate_input("user_contract.yaml", param_name="user_data")
        ... def process_user(user_data: dict):
        ...     # user_data is already validated
        ...     return {"success": True}
        >>> 
        >>> process_user({"name": "Alice", "age": 30})  # Validated automatically
    """
    # Get model once at decoration time
    if isinstance(contract, type) and issubclass(contract, BaseModel):
        model = contract
    else:
        model = get_model_from_contract(contract)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Find the parameter to validate
            if param_name in kwargs:
                data = kwargs[param_name]
            else:
                # Try to find by position
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if param_name in param_names:
                    param_index = param_names.index(param_name)
                    if param_index < len(args):
                        data = args[param_index]
                    else:
                        # Parameter not provided, skip validation
                        return func(*args, **kwargs)
                else:
                    # Parameter not found, skip validation
                    return func(*args, **kwargs)

            # Validate the data
            result = validate(model, data, strict=strict)
            
            if not result.is_valid:
                if on_error:
                    return on_error(result)
                elif strict:
                    error_msg = "; ".join(result.errors) if result.errors else "Validation failed"
                    raise ValueError(f"Input validation failed: {error_msg}")
                else:
                    # Invalid data - set to None if in kwargs, otherwise pass through
                    if param_name in kwargs:
                        kwargs[param_name] = None
                    return func(*args, **kwargs)
            
            # Replace with validated data (Pydantic model instance)
            if param_name in kwargs:
                kwargs[param_name] = result.data
            else:
                # For positional args, reconstruct args tuple
                param_index = param_names.index(param_name)
                args_list = list(args)
                if param_index < len(args_list):
                    args_list[param_index] = result.data
                    args = tuple(args_list)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_output(
    contract: Union[str, Dict[str, Any], ContractMetadata, Type[BaseModel]],
    strict: bool = False,
    on_error: Optional[Callable[[ValidationResult], Any]] = None,
):
    """
    Decorator to validate function return value against a contract.

    Args:
        contract: Contract file path, dict, ContractMetadata, or Pydantic model class
        strict: If True, raise exception on validation error
        on_error: Optional callback function called when validation fails

    Returns:
        Decorated function

    Example:
        >>> @validate_output("user_contract.yaml")
        ... def get_user() -> dict:
        ...     return {"name": "Alice", "age": 30}  # Validated on return
        >>> 
        >>> result = get_user()  # Automatically validated
    """
    # Get model once at decoration time
    if isinstance(contract, type) and issubclass(contract, BaseModel):
        model = contract
    else:
        model = get_model_from_contract(contract)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result_value = func(*args, **kwargs)

            # Convert to dict if it's a Pydantic model
            if isinstance(result_value, BaseModel):
                data = result_value.model_dump()
            elif isinstance(result_value, dict):
                data = result_value
            else:
                # Not a dict or model, skip validation
                return result_value

            # Validate the return value
            result = validate(model, data, strict=strict)
            
            if not result.is_valid:
                if on_error:
                    return on_error(result)
                elif strict:
                    error_msg = "; ".join(result.errors) if result.errors else "Validation failed"
                    raise ValueError(f"Output validation failed: {error_msg}")
                else:
                    # Return None on validation error
                    return None

            return result.data

        return wrapper

    return decorator


def validate_with_contract(
    contract: Union[str, Dict[str, Any], ContractMetadata],
    strict: bool = False,
    on_error: Optional[Callable[[ValidationResult], Any]] = None,
):
    """
    Decorator that validates both input (first parameter) and output against a contract.

    This is a convenience decorator that combines validate_input and validate_output.

    Args:
        contract: Contract file path, dict, or ContractMetadata
        strict: If True, raise exception on validation error
        on_error: Optional callback function called when validation fails

    Returns:
        Decorated function

    Example:
        >>> @validate_with_contract("user_contract.yaml")
        ... def process_user(user_data: dict) -> dict:
        ...     # Both input and output are validated
        ...     return {"processed": True, **user_data}
    """
    input_decorator = validate_input(contract, param_name="data", strict=strict, on_error=on_error)
    output_decorator = validate_output(contract, strict=strict, on_error=on_error)

    def decorator(func: Callable) -> Callable:
        # Apply both decorators
        decorated = input_decorator(func)
        decorated = output_decorator(decorated)
        return decorated

    return decorator

