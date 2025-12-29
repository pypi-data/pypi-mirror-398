"""
Runtime Validator - Contract-based validation utilities.

PRIMARY INTERFACE: Validator Class
===================================

The Validator class is the recommended and primary way to perform validation
in pycharter. It can be instantiated with contract artifacts from various sources:

    >>> from pycharter.runtime_validator import Validator
    >>> 
    >>> # From contract directory
    >>> validator = Validator(contract_dir="data/contracts/user")
    >>> result = validator.validate({"name": "Alice", "age": 30})
    >>> 
    >>> # From metadata store
    >>> from pycharter.metadata_store import SQLiteMetadataStore
    >>> store = SQLiteMetadataStore("metadata.db")
    >>> validator = Validator(store=store, schema_id="user_schema")
    >>> result = validator.validate({"name": "Alice", "age": 30})
    >>> 
    >>> # From contract file
    >>> validator = Validator(contract_file="contracts/user.yaml")
    >>> result = validator.validate({"name": "Alice", "age": 30})

Core Components:
- validator: Validator class (PRIMARY INTERFACE - use this for all validation)
- validator_core: Core validation utilities (ValidationResult, validate, validate_batch)
- wrappers: Convenience wrapper functions (backward compatibility)
- decorators: Validation decorators for functions
"""

from pycharter.runtime_validator.decorators import (
    validate_input,
    validate_output,
    validate_with_contract as validate_with_contract_decorator,
)
from pycharter.runtime_validator.validator_core import (
    ValidationResult,
    validate,
    validate_batch,
)
from pycharter.runtime_validator.wrappers import (
    get_model_from_contract,
    get_model_from_store,
    validate_batch_with_contract,
    validate_batch_with_store,
    validate_with_contract,
    validate_with_store,
)
from pycharter.runtime_validator.validator import (
    Validator,
    create_validator,
)

__all__ = [
    # PRIMARY INTERFACE: Validator class (use this for all validation)
    "Validator",
    "create_validator",
    "ValidationResult",
    # Low-level validation functions (for direct model validation)
    "validate",
    "validate_batch",
    # Convenience functions (backward compatibility - prefer Validator class)
    "validate_with_store",
    "validate_batch_with_store",
    "get_model_from_store",
    "validate_with_contract",
    "validate_batch_with_contract",
    "get_model_from_contract",
    # Decorators
    "validate_input",
    "validate_output",
    "validate_with_contract_decorator",
]
