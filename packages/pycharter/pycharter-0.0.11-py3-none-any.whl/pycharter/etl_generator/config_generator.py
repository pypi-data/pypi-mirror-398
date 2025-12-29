"""
ETL Configuration Generator - Generate YAML configs from data contracts.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml  # type: ignore[import-untyped]


def _json_type_to_etl_type(json_type: str, format_type: Optional[str] = None) -> str:
    """Convert JSON Schema type to ETL config type."""
    # Handle format-specific types
    if format_type == "date-time" or format_type == "timestamp":
        return "datetime"
    elif format_type == "date":
        return "date"
    elif format_type == "email" or format_type == "uri" or format_type == "url":
        return "string"
    
    # Map standard types
    type_mapping = {
        "string": "string",
        "integer": "integer",
        "number": "float",
        "boolean": "boolean",
        "array": "json",
        "object": "json",
    }
    
    return type_mapping.get(json_type, "string")


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    # Insert underscore before uppercase letters
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters that follow lowercase
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def _extract_field_definitions(
    schema: Dict[str, Any],
    api_field_naming: str = "camelCase",
    db_field_naming: str = "snake_case",
) -> List[Dict[str, Any]]:
    """
    Extract field definitions from JSON schema.
    
    Args:
        schema: JSON Schema dictionary
        api_field_naming: Naming convention for API fields (camelCase, snake_case, etc.)
        db_field_naming: Naming convention for DB fields (snake_case, etc.)
    
    Returns:
        List of field definitions matching ETL config format
    """
    fields = []
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))
    
    for field_name, field_schema in properties.items():
        if not isinstance(field_schema, dict):
            continue
        
        # Determine API field name (source)
        if api_field_naming == "camelCase":
            api_name = field_name  # Assume schema uses camelCase for API
        elif api_field_naming == "snake_case":
            api_name = field_name
        else:
            api_name = field_name
        
        # Determine DB field name (target)
        if db_field_naming == "snake_case":
            db_name = _camel_to_snake(field_name) if api_field_naming == "camelCase" else field_name
        else:
            db_name = field_name
        
        # Get type
        field_type = field_schema.get("type", "string")
        format_type = field_schema.get("format")
        etl_type = _json_type_to_etl_type(field_type, format_type)
        
        # Handle text vs string
        if etl_type == "string":
            max_length = field_schema.get("maxLength")
            if max_length and max_length > 255:
                etl_type = "text"
        
        # Check if required
        required = field_name in required_fields
        
        fields.append({
            "api_name": api_name,
            "db_name": db_name,
            "type": etl_type,
            "required": required,
        })
    
    return fields


def _extract_primary_key(schema: Dict[str, Any]) -> Optional[str]:
    """Extract primary key from schema (first required field with 'id' in name)."""
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    # Look for 'id' field first
    if "id" in properties and "id" in required_fields:
        return "id"
    
    # Look for fields with 'id' in name
    for field_name in required_fields:
        if "id" in field_name.lower():
            return _camel_to_snake(field_name)
    
    # Return first required field
    if required_fields:
        return _camel_to_snake(required_fields[0])
    
    return None


def _extract_unique_constraints(
    schema: Dict[str, Any],
    primary_key: Optional[str],
) -> List[List[str]]:
    """Extract unique constraints from schema."""
    constraints = []
    
    # Check for unique fields in schema
    properties = schema.get("properties", {})
    for field_name, field_schema in properties.items():
        if isinstance(field_schema, dict) and field_schema.get("unique"):
            db_name = _camel_to_snake(field_name)
            if db_name != primary_key:  # Don't duplicate primary key
                constraints.append([db_name])
    
    return constraints


def generate_etl_config(
    contract_name: str,
    schema: Dict[str, Any],
    extraction_config: Optional[Dict[str, Any]] = None,
    loading_config: Optional[Dict[str, Any]] = None,
    api_field_naming: str = "camelCase",
    db_field_naming: str = "snake_case",
    output_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Utility function to generate ETL configuration from a JSON schema.
    
    This is a helper utility function for generating ETL config files. For executing
    ETL pipelines, use the ETLOrchestrator class:
    
        >>> from pycharter.etl_generator import ETLOrchestrator
        >>> orchestrator = ETLOrchestrator(contract_dir="data/contracts/user")
        >>> await orchestrator.run()
    
    Use this function when you need to generate ETL config files programmatically.
    
    Args:
        contract_name: Name of the contract/pipeline
        schema: JSON Schema dictionary from contract
        extraction_config: Optional extraction configuration (provider, endpoint, etc.)
        loading_config: Optional loading configuration (table name, schema, etc.)
        api_field_naming: Naming convention for API fields
        db_field_naming: Naming convention for DB fields
        output_path: Optional path to write YAML file
    
    Returns:
        ETL configuration dictionary
    
    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "symbol": {"type": "string"},
        ...         "companyName": {"type": "string"}
        ...     },
        ...     "required": ["symbol"]
        ... }
        >>> config = generate_etl_config(
        ...     "company_profile",
        ...     schema,
        ...     extraction_config={"provider_name": "fmp", "api_endpoint": "/api/v3/profile/AAPL"}
        ... )
    """
    # Extract field definitions
    fields = _extract_field_definitions(schema, api_field_naming, db_field_naming)
    
    # Extract primary key
    primary_key = _extract_primary_key(schema)
    if primary_key:
        # Convert to snake_case if needed
        primary_key = _camel_to_snake(primary_key) if api_field_naming == "camelCase" else primary_key
    
    # Extract unique constraints
    unique_constraints = _extract_unique_constraints(schema, primary_key)
    
    # Build extraction config
    if extraction_config is None:
        extraction_config = {
            "provider_name": "fmp",  # Default
            "api_endpoint": f"/api/v3/{contract_name}",
            "method": "GET",
            "params": {},
            "rate_limit_delay": 0.2,
            "batch_size": 1000,
        }
    
    # Build loading config
    if loading_config is None:
        table_name = _camel_to_snake(contract_name)
        loading_config = {
            "target_table": table_name,
            "schema_name": "scraper",
            "write_method": "upsert",
            "primary_key": primary_key,
            "unique_constraints": unique_constraints if unique_constraints else [[primary_key]] if primary_key else [],
        }
    
    # Build complete config
    etl_config = {
        "job_name": contract_name,
        "execution_date": None,  # Will default to today
        "enabled": True,
        "extraction": extraction_config,
        "loading": loading_config,
        "fields": fields,
    }
    
    # Write to file if output_path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(etl_config, f, default_flow_style=False, sort_keys=False)
    
    return etl_config


