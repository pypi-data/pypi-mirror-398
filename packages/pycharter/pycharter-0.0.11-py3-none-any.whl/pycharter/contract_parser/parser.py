"""
Contract Parser - Decomposes data contract files into metadata components.

A data contract file contains:
- Schema definitions (JSON Schema)
- Governance rules
- Ownership information
- Other metadata

All contracts are validated against Pydantic models to ensure they adhere to
the database table design.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError as PydanticValidationError

from pycharter.db.schemas.data_contract import DataContractSchema


class ContractMetadata:
    """
    Container for decomposed contract metadata.

    Attributes:
        schema: JSON Schema definition
        coercion_rules: Coercion rules (optional)
        validation_rules: Validation rules (optional)
        metadata: Metadata containing ownership and governance_rules (optional)
        versions: Dictionary tracking versions of all components

    Note: ownership and governance_rules are extracted from metadata, not top-level fields.
    """

    def __init__(
        self,
        schema: Dict[str, Any],
        coercion_rules: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        versions: Optional[Dict[str, str]] = None,
    ):
        self.schema = schema
        self.coercion_rules = coercion_rules or {}
        self.validation_rules = validation_rules or {}
        self.metadata = metadata or {}
        self.versions = versions or {}

    @property
    def ownership(self) -> Optional[Dict[str, Any]]:
        """Extract ownership from metadata."""
        if self.metadata and isinstance(self.metadata, dict):
            return self.metadata.get("ownership")
        return None

    @property
    def governance_rules(self) -> Optional[Dict[str, Any]]:
        """Extract governance_rules from metadata."""
        if self.metadata and isinstance(self.metadata, dict):
            return self.metadata.get("governance_rules")
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        result = {
            "schema": self.schema,
        }
        if self.coercion_rules:
            result["coercion_rules"] = self.coercion_rules
        if self.validation_rules:
            result["validation_rules"] = self.validation_rules
        if self.metadata:
            result["metadata"] = self.metadata
        # Add versions if any are present
        if self.versions:
            result["versions"] = self.versions
        return result


def _validate_contract_structure(contract_data: Dict[str, Any]) -> None:
    """
    Validate that the contract data adheres to the data contract Pydantic model.

    Uses Pydantic models to ensure contracts strictly adhere to the database table design.

    Args:
        contract_data: Contract data dictionary to validate

    Raises:
        ValueError: If contract does not conform to the schema
    """
    try:
        # Validate using Pydantic model
        DataContractSchema.model_validate(contract_data)
    except PydanticValidationError as e:
        # Format Pydantic validation errors for better readability
        error_messages = []
        for error in e.errors():
            error_path = " -> ".join(str(loc) for loc in error.get("loc", []))
            error_msg = error.get("msg", "Unknown error")
            error_type = error.get("type", "validation_error")

            # Add input value if available (truncate if too long)
            input_value = error.get("input")
            if input_value is not None:
                # Convert to string and truncate if very long
                input_str = str(input_value)
                if len(input_str) > 200:
                    input_str = input_str[:200] + "..."
                error_messages.append(
                    f"  {error_path}: {error_msg} (type: {error_type}, input: {input_str})"
                )
            else:
                error_messages.append(
                    f"  {error_path}: {error_msg} (type: {error_type})"
                )

        raise ValueError(
            f"Contract validation failed. The contract does not conform to the required schema.\n"
            f"The contract must strictly adhere to the database table design.\n"
            f"Errors:\n" + "\n".join(error_messages)
        ) from e
    except Exception as e:
        # If validation itself fails, raise as ValueError
        raise ValueError(f"Contract validation error: {e}") from e


def parse_contract(
    contract_data: Dict[str, Any], validate: bool = True
) -> ContractMetadata:
    """
    Parse a contract dictionary and decompose into metadata components.

    Expected contract structure:
    {
        "schema": {...},              # JSON Schema definition (required, may contain "version")
        "coercion_rules": {...},      # Optional coercion rules (may contain "version")
        "validation_rules": {...},   # Optional validation rules (may contain "version")
        "metadata": {                 # Optional metadata (may contain "version")
            "ownership": {...},       # Ownership info nested in metadata
            "governance_rules": {...} # Governance rules nested in metadata
        },
        "versions": {...}             # Optional explicit version tracking
    }

    The contract is validated against Pydantic models to ensure it adheres to the
    database table design. This ensures data integrity when storing contracts.

    Note: ownership and governance_rules should be inside metadata, not at top level.
    For backward compatibility, if they are found at top level, they will be moved into metadata.

    Args:
        contract_data: Contract data as dictionary
        validate: If True (default), validate contract against schema before parsing

    Returns:
        ContractMetadata object with decomposed components and version tracking

    Raises:
        ValueError: If contract does not conform to the required schema (when validate=True)

    Example:
        >>> contract = {
        ...     "schema": {"type": "object", "version": "1.0.0", "properties": {"name": {"type": "string"}}},
        ...     "metadata": {
        ...         "version": "1.0.0",
        ...         "ownership": {"owner": "team-data", "team": "data-engineering"},
        ...         "governance_rules": {"data_retention": {"days": 365}}
        ...     }
        ... }
        >>> metadata = parse_contract(contract)
        >>> metadata.schema
        {'type': 'object', 'version': '1.0.0', 'properties': {'name': {'type': 'string'}}}
        >>> metadata.versions
        {'schema': '1.0.0', 'metadata': '1.0.0'}
        >>> metadata.ownership
        {'owner': 'team-data', 'team': 'data-engineering'}
    """
    # Validate contract structure against schema
    if validate:
        _validate_contract_structure(contract_data)

    schema = contract_data.get("schema", {})
    coercion_rules = contract_data.get("coercion_rules", {})
    validation_rules = contract_data.get("validation_rules", {})
    metadata = contract_data.get("metadata", {})

    # If schema is not at top level, check if entire contract is a schema
    if not schema and ("type" in contract_data or "properties" in contract_data):
        schema = contract_data
        # Extract other components if they exist as separate keys
        coercion_rules = contract_data.get("coercion_rules", {})
        validation_rules = contract_data.get("validation_rules", {})
        metadata = {
            k: v
            for k, v in contract_data.items()
            if k not in ["schema", "coercion_rules", "validation_rules", "versions"]
        }

    # For backward compatibility: if ownership/governance_rules are at top level, move them into metadata
    if not isinstance(metadata, dict):
        metadata = {}

    # Move ownership from top level to metadata if present
    if "ownership" in contract_data and "ownership" not in metadata:
        metadata["ownership"] = contract_data.get("ownership")

    # Move governance_rules from top level to metadata if present
    if "governance_rules" in contract_data and "governance_rules" not in metadata:
        metadata["governance_rules"] = contract_data.get("governance_rules")

    # Extract versions from all components
    versions: Dict[str, str] = {}

    # Check if explicit versions dict is provided
    if "versions" in contract_data and isinstance(contract_data["versions"], dict):
        versions.update(contract_data["versions"])

    # Extract version from schema
    if isinstance(schema, dict) and "version" in schema:
        versions["schema"] = schema["version"]

    # Extract version from metadata
    if isinstance(metadata, dict) and "version" in metadata:
        versions["metadata"] = metadata["version"]

    # Extract version from coercion_rules
    if isinstance(coercion_rules, dict) and "version" in coercion_rules:
        versions["coercion_rules"] = coercion_rules["version"]

    # Extract version from validation_rules
    if isinstance(validation_rules, dict) and "version" in validation_rules:
        versions["validation_rules"] = validation_rules["version"]

    return ContractMetadata(
        schema=schema,
        coercion_rules=coercion_rules,
        validation_rules=validation_rules,
        metadata=metadata,
        versions=versions,
    )


def parse_contract_file(file_path: str, validate: bool = True) -> ContractMetadata:
    """
    Load and parse a contract file (YAML or JSON).

    The contract is validated against Pydantic models to ensure it adheres to the
    database table design before parsing.

    Args:
        file_path: Path to contract file
        validate: If True (default), validate contract against schema before parsing

    Returns:
        ContractMetadata object with decomposed components

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported, invalid, or doesn't conform to schema

    Example:
        >>> metadata = parse_contract_file("contract.yaml")
        >>> print(metadata.schema)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {file_path}")

    # Determine file format
    suffix = path.suffix.lower()

    if suffix in [".yaml", ".yml"]:
        with open(path, "r", encoding="utf-8") as f:
            contract_data = yaml.safe_load(f)
    elif suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            contract_data = json.load(f)
    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. Supported formats: .json, .yaml, .yml"
        )

    if not isinstance(contract_data, dict):
        raise ValueError(
            f"Contract file must contain a dictionary/object, got {type(contract_data)}"
        )

    # Resolve variable substitutions in contract data
    from pycharter.utils.value_injector import resolve_values
    contract_data = resolve_values(contract_data, source_file=file_path)

    return parse_contract(contract_data, validate=validate)
