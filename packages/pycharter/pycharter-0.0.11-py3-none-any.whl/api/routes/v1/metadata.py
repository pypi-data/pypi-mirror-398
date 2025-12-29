"""
Route handlers for metadata store operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.dependencies.database import get_db_session
from api.dependencies.store import get_metadata_store
from api.models.metadata import (
    CoercionRulesStoreRequest,
    MetadataGetRequest,
    MetadataGetResponse,
    MetadataStoreRequest,
    MetadataStoreResponse,
    RulesGetResponse,
    RulesStoreResponse,
    SchemaGetRequest,
    SchemaGetResponse,
    SchemaListItem,
    SchemaListResponse,
    SchemaStoreRequest,
    SchemaStoreResponse,
    ValidationRulesStoreRequest,
)
from pycharter.db.models import DataContractModel
from pycharter.metadata_store import MetadataStoreClient
from pycharter.utils.version import compare_versions, get_latest_version

router = APIRouter()


@router.post(
    "/metadata/schemas",
    response_model=SchemaStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store a schema",
    description="Store a JSON Schema definition in the metadata store. Validates version numbers and prevents duplicate contracts.",
    response_description="Stored schema information",
)
async def store_schema(
    request: SchemaStoreRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
    db: Session = Depends(get_db_session),
) -> SchemaStoreResponse:
    """
    Store a schema in the metadata store.
    
    This endpoint stores a JSON Schema definition with a given name and version
    in the metadata store. The schema can later be retrieved by its ID and version.
    
    **Version Validation:**
    - Prevents duplicate contracts (same name + version)
    - Ensures new versions are higher than existing versions
    - Prevents overwriting existing contracts
    
    Args:
        request: Schema store request containing schema name, schema definition, and version
        store: Metadata store dependency
        db: Database session for contract validation
        
    Returns:
        Stored schema information including schema_id
        
    Raises:
        HTTPException: If schema storage fails, duplicate contract exists, or version is invalid
    """
    # Check for existing contracts with the same name
    existing_contracts = db.query(DataContractModel).filter(
        DataContractModel.name == request.schema_name
    ).all()
    
    if existing_contracts:
        # Check if exact duplicate (same name + version)
        for contract in existing_contracts:
            if contract.version == request.version:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Contract '{request.schema_name}' with version '{request.version}' already exists. "
                        f"Cannot create duplicate contracts. Use a different version number."
                    ),
                )
        
        # Get all existing versions for this contract name
        existing_versions = [c.version for c in existing_contracts]
        latest_version = get_latest_version(existing_versions)
        
        if latest_version:
            # Validate that new version is higher than the latest existing version
            version_comparison = compare_versions(request.version, latest_version)
            if version_comparison <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Version '{request.version}' must be higher than the latest existing version "
                        f"'{latest_version}' for contract '{request.schema_name}'. "
                        f"Existing versions: {', '.join(existing_versions)}"
                    ),
                )
    
    # Store the schema (this will create the data contract if it doesn't exist)
    try:
        schema_id = store.store_schema(
            schema_name=request.schema_name,
            schema=request.schema,
            version=request.version,
        )
    except ValueError as e:
        # Re-raise ValueError as HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return SchemaStoreResponse(
        schema_id=schema_id,
        schema_name=request.schema_name,
        version=request.version,
    )


@router.get(
    "/metadata/schemas/{schema_id}",
    response_model=SchemaGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a schema",
    description="Retrieve a schema from the metadata store by ID and optional version",
    response_description="Schema definition",
)
async def get_schema(
    schema_id: str,
    version: str | None = Query(None, description="Schema version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> SchemaGetResponse:
    """
    Get a schema from the metadata store.
    
    This endpoint retrieves a schema definition by its ID. If a version is specified,
    that specific version is returned; otherwise, the latest version is returned.
    
    Args:
        schema_id: Schema identifier
        version: Optional schema version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Schema definition
        
    Raises:
        HTTPException: If schema retrieval fails or schema not found
    """
    schema = store.get_schema(schema_id, version=version)
    
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: {schema_id}",
        )
    
    return SchemaGetResponse(
        schema=schema,
        version=schema.get("version") if isinstance(schema, dict) else None,
    )


@router.post(
    "/metadata/metadata",
    response_model=MetadataStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store metadata",
    description="Store metadata for a resource in the metadata store",
    response_description="Stored metadata information",
)
async def store_metadata(
    request: MetadataStoreRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> MetadataStoreResponse:
    """
    Store metadata for a schema in the metadata store.
    
    This endpoint stores metadata associated with a schema.
    The metadata can include ownership information, governance rules, and other metadata.
    
    Args:
        request: Metadata store request containing schema_id, metadata, and optional version
        store: Metadata store dependency
        
    Returns:
        Stored metadata information including metadata_id
        
    Raises:
        HTTPException: If metadata storage fails
    """
    metadata_id = store.store_metadata(
        schema_id=request.schema_id,
        metadata=request.metadata,
        version=request.version,
    )
    
    return MetadataStoreResponse(
        metadata_id=metadata_id,
        schema_id=request.schema_id,
    )


@router.get(
    "/metadata/metadata/{schema_id}",
    response_model=MetadataGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get metadata",
    description="Retrieve metadata for a schema from the metadata store",
    response_description="Metadata dictionary",
)
async def get_metadata(
    schema_id: str,
    version: str | None = Query(None, description="Metadata version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> MetadataGetResponse:
    """
    Get metadata for a schema from the metadata store.
    
    This endpoint retrieves metadata associated with a schema by its ID and optional version.
    
    Args:
        schema_id: Schema identifier
        version: Optional metadata version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Metadata dictionary
        
    Raises:
        HTTPException: If metadata retrieval fails or metadata not found
    """
    metadata = store.get_metadata(
        schema_id=schema_id,
        version=version,
    )
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metadata not found for schema: {schema_id}",
        )
    
    return MetadataGetResponse(metadata=metadata)


@router.post(
    "/metadata/coercion-rules",
    response_model=RulesStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store coercion rules",
    description="Store coercion rules for a schema in the metadata store",
    response_description="Stored rules information",
)
async def store_coercion_rules(
    request: CoercionRulesStoreRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> RulesStoreResponse:
    """
    Store coercion rules for a schema in the metadata store.
    
    This endpoint stores coercion rules that define how data should be transformed
    before validation. Coercion rules are versioned and associated with a schema.
    
    Args:
        request: Coercion rules store request containing schema_id, coercion_rules, and version
        store: Metadata store dependency
        
    Returns:
        Stored rules information including rule_id
        
    Raises:
        HTTPException: If coercion rules storage fails
    """
    rule_id = store.store_coercion_rules(
        schema_id=request.schema_id,
        coercion_rules=request.coercion_rules,
        version=request.version or "1.0.0",
    )
    
    return RulesStoreResponse(
        rule_id=rule_id,
        schema_id=request.schema_id,
        version=request.version or "1.0.0",
    )


@router.post(
    "/metadata/validation-rules",
    response_model=RulesStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store validation rules",
    description="Store validation rules for a schema in the metadata store",
    response_description="Stored rules information",
)
async def store_validation_rules(
    request: ValidationRulesStoreRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> RulesStoreResponse:
    """
    Store validation rules for a schema in the metadata store.
    
    This endpoint stores validation rules that define custom validation logic
    beyond the JSON Schema validation. Validation rules are versioned and associated with a schema.
    
    Args:
        request: Validation rules store request containing schema_id, validation_rules, and version
        store: Metadata store dependency
        
    Returns:
        Stored rules information including rule_id
        
    Raises:
        HTTPException: If validation rules storage fails
    """
    rule_id = store.store_validation_rules(
        schema_id=request.schema_id,
        validation_rules=request.validation_rules,
        version=request.version or "1.0.0",
    )
    
    return RulesStoreResponse(
        rule_id=rule_id,
        schema_id=request.schema_id,
        version=request.version or "1.0.0",
    )


@router.get(
    "/metadata/schemas",
    response_model=SchemaListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all schemas",
    description="Retrieve a list of all schemas stored in the metadata store",
    response_description="List of schemas",
)
async def list_schemas(
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> SchemaListResponse:
    """
    List all schemas in the metadata store.
    
    This endpoint retrieves a list of all schemas with their basic information
    (id, name, title, version).
    
    Args:
        store: Metadata store dependency
        
    Returns:
        List of schemas with metadata
        
    Raises:
        HTTPException: If schema listing fails
    """
    schemas = store.list_schemas()
    
    schema_items = [
        SchemaListItem(
            id=schema.get("id", ""),
            name=schema.get("name"),
            title=schema.get("title"),
            version=schema.get("version"),
        )
        for schema in schemas
    ]
    
    return SchemaListResponse(
        schemas=schema_items,
        count=len(schema_items),
    )


@router.get(
    "/metadata/coercion-rules/{schema_id}",
    response_model=RulesGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get coercion rules",
    description="Retrieve coercion rules for a schema from the metadata store",
    response_description="Coercion rules dictionary",
)
async def get_coercion_rules(
    schema_id: str,
    version: str | None = Query(None, description="Rules version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> RulesGetResponse:
    """
    Get coercion rules for a schema from the metadata store.
    
    This endpoint retrieves coercion rules associated with a schema. If a version
    is specified, that specific version is returned; otherwise, the latest version
    is returned.
    
    Args:
        schema_id: Schema identifier
        version: Optional rules version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Coercion rules dictionary
        
    Raises:
        HTTPException: If coercion rules retrieval fails or rules not found
    """
    rules = store.get_coercion_rules(schema_id, version=version)
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coercion rules not found for schema: {schema_id}",
        )
    
    return RulesGetResponse(
        rules=rules,
        schema_id=schema_id,
        version=version,
    )


@router.get(
    "/metadata/validation-rules/{schema_id}",
    response_model=RulesGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get validation rules",
    description="Retrieve validation rules for a schema from the metadata store",
    response_description="Validation rules dictionary",
)
async def get_validation_rules(
    schema_id: str,
    version: str | None = Query(None, description="Rules version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> RulesGetResponse:
    """
    Get validation rules for a schema from the metadata store.
    
    This endpoint retrieves validation rules associated with a schema. If a version
    is specified, that specific version is returned; otherwise, the latest version
    is returned.
    
    Args:
        schema_id: Schema identifier
        version: Optional rules version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Validation rules dictionary
        
    Raises:
        HTTPException: If validation rules retrieval fails or rules not found
    """
    rules = store.get_validation_rules(schema_id, version=version)
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation rules not found for schema: {schema_id}",
        )
    
    return RulesGetResponse(
        rules=rules,
        schema_id=schema_id,
        version=version,
    )


@router.get(
    "/metadata/schemas/{schema_id}/complete",
    response_model=SchemaGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete schema with rules",
    description="Retrieve a complete schema with coercion and validation rules merged from the metadata store",
    response_description="Complete schema with rules merged",
)
async def get_complete_schema(
    schema_id: str,
    version: str | None = Query(None, description="Schema version (default: latest)"),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> SchemaGetResponse:
    """
    Get complete schema with coercion and validation rules merged.
    
    This endpoint retrieves a schema and automatically merges coercion and validation
    rules into it, returning a complete schema ready for validation.
    
    Args:
        schema_id: Schema identifier
        version: Optional schema version (default: latest)
        store: Metadata store dependency
        
    Returns:
        Complete schema dictionary with rules merged
        
    Raises:
        HTTPException: If schema retrieval fails or schema not found
    """
    complete_schema = store.get_complete_schema(schema_id, version=version)
    
    if not complete_schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: {schema_id}",
        )
    
    return SchemaGetResponse(
        schema=complete_schema,
        version=complete_schema.get("version") if isinstance(complete_schema, dict) else None,
    )
