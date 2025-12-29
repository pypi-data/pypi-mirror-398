"""
Pydantic models for data contract validation.

These models ensure that data contracts strictly adhere to the database table design.
Based on the database schema:
- data_contracts table
- schemas table
- metadata_records table
- owners table
- coercion_rules table
- validation_rules table
"""

import warnings
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from typing import ForwardRef

# Suppress Pydantic warnings about field name "schema" shadowing BaseModel.schema()
# This is safe because we're using the field for data validation, not accessing BaseModel.schema()
warnings.filterwarnings(
    "ignore",
    message='.*Field name "schema".*shadows an attribute.*',
    category=UserWarning,
)


class SchemaComponent(BaseModel):
    """
    Schema component - required field.

    Must be a valid JSON Schema object. Stored in schemas table.
    """

    type: str = Field(..., description="JSON Schema type (e.g., 'object')")
    properties: Optional[Dict[str, Any]] = Field(
        None, description="JSON Schema properties"
    )
    required: Optional[List[str]] = Field(None, description="Required fields")
    version: Optional[str] = Field(None, max_length=50, description="Schema version")
    title: Optional[str] = Field(None, description="Schema title")

    model_config = {
        "extra": "allow",  # Allow additional JSON Schema fields
    }


class OwnershipComponent(BaseModel):
    """
    Ownership component - optional field.

    Stored in owners table. Matches database column constraints.
    """

    owner: Optional[str] = Field(
        None, max_length=255, description="Owner identifier (matches owners.id)"
    )
    name: Optional[str] = Field(
        None, max_length=255, description="Display name (matches owners.name)"
    )
    email: Optional[str] = Field(
        None, max_length=255, description="Owner email (matches owners.email)"
    )
    team: Optional[str] = Field(
        None, max_length=255, description="Team name (matches owners.team)"
    )
    additional_info: Optional[Dict[str, Any]] = Field(
        None, description="Additional info (stored in owners.additional_info as JSON)"
    )

    model_config = {
        "extra": "allow",  # Allow additional ownership fields
    }


class GovernanceRulesComponent(BaseModel):
    """
    Governance rules component - optional field.

    Stored in metadata_records.governance_rules as JSON.
    """

    model_config = {
        "extra": "allow",  # Governance rules can contain any structure (stored as JSON)
    }


class MetadataComponent(BaseModel):
    """
    Metadata component - optional field.

    Stored in metadata_records table. Matches database column constraints.
    Contains ownership and governance_rules as nested fields.
    """

    version: Optional[str] = Field(None, max_length=50, description="Metadata version")
    title: Optional[str] = Field(
        None, max_length=255, description="Title (matches metadata_records.title)"
    )
    status: Optional[str] = Field(
        None, max_length=50, description="Status: active, deprecated, or draft"
    )
    type: Optional[str] = Field(
        None, max_length=50, description="Type (matches metadata_records.type)"
    )
    description: Optional[str] = Field(None, description="Description")
    created_by: Optional[str] = Field(
        None,
        max_length=255,
        description="Created by (matches metadata_records.created_by)",
    )
    updated_by: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated by (matches metadata_records.updated_by)",
    )

    # Ownership fields (stored in metadata_records as JSON arrays)
    business_owners: Optional[List[str]] = Field(
        None,
        description="Business owners (stored in metadata_records.business_owners as JSON)",
    )
    bu_sme: Optional[List[str]] = Field(
        None, description="BU SMEs (stored in metadata_records.bu_sme as JSON)"
    )
    it_application_owners: Optional[List[str]] = Field(
        None,
        description="IT Application Owners (stored in metadata_records.it_application_owners as JSON)",
    )
    it_sme: Optional[List[str]] = Field(
        None, description="IT SMEs (stored in metadata_records.it_sme as JSON)"
    )
    support_lead: Optional[List[str]] = Field(
        None,
        description="Support Lead (stored in metadata_records.support_lead as JSON)",
    )

    # Ownership component (stored in owners table, referenced from metadata)
    ownership: Optional[OwnershipComponent] = Field(
        None, description="Ownership information (stored in owners table)"
    )

    # Governance rules (stored in metadata_records.governance_rules as JSON)
    governance_rules: Optional[GovernanceRulesComponent] = Field(
        None,
        description="Governance rules (stored in metadata_records.governance_rules as JSON)",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status enum values."""
        if v is not None and v not in ["active", "deprecated", "draft"]:
            raise ValueError("status must be one of: active, deprecated, draft")
        return v

    model_config = {
        "extra": "allow",  # Allow additional metadata fields (stored as JSON in database)
    }


class CoercionRulesComponent(BaseModel):
    """
    Coercion rules component - optional field.

    Stored in coercion_rules table. Structure matches database design.
    """

    version: Optional[str] = Field(
        None, max_length=50, description="Coercion rules version"
    )
    rules: Optional[Dict[str, str]] = Field(
        None,
        description="Coercion rules mapping field names to coercion function names",
    )

    model_config = {
        "extra": "allow",  # Allow additional fields in coercion rules
    }


class ValidationRulesComponent(BaseModel):
    """
    Validation rules component - optional field.

    Stored in validation_rules table. Structure matches database design.
    """

    version: Optional[str] = Field(
        None, max_length=50, description="Validation rules version"
    )
    rules: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Validation rules mapping field names to validation configurations",
    )

    model_config = {
        "extra": "allow",  # Allow additional fields in validation rules
    }


class VersionsComponent(BaseModel):
    """
    Versions component - optional field.

    Tracks versions of all components. Stored in data_contracts table version columns.
    """

    schema: Optional[str] = Field(  # type: ignore[assignment]
        None,
        max_length=50,
        description="Schema version",
        alias="schema",
        serialization_alias="schema",
    )
    metadata: Optional[str] = Field(None, max_length=50, description="Metadata version")
    coercion_rules: Optional[str] = Field(
        None, max_length=50, description="Coercion rules version"
    )
    validation_rules: Optional[str] = Field(
        None, max_length=50, description="Validation rules version"
    )

    model_config = {
        "extra": "forbid",  # Versions should only contain these fields
        "populate_by_name": True,
        "validate_assignment": True,
    }


class DataContractSchema(BaseModel):
    """
    Pydantic model for validating data contract structure.

    Ensures contracts strictly adhere to the database table design.
    All fields match the database schema constraints.

    Contract structure:
    - schema: JSON Schema definition (required)
    - coercion_rules: Coercion rules (optional)
    - validation_rules: Validation rules (optional)
    - metadata: Metadata containing ownership and governance_rules (optional)
    - versions: Version tracking (optional)

    Note: ownership and governance_rules are nested inside metadata, not at top level.
    """

    schema: SchemaComponent = Field(  # type: ignore[assignment]
        ...,
        description="JSON Schema definition (required, stored in schemas table)",
        alias="schema",
        serialization_alias="schema",
    )
    coercion_rules: Optional[CoercionRulesComponent] = Field(
        None, description="Coercion rules (optional, stored in coercion_rules table)"
    )
    validation_rules: Optional[ValidationRulesComponent] = Field(
        None,
        description="Validation rules (optional, stored in validation_rules table)",
    )
    metadata: Optional[MetadataComponent] = Field(
        None,
        description="Metadata (optional, stored in metadata_records table). Contains ownership and governance_rules.",
    )
    versions: Optional[VersionsComponent] = Field(
        None, description="Version tracking (optional, stored in data_contracts table)"
    )

    model_config = {
        "extra": "forbid",  # Only allow defined fields to ensure strict adherence to database schema
        "populate_by_name": True,
        "validate_assignment": True,
    }
