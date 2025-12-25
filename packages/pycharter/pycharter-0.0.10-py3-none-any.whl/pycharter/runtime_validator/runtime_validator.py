"""
Runtime validator with support for retrieving schemas, metadata, and rules from store.

This module provides high-level functions for runtime validation that retrieve
all necessary components (schema, metadata, coercion rules, validation rules)
from the metadata store and perform validation.

It also supports direct validation against data contracts without database queries.
"""

import copy
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel

from pycharter.contract_parser import (
    ContractMetadata,
    parse_contract,
    parse_contract_file,
)
from pycharter.metadata_store import MetadataStoreClient
from pycharter.pydantic_generator import from_dict
from pycharter.runtime_validator.validator import (
    ValidationResult,
    validate,
    validate_batch,
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

    This function:
    1. Retrieves schema from metadata store
    2. Retrieves coercion rules and merges them into schema
    3. Retrieves validation rules and merges them into schema
    4. Generates Pydantic model from complete schema
    5. Validates data against the model

    Args:
        store: MetadataStoreClient instance
        schema_id: Schema identifier
        data: Data dictionary to validate
        version: Optional version string (if None, uses latest)
        strict: If True, raise exceptions on validation errors

    Returns:
        ValidationResult object

    Example:
        >>> store = MyMetadataStore(...)
        >>> store.connect()
        >>> result = validate_with_store(store, "user_schema_v1", {"name": "Alice"})
        >>> if result.is_valid:
        ...     print(f"Valid: {result.data.name}")
    """
    # Get complete schema (with coercion and validation rules merged)
    complete_schema = store.get_complete_schema(schema_id, version)

    if not complete_schema:
        raise ValueError(f"Schema not found: {schema_id}")

    # Generate model from complete schema
    model_name = complete_schema.get("title", "DynamicModel")
    Model = from_dict(complete_schema, model_name)

    # Validate data
    return validate(Model, data, strict=strict)


def validate_batch_with_store(
    store: MetadataStoreClient,
    schema_id: str,
    data_list: List[Dict[str, Any]],
    version: Optional[str] = None,
    strict: bool = False,
) -> List[ValidationResult]:
    """
    Validate a batch of data using schema and rules from store.

    Args:
        store: MetadataStoreClient instance
        schema_id: Schema identifier
        data_list: List of data dictionaries to validate
        version: Optional version string (if None, uses latest)
        strict: If True, stop on first validation error

    Returns:
        List of ValidationResult objects

    Example:
        >>> store = MyMetadataStore(...)
        >>> store.connect()
        >>> results = validate_batch_with_store(
        ...     store, "user_schema_v1", [{"name": "Alice"}, {"name": "Bob"}]
        ... )
        >>> valid_count = sum(1 for r in results if r.is_valid)
    """
    # Get complete schema once
    complete_schema = store.get_complete_schema(schema_id, version)

    if not complete_schema:
        raise ValueError(f"Schema not found: {schema_id}")

    # Generate model once
    model_name = complete_schema.get("title", "DynamicModel")
    Model = from_dict(complete_schema, model_name)

    # Validate batch
    return validate_batch(Model, data_list, strict=strict)


def get_model_from_store(
    store: MetadataStoreClient,
    schema_id: str,
    model_name: Optional[str] = None,
    version: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Get a Pydantic model from store with all rules applied.

    This is useful when you need the model for multiple validations
    and want to avoid retrieving the schema multiple times.

    Args:
        store: MetadataStoreClient instance
        schema_id: Schema identifier
        model_name: Optional model name (defaults to schema title)
        version: Optional version string (if None, uses latest)

    Returns:
        Pydantic model class

    Example:
        >>> store = MyMetadataStore(...)
        >>> store.connect()
        >>> UserModel = get_model_from_store(store, "user_schema_v1", "User")
        >>> # Use model multiple times
        >>> result1 = validate(UserModel, data1)
        >>> result2 = validate(UserModel, data2)
    """
    complete_schema = store.get_complete_schema(schema_id, version)

    if not complete_schema:
        raise ValueError(f"Schema not found: {schema_id}")

    model_name = model_name or complete_schema.get("title", "DynamicModel")
    return from_dict(complete_schema, model_name)


def _merge_rules_into_schema(
    schema: Dict[str, Any],
    coercion_rules: Optional[Dict[str, Any]] = None,
    validation_rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Merge coercion and validation rules into a schema dictionary.

    This is a helper function that replicates the logic from MetadataStoreClient
    for merging rules into schemas when working with contracts directly.

    Args:
        schema: Schema dictionary (will be deep copied)
        coercion_rules: Optional coercion rules dictionary
        validation_rules: Optional validation rules dictionary

    Returns:
        Complete schema with rules merged
    """
    # Deep copy to avoid modifying original
    complete_schema = copy.deepcopy(schema)

    if not coercion_rules and not validation_rules:
        return complete_schema

    if "properties" not in complete_schema:
        return complete_schema

    # Merge coercion rules
    if coercion_rules:
        for field_name, coercion_name in coercion_rules.items():
            if field_name in complete_schema["properties"]:
                complete_schema["properties"][field_name]["coercion"] = coercion_name

    # Merge validation rules
    if validation_rules:
        for field_path, field_validations in validation_rules.items():
            # Handle nested fields with dot notation (e.g., "author.name")
            if "." in field_path:
                parts = field_path.split(".")
                if len(parts) == 2:
                    parent_field, child_field = parts
                    if parent_field in complete_schema["properties"]:
                        parent_prop = complete_schema["properties"][parent_field]
                        if (
                            "properties" in parent_prop
                            and child_field in parent_prop["properties"]
                        ):
                            if (
                                "validations"
                                not in parent_prop["properties"][child_field]
                            ):
                                parent_prop["properties"][child_field][
                                    "validations"
                                ] = {}
                            parent_prop["properties"][child_field][
                                "validations"
                            ].update(field_validations)
            else:
                # Handle top-level fields
                if field_path in complete_schema["properties"]:
                    if "validations" not in complete_schema["properties"][field_path]:
                        complete_schema["properties"][field_path]["validations"] = {}
                    complete_schema["properties"][field_path]["validations"].update(
                        field_validations
                    )

    return complete_schema


def get_model_from_contract(
    contract: Union[Dict[str, Any], ContractMetadata, str],
    model_name: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Generate a Pydantic model from a data contract without database queries.

    The contract can be:
    - A dictionary (parsed contract structure)
    - A ContractMetadata object (from parse_contract or parse_contract_file)
    - A file path string (YAML or JSON file)

    Args:
        contract: Contract data (dict, ContractMetadata, or file path)
        model_name: Optional model name (defaults to schema title)

    Returns:
        Pydantic model class with all rules applied

    Example:
        >>> # From dictionary
        >>> contract = {
        ...     "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
        ...     "coercion_rules": {"rules": {"name": "coerce_to_string"}},
        ...     "validation_rules": {"rules": {"name": {"min_length": {"threshold": 3}}}}
        ... }
        >>> UserModel = get_model_from_contract(contract, "User")
        >>>
        >>> # From file
        >>> UserModel = get_model_from_contract("data/examples/book/book_contract.yaml", "Book")
        >>>
        >>> # From ContractMetadata
        >>> from pycharter import parse_contract_file
        >>> contract_meta = parse_contract_file("book_contract.yaml")
        >>> UserModel = get_model_from_contract(contract_meta)
    """
    # Parse contract if needed
    if isinstance(contract, str):
        # File path - parse it
        contract_meta = parse_contract_file(contract)
    elif isinstance(contract, ContractMetadata):
        # Already parsed
        contract_meta = contract
    elif isinstance(contract, dict):
        # Dictionary - parse it
        contract_meta = parse_contract(contract)
    else:
        raise TypeError(
            f"Contract must be dict, ContractMetadata, or file path string, got {type(contract)}"
        )

    # Get schema
    schema = contract_meta.schema
    if not schema:
        raise ValueError("Contract must contain a schema")

    # Extract coercion and validation rules from contract
    # Rules might be:
    # 1. Already merged into schema properties (from parsed YAML/JSON)
    # 2. Separate top-level keys in contract dict (coercion_rules, validation_rules)
    # 3. Not present at all

    coercion_rules = None
    validation_rules = None

    # Only extract if contract is a dict (not already parsed)
    if isinstance(contract, dict):
        # Check for coercion_rules in contract dict
        coercion_data = contract.get("coercion_rules", {})
        if isinstance(coercion_data, dict) and coercion_data:
            # Could be {"version": "...", "rules": {...}} or just {"field": "coercion"}
            if "rules" in coercion_data:
                coercion_rules = coercion_data["rules"]
            elif not any(k in coercion_data for k in ["version", "description"]):
                # Looks like direct rules dict
                coercion_rules = coercion_data

        # Check for validation_rules in contract dict
        validation_data = contract.get("validation_rules", {})
        if isinstance(validation_data, dict) and validation_data:
            if "rules" in validation_data:
                validation_rules = validation_data["rules"]
            elif not any(k in validation_data for k in ["version", "description"]):
                # Looks like direct rules dict
                validation_rules = validation_data

    # Merge rules into schema (only if we found separate rules)
    # If rules are already in schema properties, they'll remain there
    complete_schema = _merge_rules_into_schema(schema, coercion_rules, validation_rules)

    # Generate model
    model_name = model_name or complete_schema.get("title", "DynamicModel")
    return from_dict(complete_schema, model_name)


def validate_with_contract(
    contract: Union[Dict[str, Any], ContractMetadata, str],
    data: Dict[str, Any],
    model_name: Optional[str] = None,
    strict: bool = False,
) -> ValidationResult:
    """
    Validate data against a data contract without database queries.

    This function:
    1. Parses the contract (if needed)
    2. Merges coercion and validation rules into the schema
    3. Generates a Pydantic model
    4. Validates the data

    The contract can be:
    - A dictionary (parsed contract structure)
    - A ContractMetadata object (from parse_contract or parse_contract_file)
    - A file path string (YAML or JSON file)

    Args:
        contract: Contract data (dict, ContractMetadata, or file path)
        data: Data dictionary to validate
        model_name: Optional model name (defaults to schema title)
        strict: If True, raise exceptions on validation errors

    Returns:
        ValidationResult object

    Example:
        >>> # From dictionary
        >>> contract = {
        ...     "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
        ...     "coercion_rules": {"rules": {"name": "coerce_to_string"}}
        ... }
        >>> result = validate_with_contract(contract, {"name": "Alice"})
        >>> result.is_valid
        True
        >>>
        >>> # From file
        >>> result = validate_with_contract("book_contract.yaml", {"isbn": "1234567890"})
        >>>
        >>> # For multiple validations, use get_model_from_contract() once
        >>> UserModel = get_model_from_contract(contract)
        >>> result1 = validate(UserModel, data1)
        >>> result2 = validate(UserModel, data2)
    """
    Model = get_model_from_contract(contract, model_name)
    return validate(Model, data, strict=strict)


def validate_batch_with_contract(
    contract: Union[Dict[str, Any], ContractMetadata, str],
    data_list: List[Dict[str, Any]],
    model_name: Optional[str] = None,
    strict: bool = False,
) -> List[ValidationResult]:
    """
    Validate a batch of data against a data contract without database queries.

    This function generates the model once and validates all data items,
    making it efficient for batch processing.

    Args:
        contract: Contract data (dict, ContractMetadata, or file path)
        data_list: List of data dictionaries to validate
        model_name: Optional model name (defaults to schema title)
        strict: If True, stop on first validation error

    Returns:
        List of ValidationResult objects

    Example:
        >>> contract = parse_contract_file("book_contract.yaml")
        >>> results = validate_batch_with_contract(
        ...     contract,
        ...     [{"isbn": "123"}, {"isbn": "456"}]
        ... )
        >>> valid_count = sum(1 for r in results if r.is_valid)
    """
    Model = get_model_from_contract(contract, model_name)
    return validate_batch(Model, data_list, strict=strict)