def generate_etl_config_from_contract(
    contract: Dict[str, Any],
    contract_name: Optional[str] = None,
    extraction_config: Optional[Dict[str, Any]] = None,
    loading_config: Optional[Dict[str, Any]] = None,
    api_field_naming: str = "camelCase",
    db_field_naming: str = "snake_case",
    output_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Utility function to generate ETL configuration from a complete data contract.
    
    This is a helper utility function for generating ETL config files. For executing
    ETL pipelines, use the ETLOrchestrator class:
    
        >>> from pycharter.etl_generator import ETLOrchestrator
        >>> orchestrator = ETLOrchestrator(contract_file="contracts/user.yaml")
        >>> await orchestrator.run()
    
    Use this function when you need to generate ETL config files from contracts programmatically.
    
    Args:
        contract: Complete data contract dictionary
        contract_name: Optional contract name (extracted from contract if not provided)
        extraction_config: Optional extraction configuration
        loading_config: Optional loading configuration
        api_field_naming: Naming convention for API fields
        db_field_naming: Naming convention for DB fields
        output_path: Optional path to write YAML file
    
    Returns:
        ETL configuration dictionary
    """
    # Extract schema
    schema = contract.get("schema", {})
    if not schema:
        raise ValueError("Contract must have a 'schema' field")
    
    # Extract contract name
    if contract_name is None:
        contract_name = schema.get("title") or schema.get("name") or "etl_pipeline"
        # Sanitize name
        contract_name = re.sub(r"[^a-zA-Z0-9_]", "_", contract_name).lower()
    
    # Extract metadata for extraction/loading config hints
    metadata = contract.get("metadata", {})
    
    # Try to extract extraction hints from metadata
    if extraction_config is None and metadata:
        # Look for source information in metadata
        source_info = metadata.get("source") or metadata.get("extraction")
        if source_info:
            if isinstance(source_info, dict):
                extraction_config = {
                    "provider_name": source_info.get("provider", "fmp"),
                    "api_endpoint": source_info.get("endpoint", f"/api/v3/{contract_name}"),
                    "method": source_info.get("method", "GET"),
                    "params": source_info.get("params", {}),
                    "rate_limit_delay": source_info.get("rate_limit_delay", 0.2),
                    "batch_size": source_info.get("batch_size", 1000),
                }
    
    # Try to extract loading hints from metadata
    if loading_config is None and metadata:
        target_info = metadata.get("target") or metadata.get("loading")
        if target_info:
            if isinstance(target_info, dict):
                primary_key = _extract_primary_key(schema)
                loading_config = {
                    "target_table": target_info.get("table", _camel_to_snake(contract_name)),
                    "schema_name": target_info.get("schema", "scraper"),
                    "write_method": target_info.get("write_method", "upsert"),
                    "primary_key": target_info.get("primary_key", primary_key),
                    "unique_constraints": target_info.get("unique_constraints", []),
                }
    
    return generate_etl_config(
        contract_name=contract_name,
        schema=schema,
        extraction_config=extraction_config,
        loading_config=loading_config,
        api_field_naming=api_field_naming,
        db_field_naming=db_field_naming,
        output_path=output_path,
    )


def generate_etl_config_from_store(
    contract_name: str,
    version: Optional[str] = None,
    store: Any = None,  # MetadataStoreClient
    extraction_config: Optional[Dict[str, Any]] = None,
    loading_config: Optional[Dict[str, Any]] = None,
    api_field_naming: str = "camelCase",
    db_field_naming: str = "snake_case",
    output_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Utility function to generate ETL configuration from a contract stored in metadata store.
    
    This is a helper utility function for generating ETL config files. For executing
    ETL pipelines, use the ETLOrchestrator class:
    
        >>> from pycharter.etl_generator import ETLOrchestrator
        >>> orchestrator = ETLOrchestrator(contract_file="contracts/user.yaml")
        >>> await orchestrator.run()
    
    Use this function when you need to generate ETL config files from store contracts programmatically.
    
    Args:
        contract_name: Name of the contract
        version: Optional contract version (uses latest if not provided)
        store: MetadataStoreClient instance
        extraction_config: Optional extraction configuration
        loading_config: Optional loading configuration
        api_field_naming: Naming convention for API fields
        db_field_naming: Naming convention for DB fields
        output_path: Optional path to write YAML file
    
    Returns:
        ETL configuration dictionary
    """
    if store is None:
        raise ValueError("MetadataStoreClient instance is required")
    
    # Retrieve contract from store
    if version:
        contract = store.get_contract(contract_name, version)
    else:
        # Get latest version
        contract = store.get_contract(contract_name)
    
    if not contract:
        raise ValueError(f"Contract '{contract_name}' not found in store")
    
    return generate_etl_config_from_contract(
        contract=contract,
        contract_name=contract_name,
        extraction_config=extraction_config,
        loading_config=loading_config,
        api_field_naming=api_field_naming,
        db_field_naming=db_field_naming,
        output_path=output_path,
    )

