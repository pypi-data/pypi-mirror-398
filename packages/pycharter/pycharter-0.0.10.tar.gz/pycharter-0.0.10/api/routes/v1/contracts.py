"""
Route handlers for contract parsing and building.
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from pycharter import build_contract_from_store, parse_contract
from api.dependencies.database import get_db_session
from api.dependencies.store import get_metadata_store
from api.models.contracts import (
    ContractBuildRequest,
    ContractBuildResponse,
    ContractListResponse,
    ContractListItem,
    ContractParseRequest,
    ContractParseResponse,
)
from pycharter.db.models import DataContractModel
from pycharter.metadata_store import MetadataStoreClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/contracts/parse",
    response_model=ContractParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse a data contract",
    description="Parse a data contract dictionary into its component parts (schema, metadata, ownership, governance rules, etc.)",
    response_description="Parsed contract components",
)
async def parse_contract_endpoint(
    request: ContractParseRequest,
) -> ContractParseResponse:
    """
    Parse a data contract into its components.
    
    This endpoint takes a complete data contract dictionary and breaks it down
    into its constituent parts: schema, metadata, ownership, governance rules,
    coercion rules, and validation rules.
    
    Args:
        request: Contract parse request containing contract data
        
    Returns:
        Parsed contract components
        
    Raises:
        HTTPException: If contract parsing fails
    """
    # Handle potential double-wrapping
    contract_data = request.contract
    if isinstance(contract_data, dict) and "contract" in contract_data and len(contract_data) == 1:
        contract_data = contract_data["contract"]
    
    if not isinstance(contract_data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contract format: expected dict, got {type(contract_data)}",
        )
    
    if "schema" not in contract_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract must contain a 'schema' field at the top level",
        )
    
    try:
        contract_metadata = parse_contract(contract_data)
        return ContractParseResponse(
            schema=contract_metadata.schema,
            metadata=contract_metadata.metadata,
            ownership=contract_metadata.ownership,
            governance_rules=contract_metadata.governance_rules,
            coercion_rules=contract_metadata.coercion_rules,
            validation_rules=contract_metadata.validation_rules,
            versions=contract_metadata.versions,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/contracts/build",
    response_model=ContractBuildResponse,
    status_code=status.HTTP_200_OK,
    summary="Build a contract from metadata store",
    description="Reconstruct a complete data contract from components stored in the metadata store",
    response_description="Complete contract dictionary",
)
async def build_contract_endpoint(
    request: ContractBuildRequest,
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ContractBuildResponse:
    """
    Build a contract from metadata store.
    
    This endpoint reconstructs a complete data contract dictionary from
    components stored in the metadata store. You can optionally include
    metadata, ownership, and governance rules.
    
    Args:
        request: Contract build request with schema_id and options
        store: Metadata store dependency
        
    Returns:
        Complete contract dictionary
        
    Raises:
        HTTPException: If contract building fails or schema not found
    """
    contract = build_contract_from_store(
        store=store,
        schema_id=request.schema_id,
        version=request.version,
        include_metadata=request.include_metadata,
        include_ownership=request.include_ownership,
        include_governance=request.include_governance,
    )
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: {request.schema_id}",
        )
    
    return ContractBuildResponse(contract=contract)


@router.get(
    "/contracts",
    response_model=ContractListResponse,
    status_code=status.HTTP_200_OK,
    summary="List data contracts",
    description="Get a list of all data contracts stored in the database",
    response_description="List of contracts",
)
async def list_contracts(
    db: Session = Depends(get_db_session),
) -> ContractListResponse:
    """
    List all data contracts from the database.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of contracts with metadata
        
    Raises:
        HTTPException: If database query fails
    """
    contracts = db.query(DataContractModel).order_by(
        DataContractModel.created_at.desc()
    ).all()
    
    contract_items = [
        ContractListItem(
            id=str(contract.id),
            name=contract.name,
            version=contract.version,
            status=contract.status,
            description=contract.description,
            schema_id=str(contract.schema_id) if contract.schema_id else None,
            created_at=contract.created_at.isoformat() if contract.created_at else None,
            updated_at=contract.updated_at.isoformat() if contract.updated_at else None,
        )
        for contract in contracts
    ]
    
    return ContractListResponse(
        contracts=contract_items,
        total=len(contract_items),
    )


@router.get(
    "/contracts/{contract_id}",
    response_model=ContractListItem,
    status_code=status.HTTP_200_OK,
    summary="Get data contract by ID",
    description="Retrieve a specific data contract from the database by its ID",
    response_description="Contract details",
)
async def get_contract(
    contract_id: str,
    db: Session = Depends(get_db_session),
) -> ContractListItem:
    """
    Get a specific data contract from the database by ID.
    
    Args:
        contract_id: Contract ID (UUID)
        db: Database session dependency
        
    Returns:
        Contract details
        
    Raises:
        HTTPException: If contract not found or database query fails
    """
    try:
        contract_uuid = uuid.UUID(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contract ID format: {contract_id}",
        )
    
    contract = db.query(DataContractModel).filter(
        DataContractModel.id == contract_uuid
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract not found: {contract_id}",
        )
    
    return ContractListItem(
        id=str(contract.id),
        name=contract.name,
        version=contract.version,
        status=contract.status,
        description=contract.description,
        schema_id=str(contract.schema_id) if contract.schema_id else None,
        created_at=contract.created_at.isoformat() if contract.created_at else None,
        updated_at=contract.updated_at.isoformat() if contract.updated_at else None,
    )


@router.post(
    "/contracts/{contract_id}/build",
    response_model=ContractBuildResponse,
    status_code=status.HTTP_200_OK,
    summary="Build contract from contract ID",
    description="Reconstruct a complete data contract from a contract ID by fetching the associated schema and building the contract",
    response_description="Complete contract dictionary",
)
async def build_contract_from_id(
    contract_id: str,
    include_metadata: bool = Query(True, description="Include metadata in contract"),
    include_ownership: bool = Query(True, description="Include ownership information"),
    include_governance: bool = Query(True, description="Include governance rules"),
    db: Session = Depends(get_db_session),
    store: MetadataStoreClient = Depends(get_metadata_store),
) -> ContractBuildResponse:
    """
    Build a contract from a contract ID.
    
    This endpoint fetches the contract from the database, gets its schema_id,
    and then builds the complete contract from the metadata store.
    
    Args:
        contract_id: Contract ID (UUID)
        include_metadata: Whether to include metadata in the contract
        include_ownership: Whether to include ownership information
        include_governance: Whether to include governance rules
        db: Database session dependency
        store: Metadata store dependency
        
    Returns:
        Complete contract dictionary
        
    Raises:
        HTTPException: If contract not found or building fails
    """
    try:
        contract_uuid = uuid.UUID(contract_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid contract ID format: {contract_id}",
        )
    
    # Query contract - try UUID comparison first
    contract = db.query(DataContractModel).filter(
        DataContractModel.id == contract_uuid
    ).first()
    
    # If not found, try string comparison (for SQLite compatibility where UUIDs might be stored as strings)
    if not contract:
        from sqlalchemy import cast, String
        contract = db.query(DataContractModel).filter(
            cast(DataContractModel.id, String) == contract_id
        ).first()
    
    # Final fallback: query all and compare by string (for edge cases)
    if not contract:
        logger.warning(f"Contract not found with standard queries, trying fallback for: {contract_id}")
        all_contracts = db.query(DataContractModel).all()
        for c in all_contracts:
            c_id_str = str(c.id)
            if c_id_str == contract_id or c_id_str.lower() == contract_id.lower():
                contract = c
                logger.info(f"Found contract via string comparison: {c.id}")
                break
    
    if not contract:
        # Get diagnostic info for error message
        total = db.query(DataContractModel).count()
        all_contracts = db.query(DataContractModel).all()
        all_ids = [str(c.id) for c in all_contracts]
        logger.error(
            f"Contract not found: {contract_id} (UUID: {contract_uuid}). "
            f"Total contracts: {total}. "
            f"Available IDs: {all_ids}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract not found: {contract_id}",
        )
    
    if not contract.schema_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract {contract_id} does not have an associated schema",
        )
    
    built_contract = build_contract_from_store(
        store=store,
        schema_id=str(contract.schema_id),
        version=contract.schema_version,
        include_metadata=include_metadata,
        include_ownership=include_ownership,
        include_governance=include_governance,
    )
    
    if not built_contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found for contract: {contract_id}",
        )
    
    return ContractBuildResponse(contract=built_contract)
