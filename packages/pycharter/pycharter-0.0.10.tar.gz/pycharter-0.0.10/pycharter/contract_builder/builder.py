"""
Contract Builder - Constructs consolidated data contracts from separate artifacts.

This module provides functionality to combine separate artifacts (schema, coercion rules,
validation rules, metadata) into a single consolidated data contract that tracks all
component versions and can be used for runtime validation.
"""

import copy
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pycharter.metadata_store import MetadataStoreClient
from pycharter.metadata_store.client import (
    _merge_coercion_rules,
    _merge_validation_rules,
)


@dataclass
class ContractArtifacts:
    """
    Container for separate contract artifacts.

    Attributes:
        schema: JSON Schema definition (may contain version)
        coercion_rules: Coercion rules dictionary (may contain version)
        validation_rules: Validation rules dictionary (may contain version)
        metadata: Metadata dictionary (may contain version)
        ownership: Ownership information (optional)
        governance_rules: Governance rules (optional)
    """

    schema: Dict[str, Any]
    coercion_rules: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    ownership: Optional[Dict[str, Any]] = None
    governance_rules: Optional[Dict[str, Any]] = None


def _extract_version(artifact: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract version from an artifact dictionary."""
    if artifact and isinstance(artifact, dict) and "version" in artifact:
        return artifact["version"]
    return None


def _extract_rules(artifact: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Extract rules from an artifact.

    Handles both formats:
    - {"version": "...", "rules": {...}} -> returns rules
    - {"field": "value", ...} -> returns as-is (direct rules dict)
    """
    if not artifact or not isinstance(artifact, dict):
        return None

    # If it has "rules" key, extract that
    if "rules" in artifact:
        return artifact["rules"]

    # If it has version/description but no rules, return None
    if any(k in artifact for k in ["version", "description"]):
        # Check if it looks like a rules dict (has field mappings)
        if not any(k in artifact for k in ["version", "description"]):
            return artifact
        return None

    # Looks like direct rules dict
    return artifact


def build_contract(
    artifacts: ContractArtifacts,
    include_metadata: bool = True,
    include_ownership: bool = True,
    include_governance: bool = True,
) -> Dict[str, Any]:
    """
    Build a consolidated data contract from separate artifacts.

    This function combines schema, coercion rules, validation rules, and metadata
    into a single consolidated contract. It tracks versions of all components
    and produces a contract suitable for runtime validation.

    Args:
        artifacts: ContractArtifacts object containing all separate artifacts
        include_metadata: Whether to include metadata in the contract
        include_ownership: Whether to include ownership information
        include_governance: Whether to include governance rules

    Returns:
        Consolidated contract dictionary with:
        - schema: Complete schema with coercion/validation rules merged (must have version)
        - coercion_rules: Coercion rules (if provided)
        - validation_rules: Validation rules (if provided)
        - metadata: Metadata containing ownership and governance_rules (if include_metadata=True)
        - versions: Dictionary tracking versions of all components

        Note: ownership and governance_rules are nested inside metadata, not at top level.

    Raises:
        ValueError: If schema does not have a version field

    Example:
        >>> artifacts = ContractArtifacts(
        ...     schema={"type": "object", "version": "1.0.0", "properties": {...}},
        ...     coercion_rules={"version": "1.0.0", "rules": {"age": "coerce_to_integer"}},
        ...     validation_rules={"version": "1.0.0", "rules": {"age": {"is_positive": {...}}}},
        ...     metadata={"version": "1.0.0", "description": "User contract"},
        ...     ownership={"owner": "data-team", "team": "engineering"},
        ...     governance_rules={"data_retention": {"days": 365}}
        ... )
        >>> contract = build_contract(artifacts)
        >>> contract["versions"]
        {'schema': '1.0.0', 'coercion_rules': '1.0.0', 'validation_rules': '1.0.0', 'metadata': '1.0.0'}
        >>> contract["metadata"]["ownership"]
        {'owner': 'data-team', 'team': 'engineering'}
        >>> contract["metadata"]["governance_rules"]
        {'data_retention': {'days': 365}}
    """
    if not artifacts.schema:
        raise ValueError("Schema is required to build a contract")

    # Validate schema has version
    if "version" not in artifacts.schema:
        raise ValueError(
            "Schema must have a 'version' field. All schemas must be versioned. "
            "Please ensure the schema dictionary contains 'version': '<version_string>'."
        )

    # Deep copy schema to avoid modifying original
    complete_schema = copy.deepcopy(artifacts.schema)

    # Extract and merge coercion rules
    coercion_rules = _extract_rules(artifacts.coercion_rules)
    if coercion_rules:
        _merge_coercion_rules(complete_schema, coercion_rules)

    # Extract and merge validation rules
    validation_rules = _extract_rules(artifacts.validation_rules)
    if validation_rules:
        _merge_validation_rules(complete_schema, validation_rules)

    # Build contract
    contract: Dict[str, Any] = {
        "schema": complete_schema,
    }

    # Track versions
    versions: Dict[str, str] = {}

    # Extract version from schema
    schema_version = _extract_version(artifacts.schema)
    if schema_version:
        versions["schema"] = schema_version

    # Extract version from coercion rules
    if artifacts.coercion_rules:
        coercion_version = _extract_version(artifacts.coercion_rules)
        if coercion_version:
            versions["coercion_rules"] = coercion_version

    # Extract version from validation rules
    if artifacts.validation_rules:
        validation_version = _extract_version(artifacts.validation_rules)
        if validation_version:
            versions["validation_rules"] = validation_version

    # Extract version from metadata
    if artifacts.metadata:
        metadata_version = _extract_version(artifacts.metadata)
        if metadata_version:
            versions["metadata"] = metadata_version

    # Add metadata if requested
    if include_metadata and artifacts.metadata:
        # Create metadata dict without version (version is tracked separately)
        metadata_dict = copy.deepcopy(artifacts.metadata)
        metadata_dict.pop("version", None)  # Remove version, it's in versions dict

        # Add ownership inside metadata if requested
        if include_ownership and artifacts.ownership:
            metadata_dict["ownership"] = copy.deepcopy(artifacts.ownership)

        # Add governance rules inside metadata if requested
        if include_governance and artifacts.governance_rules:
            metadata_dict["governance_rules"] = copy.deepcopy(
                artifacts.governance_rules
            )

        contract["metadata"] = metadata_dict

    # Also expose ownership and governance_rules at top level for easier access
    if include_ownership and artifacts.ownership:
        contract["ownership"] = copy.deepcopy(artifacts.ownership)
    
    if include_governance and artifacts.governance_rules:
        contract["governance_rules"] = copy.deepcopy(artifacts.governance_rules)

    # Add versions tracking
    if versions:
        contract["versions"] = versions

    return contract


def build_contract_from_store(
    store: MetadataStoreClient,
    schema_id: str,
    version: Optional[str] = None,
    include_metadata: bool = True,
    include_ownership: bool = True,
    include_governance: bool = True,
) -> Dict[str, Any]:
    """
    Build a consolidated data contract from artifacts stored in metadata store.

    This function retrieves all separate artifacts (schema, coercion rules,
    validation rules, metadata) from the metadata store and combines them
    into a single consolidated contract.

    Args:
        store: MetadataStoreClient instance
        schema_id: Schema identifier
        version: Optional version string (if None, uses latest for each component)
        include_metadata: Whether to include metadata in the contract
        include_ownership: Whether to include ownership information
        include_governance: Whether to include governance rules

    Returns:
        Consolidated contract dictionary ready for runtime validation

    Example:
        >>> store = InMemoryMetadataStore()
        >>> store.connect()
        >>> # ... store schema, rules, metadata ...
        >>> contract = build_contract_from_store(store, "user_schema_v1")
        >>> # Use contract for validation
        >>> from pycharter import validate_with_contract
        >>> result = validate_with_contract(contract, {"name": "Alice", "age": 30})
    """
    # Retrieve schema with version (if specified)
    schema = store.get_schema(schema_id, version)
    if not schema:
        raise ValueError(f"Schema not found: {schema_id} (version: {version})")

    # Validate schema has version
    if "version" not in schema:
        raise ValueError(
            f"Schema {schema_id} does not have a version field. "
            "All schemas must be versioned."
        )

    # Retrieve coercion rules
    coercion_rules = store.get_coercion_rules(schema_id, version)

    # Retrieve validation rules
    validation_rules = store.get_validation_rules(schema_id, version)

    # Retrieve metadata
    metadata = None
    if include_metadata:
        metadata = store.get_metadata(schema_id)

    # Extract ownership and governance_rules from metadata
    ownership = None
    governance_rules = None
    if metadata:
        # Ownership fields might be at top level of metadata (from database relationships)
        # or nested in an "ownership" dict
        ownership_fields = [
            "business_owners", "bu_sme", "it_application_owners", 
            "it_sme", "support_lead"
        ]
        
        # Check if ownership is already a nested dict
        if "ownership" in metadata and isinstance(metadata.get("ownership"), dict):
            ownership = metadata.get("ownership")
        else:
            # Extract ownership fields from top-level metadata
            ownership = {}
            for field in ownership_fields:
                if field in metadata:
                    ownership[field] = metadata[field]
            
            # Only create ownership dict if we found any ownership fields
            if not ownership:
                ownership = None
            else:
                # Remove ownership fields from metadata to avoid duplication
                # Create a copy to avoid modifying the original
                metadata = metadata.copy()
                for field in ownership_fields:
                    metadata.pop(field, None)
        
        # Governance rules should be nested in metadata or at top level
        governance_rules = metadata.get("governance_rules")

    # Build contract from artifacts
    artifacts = ContractArtifacts(
        schema=schema,
        coercion_rules=coercion_rules,
        validation_rules=validation_rules,
        metadata=metadata,
        ownership=ownership,
        governance_rules=governance_rules,
    )

    return build_contract(
        artifacts,
        include_metadata=include_metadata,
        include_ownership=include_ownership,
        include_governance=include_governance,
    )
