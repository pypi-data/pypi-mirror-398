"""
Request/Response models for schema generation and conversion endpoints.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SchemaGenerateRequest(BaseModel):
    """Request model for generating a Pydantic model from JSON Schema."""
    
    schema: Dict[str, Any] = Field(..., description="JSON Schema definition")
    model_name: Optional[str] = Field("DynamicModel", description="Name for the generated model")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer", "minimum": 0, "maximum": 150}
                    },
                    "required": ["name", "age"]
                },
                "model_name": "User"
            }
        }


class SchemaGenerateResponse(BaseModel):
    """Response model for generated schema."""
    
    model_name: str = Field(..., description="Name of the generated model")
    schema_json: Dict[str, Any] = Field(..., description="JSON Schema representation of the model")
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "User",
                "schema_json": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer", "minimum": 0, "maximum": 150}
                    },
                    "required": ["name", "age"]
                },
                "message": "Model generated successfully"
            }
        }


class SchemaConvertRequest(BaseModel):
    """Request model for converting a Pydantic model to JSON Schema."""
    
    model_class: str = Field(..., description="Fully qualified model class name (e.g., 'pydantic.BaseModel')")
    # Note: In practice, you might want to accept the model definition as JSON
    # For now, we'll use a simplified approach
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_class": "examples.book.book_models.Book"
            }
        }


class SchemaConvertResponse(BaseModel):
    """Response model for converted schema."""
    
    schema: Dict[str, Any] = Field(..., description="JSON Schema definition")
    title: Optional[str] = Field(None, description="Schema title")
    version: Optional[str] = Field(None, description="Schema version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "author": {"type": "string"}
                    }
                },
                "title": "Book",
                "version": "1.0.0"
            }
        }

