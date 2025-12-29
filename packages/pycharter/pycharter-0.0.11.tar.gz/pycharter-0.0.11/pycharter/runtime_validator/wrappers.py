"""
Convenience wrapper functions for backward compatibility.

These functions provide a simple function-based API that wraps the Validator class.
For new code, prefer using the Validator class directly for better performance
and more control.

PRIMARY INTERFACE: Validator Class
==================================

For most use cases, use the Validator class directly:

    >>> from pycharter.runtime_validator import Validator
    >>> validator = Validator(contract_dir="data/contracts/user")
    >>> result = validator.validate({"name": "Alice", "age": 30})

These wrapper functions are provided for backward compatibility and convenience
when you need a quick one-off validation without creating a Validator instance.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel

from pycharter.contract_parser import ContractMetadata
from pycharter.metadata_store import MetadataStoreClient
from pycharter.runtime_validator.validator_core import ValidationResult


def _create_validator_from_contract(
    contract: Union[Dict[str, Any], ContractMetadata, str],
) -> Any:  # Returns Validator, but using Any to avoid circular import
    """
    Create a Validator instance from various contract formats.
    
    This helper function centralizes the logic for creating validators
    from different contract representations, reducing code duplication.
    
    Args:
        contract: Contract data (dict, ContractMetadata, contract file path, or contract directory)
        
    Returns:
        Validator instance
        
    Raises:
        ValueError: If contract type is invalid
    """
    # Lazy import to avoid circular dependency
    from pycharter.runtime_validator.validator import Validator
    
    if isinstance(contract, str):
        path = Path(contract)
        if path.is_dir():
            return Validator(contract_dir=str(contract))
        else:
            return Validator(contract_file=str(contract))
    elif isinstance(contract, dict):
        return Validator(contract_dict=contract)
    elif isinstance(contract, ContractMetadata):
        return Validator(contract_metadata=contract)
    else:
        raise ValueError(
            f"Invalid contract type: {type(contract)}. "
            f"Expected dict, ContractMetadata, or str (file/dir path)"
        )


def validate_with_store(
    store: MetadataStoreClient,
    schema_id: str,
    data: Dict[str, Any],
    version: Optional[str] = None,
    strict: bool = False,
) -> ValidationResult:
    """
    Validate data using schema, coercion rules, and validation rules from store.
    
    This function uses the Validator class internally. For better performance
    when validating multiple records, create a Validator instance and reuse it.
    
    Args:
        store: MetadataStoreClient instance
        schema_id: Schema identifier
        data: Data dictionary to validate
        version: Optional version string (if None, uses latest)
        strict: If True, raise exceptions on validation errors
    
    Returns:
        ValidationResult object
    
    Example:
        >>> store = SQLiteMetadataStore("metadata.db")
        >>> result = validate_with_store(store, "user_schema", {"name": "Alice"})
        
        # For multiple validations, prefer Validator class:
        >>> validator = Validator(store=store, schema_id="user_schema")
        >>> result1 = validator.validate(data1)
        >>> result2 = validator.validate(data2)
    """
    # Lazy import to avoid circular dependency
    from pycharter.runtime_validator.validator import Validator
    
    validator = Validator(store=store, schema_id=schema_id, schema_version=version)
    return validator.validate(data, strict=strict)


def validate_batch_with_store(
    store: MetadataStoreClient,
    schema_id: str,
    data_list: List[Dict[str, Any]],
    version: Optional[str] = None,
    strict: bool = False,
) -> List[ValidationResult]:
    """
    Validate a batch of data using schema and rules from store.
    
    This function uses the Validator class internally. The Validator instance
    is created once and reused for all validations in the batch.
    
    Args:
        store: MetadataStoreClient instance
        schema_id: Schema identifier
        data_list: List of data dictionaries to validate
        version: Optional version string (if None, uses latest)
        strict: If True, stop on first validation error
    
    Returns:
        List of ValidationResult objects
    
    Example:
        >>> store = SQLiteMetadataStore("metadata.db")
        >>> results = validate_batch_with_store(store, "user_schema", [data1, data2])
    """
    # Lazy import to avoid circular dependency
    from pycharter.runtime_validator.validator import Validator
    
    validator = Validator(store=store, schema_id=schema_id, schema_version=version)
    return validator.validate_batch(data_list, strict=strict)


def get_model_from_store(
    store: MetadataStoreClient,
    schema_id: str,
    model_name: Optional[str] = None,
    version: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Generate a Pydantic model from a schema stored in the metadata store.
    
    This function uses the Validator class internally. For better performance
    when you need both the model and validation, create a Validator instance.
    
    Args:
        store: MetadataStoreClient instance
        schema_id: Schema identifier
        model_name: Optional model name (ignored, kept for compatibility)
        version: Optional version string (if None, uses latest)
    
    Returns:
        Pydantic model class
    
    Example:
        >>> store = SQLiteMetadataStore("metadata.db")
        >>> Model = get_model_from_store(store, "user_schema")
        
        # For validation, prefer Validator class:
        >>> validator = Validator(store=store, schema_id="user_schema")
        >>> Model = validator.get_model()
        >>> result = validator.validate(data)
    """
    # Lazy import to avoid circular dependency
    from pycharter.runtime_validator.validator import Validator
    
    validator = Validator(store=store, schema_id=schema_id, schema_version=version)
    return validator.get_model()


def get_model_from_contract(
    contract: Union[Dict[str, Any], ContractMetadata, str],
    model_name: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Generate a Pydantic model from a data contract (uses Validator internally).
    
    Args:
        contract: Contract data (dict, ContractMetadata, contract file path, or contract directory)
        model_name: Optional model name (ignored, kept for compatibility)
    
    Returns:
        Pydantic model class
    """
    validator = _create_validator_from_contract(contract)
    return validator.get_model()


def validate_with_contract(
    contract: Union[Dict[str, Any], ContractMetadata, str],
    data: Dict[str, Any],
    model_name: Optional[str] = None,
    strict: bool = False,
) -> ValidationResult:
    """
    Validate data against a data contract (uses Validator internally).
    
    Args:
        contract: Contract data (dict, ContractMetadata, contract file path, or contract directory)
        data: Data dictionary to validate
        model_name: Optional model name (ignored, kept for compatibility)
        strict: If True, raise exceptions on validation errors
    
    Returns:
        ValidationResult object
    """
    validator = _create_validator_from_contract(contract)
    return validator.validate(data, strict=strict)


def validate_batch_with_contract(
    contract: Union[Dict[str, Any], ContractMetadata, str],
    data_list: List[Dict[str, Any]],
    model_name: Optional[str] = None,
    strict: bool = False,
) -> List[ValidationResult]:
    """
    Validate a batch of data against a data contract (uses Validator internally).
    
    Args:
        contract: Contract data (dict, ContractMetadata, contract file path, or contract directory)
        data_list: List of data dictionaries to validate
        model_name: Optional model name (ignored, kept for compatibility)
        strict: If True, stop on first validation error
    
    Returns:
        List of ValidationResult objects
    """
    validator = _create_validator_from_contract(contract)
    return validator.validate_batch(data_list, strict=strict)

