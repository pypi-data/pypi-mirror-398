"""
Request/Response models for metadata store endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SchemaStoreRequest(BaseModel):
    """Request model for storing a schema."""
    
    schema_name: str = Field(..., description="Schema name/identifier")
    schema: Dict[str, Any] = Field(..., description="JSON Schema definition")
    version: str = Field(..., description="Schema version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_name": "user_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    }
                },
                "version": "1.0.0"
            }
        }


class SchemaStoreResponse(BaseModel):
    """Response model for stored schema."""
    
    schema_id: str = Field(..., description="Schema identifier")
    schema_name: str = Field(..., description="Schema name")
    version: str = Field(..., description="Schema version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "schema_1",
                "schema_name": "user_schema",
                "version": "1.0.0"
            }
        }


class SchemaGetRequest(BaseModel):
    """Request model for retrieving a schema."""
    
    schema_id: str = Field(..., description="Schema identifier")
    version: Optional[str] = Field(None, description="Schema version (default: latest)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "schema_1",
                "version": "1.0.0"
            }
        }


class SchemaGetResponse(BaseModel):
    """Response model for retrieved schema."""
    
    schema: Dict[str, Any] = Field(..., description="JSON Schema definition")
    version: Optional[str] = Field(None, description="Schema version")
    
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
                "version": "1.0.0"
            }
        }


class MetadataStoreRequest(BaseModel):
    """Request model for storing metadata."""
    
    schema_id: str = Field(..., description="Schema identifier")
    metadata: Dict[str, Any] = Field(..., description="Metadata dictionary")
    version: Optional[str] = Field(None, description="Version string (default: uses schema version)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "schema_1",
                "metadata": {
                    "title": "User Schema Metadata",
                    "description": "Metadata for user schema",
                    "business_owners": ["owner@example.com"]
                },
                "version": "1.0.0"
            }
        }


class MetadataStoreResponse(BaseModel):
    """Response model for stored metadata."""
    
    metadata_id: str = Field(..., description="Metadata record identifier")
    schema_id: str = Field(..., description="Schema identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata_id": "metadata_1",
                "schema_id": "schema_1"
            }
        }


class MetadataGetRequest(BaseModel):
    """Request model for retrieving metadata."""
    
    schema_id: str = Field(..., description="Schema identifier")
    version: Optional[str] = Field(None, description="Version string (default: uses latest version)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "schema_1",
                "version": "1.0.0"
            }
        }


class MetadataGetResponse(BaseModel):
    """Response model for retrieved metadata."""
    
    metadata: Dict[str, Any] = Field(..., description="Metadata dictionary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "title": "User Schema Metadata",
                    "description": "Metadata for user schema",
                    "business_owners": ["owner@example.com"]
                }
            }
        }


class CoercionRulesStoreRequest(BaseModel):
    """Request model for storing coercion rules."""
    
    schema_id: str = Field(..., description="Schema identifier")
    coercion_rules: Dict[str, Any] = Field(..., description="Coercion rules dictionary")
    version: Optional[str] = Field(None, description="Rules version (default: 1.0.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "schema_1",
                "coercion_rules": {
                    "age": "coerce_to_integer",
                    "email": "coerce_to_lowercase"
                },
                "version": "1.0.0"
            }
        }


class ValidationRulesStoreRequest(BaseModel):
    """Request model for storing validation rules."""
    
    schema_id: str = Field(..., description="Schema identifier")
    validation_rules: Dict[str, Any] = Field(..., description="Validation rules dictionary")
    version: Optional[str] = Field(None, description="Rules version (default: 1.0.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": "schema_1",
                "validation_rules": {
                    "age": {
                        "is_positive": {},
                        "is_in_range": {"min": 0, "max": 150}
                    }
                },
                "version": "1.0.0"
            }
        }


class RulesStoreResponse(BaseModel):
    """Response model for stored rules."""
    
    rule_id: str = Field(..., description="Rule identifier")
    schema_id: str = Field(..., description="Schema identifier")
    version: str = Field(..., description="Rules version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "coercion_1",
                "schema_id": "schema_1",
                "version": "1.0.0"
            }
        }


class SchemaListItem(BaseModel):
    """Schema list item model."""
    
    id: str = Field(..., description="Schema identifier")
    name: Optional[str] = Field(None, description="Schema name")
    title: Optional[str] = Field(None, description="Schema title")
    version: Optional[str] = Field(None, description="Schema version")


class SchemaListResponse(BaseModel):
    """Response model for listing schemas."""
    
    schemas: List[SchemaListItem] = Field(..., description="List of schemas")
    count: int = Field(..., description="Total number of schemas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schemas": [
                    {
                        "id": "schema_1",
                        "name": "user_schema",
                        "title": "User Schema",
                        "version": "1.0.0"
                    }
                ],
                "count": 1
            }
        }


class RulesGetResponse(BaseModel):
    """Response model for retrieving rules."""
    
    rules: Dict[str, Any] = Field(..., description="Rules dictionary")
    schema_id: str = Field(..., description="Schema identifier")
    version: Optional[str] = Field(None, description="Rules version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rules": {
                    "age": "coerce_to_integer",
                    "email": "coerce_to_lowercase"
                },
                "schema_id": "schema_1",
                "version": "1.0.0"
            }
        }

