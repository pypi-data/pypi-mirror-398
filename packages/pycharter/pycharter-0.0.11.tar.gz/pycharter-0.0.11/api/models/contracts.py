"""
Request/Response models for contract endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContractParseRequest(BaseModel):
    """Request model for parsing a contract."""
    
    contract: Dict[str, Any] = Field(..., description="Contract data as dictionary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"}
                        }
                    },
                    "metadata": {
                        "title": "User Contract",
                        "version": "1.0.0"
                    }
                }
            }
        }


class ContractParseResponse(BaseModel):
    """Response model for parsed contract."""
    
    schema: Dict[str, Any] = Field(..., description="JSON Schema definition")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata information")
    ownership: Optional[Dict[str, Any]] = Field(None, description="Ownership information")
    governance_rules: Optional[Dict[str, Any]] = Field(None, description="Governance rules")
    coercion_rules: Optional[Dict[str, Any]] = Field(None, description="Coercion rules")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    versions: Optional[Dict[str, str]] = Field(None, description="Component versions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    }
                },
                "metadata": {
                    "title": "User Contract",
                    "version": "1.0.0"
                },
                "versions": {
                    "schema": "1.0.0",
                    "metadata": "1.0.0"
                }
            }
        }


class ContractBuildRequest(BaseModel):
    """Request model for building a contract from store."""
    
    schema_id: str = Field(..., description="Schema identifier")
    version: Optional[str] = Field(None, description="Schema version (default: latest)")
    include_metadata: bool = Field(True, description="Include metadata in contract")
    include_ownership: bool = Field(True, description="Include ownership in contract")
    include_governance: bool = Field(True, description="Include governance rules in contract")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "user_schema",
                "version": "1.0.0",
                "include_metadata": True,
                "include_ownership": True,
                "include_governance": True
            }
        }


class ContractBuildResponse(BaseModel):
    """Response model for built contract."""
    
    contract: Dict[str, Any] = Field(..., description="Complete contract dictionary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract": {
                    "schema": {...},
                    "metadata": {...},
                    "ownership": {...},
                    "governance_rules": {...}
                }
            }
        }
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        """Custom JSON schema generation to handle Dict[str, Any] with potential sets."""
        # Return a simple object schema for Dict[str, Any] to avoid set hashing issues
        return {
            "type": "object",
            "additionalProperties": True,
            "description": field_schema.get("description", "Complete contract dictionary"),
        }


class ContractListItem(BaseModel):
    """Model for a single contract in the list."""
    
    id: str = Field(..., description="Contract ID (UUID)")
    name: str = Field(..., description="Contract name")
    version: str = Field(..., description="Contract version")
    status: Optional[str] = Field(None, description="Contract status")
    description: Optional[str] = Field(None, description="Contract description")
    schema_id: Optional[str] = Field(None, description="Schema ID (UUID) associated with this contract")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "user_contract",
                "version": "1.0.0",
                "status": "active",
                "description": "User data contract",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ContractListResponse(BaseModel):
    """Response model for contract list."""
    
    contracts: List[ContractListItem] = Field(..., description="List of contracts")
    total: int = Field(..., description="Total number of contracts")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contracts": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "user_contract",
                        "version": "1.0.0",
                        "status": "active",
                        "description": "User data contract"
                    }
                ],
                "total": 1
            }
        }

