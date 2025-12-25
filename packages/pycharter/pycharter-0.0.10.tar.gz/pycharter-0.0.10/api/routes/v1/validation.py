"""
Route handlers for runtime validation.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from pycharter import (
    validate_batch_with_contract,
    validate_batch_with_store,
    validate_with_contract,
    validate_with_store,
)
from api.dependencies.store import get_metadata_store
from api.models.validation import (
    ValidationBatchRequest,
    ValidationBatchResponse,
    ValidationErrorDetail,
    ValidationRequest,
    ValidationResponse,
)
from pycharter.metadata_store import MetadataStoreClient

router = APIRouter()


@router.post(
    "/validation/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate data",
    description="Validate data against a schema from the metadata store or a contract dictionary",
    response_description="Validation result",
)
async def validate_data(
    request: ValidationRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ValidationResponse:
    """
    Validate data against a schema.
    
    This endpoint supports two validation modes:
    1. **Store-based**: Use `schema_id` to retrieve schema from metadata store
    2. **Contract-based**: Use `contract` dictionary directly
    
    The validation applies coercion rules (if available) and validation rules
    (if available) in addition to JSON Schema validation.
    
    Args:
        request: Validation request containing data and either schema_id or contract
        store: Metadata store dependency
        
    Returns:
        Validation result with validated data or errors
        
    Raises:
        HTTPException: If validation fails or required parameters are missing
    """
    if request.schema_id:
        result = validate_with_store(
            store=store,
            schema_id=request.schema_id,
            data=request.data,
            version=request.version,
            strict=request.strict,
        )
    elif request.contract:
        result = validate_with_contract(
            contract=request.contract,
            data=request.data,
            strict=request.strict,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either schema_id or contract must be provided",
        )
    
    errors = [
        ValidationErrorDetail(
            field=error.get("field", "unknown"),
            message=error.get("message", "Validation error"),
            input_value=error.get("input_value"),
        )
        for error in (result.errors or []) if not result.is_valid
    ]
    
    return ValidationResponse(
        is_valid=result.is_valid,
        data=result.data.model_dump() if result.data else None,
        errors=errors,
        error_count=len(errors),
    )


@router.post(
    "/validation/validate-batch",
    response_model=ValidationBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate batch of data",
    description="Validate a batch of data records against a schema from the metadata store or a contract dictionary",
    response_description="Batch validation results",
)
async def validate_batch_data(
    request: ValidationBatchRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ValidationBatchResponse:
    """
    Validate a batch of data records.
    
    This endpoint validates multiple data records in a single request. It supports
    the same two validation modes as the single validation endpoint:
    1. **Store-based**: Use `schema_id` to retrieve schema from metadata store
    2. **Contract-based**: Use `contract` dictionary directly
    
    Args:
        request: Batch validation request containing data_list and either schema_id or contract
        store: Metadata store dependency
        
    Returns:
        Batch validation results with counts and individual results
        
    Raises:
        HTTPException: If batch validation fails or required parameters are missing
    """
    if request.schema_id:
        results = validate_batch_with_store(
            store=store,
            schema_id=request.schema_id,
            data_list=request.data_list,
            version=request.version,
            strict=request.strict,
        )
    elif request.contract:
        results = validate_batch_with_contract(
            contract=request.contract,
            data_list=request.data_list,
            strict=request.strict,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either schema_id or contract must be provided",
        )
    
    response_results = []
    valid_count = 0
    invalid_count = 0
    
    for result in results:
        errors = [
            ValidationErrorDetail(
                field=error.get("field", "unknown"),
                message=error.get("message", "Validation error"),
                input_value=error.get("input_value"),
            )
            for error in (result.errors or []) if not result.is_valid
        ]
        
        if result.is_valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        response_results.append(
            ValidationResponse(
                is_valid=result.is_valid,
                data=result.data.model_dump() if result.data else None,
                errors=errors,
                error_count=len(errors),
            )
        )
    
    return ValidationBatchResponse(
        results=response_results,
        total_count=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count,
    )
