"""
Route handlers for schema generation and conversion.
"""

from fastapi import APIRouter, HTTPException, status

from pycharter import from_dict, to_dict
from api.models.schemas import (
    SchemaConvertRequest,
    SchemaConvertResponse,
    SchemaGenerateRequest,
    SchemaGenerateResponse,
)

router = APIRouter()


@router.post(
    "/schemas/generate",
    response_model=SchemaGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Pydantic model from JSON Schema",
    description="Generate a Pydantic model class from a JSON Schema definition",
    response_description="Generated model information",
)
async def generate_schema(
    request: SchemaGenerateRequest,
) -> SchemaGenerateResponse:
    """
    Generate a Pydantic model from JSON Schema.
    
    This endpoint takes a JSON Schema definition and generates a Pydantic model
    class that can be used for data validation. The generated model's JSON schema
    representation is also returned.
    
    Args:
        request: Schema generation request containing schema and model_name
        
    Returns:
        Generated model information including model name and JSON schema
        
    Raises:
        HTTPException: If model generation fails
    """
    Model = from_dict(request.schema, request.model_name)
    schema_json = Model.model_json_schema()
    
    return SchemaGenerateResponse(
        model_name=request.model_name,
        schema_json=schema_json,
        message=f"Model '{request.model_name}' generated successfully",
    )


@router.post(
    "/schemas/convert",
    response_model=SchemaConvertResponse,
    status_code=status.HTTP_200_OK,
    summary="Convert Pydantic model to JSON Schema",
    description="Convert a Pydantic model class to JSON Schema definition",
    response_description="JSON Schema definition",
)
async def convert_schema(
    request: SchemaConvertRequest,
) -> SchemaConvertResponse:
    """
    Convert a Pydantic model to JSON Schema.
    
    This endpoint takes a Pydantic model class (specified by its import path)
    and converts it to a JSON Schema definition.
    
    **Note**: This endpoint requires the model class to be importable at runtime.
    In a production environment, you might want to accept the model definition
    as JSON and reconstruct it, or use a different approach.
    
    Args:
        request: Schema conversion request containing model_class path
        
    Returns:
        JSON Schema definition
        
    Raises:
        HTTPException: If schema conversion fails or model cannot be imported
    """
    parts = request.model_class.rsplit(".", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_class must be in format 'module.path.ModelClass'",
        )
    
    module_path, class_name = parts
    try:
        module = __import__(module_path, fromlist=[class_name])
        model_class = getattr(module, class_name)
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to import model class: {str(e)}",
        )
    
    schema = to_dict(model_class)
    return SchemaConvertResponse(
        schema=schema,
        title=schema.get("title"),
        version=schema.get("version"),
    )
