"""
Contract Validator Class - Runtime validation from contract artifacts.

This module provides a Validator class that can be instantiated with contract
artifacts (schema, coercion rules, validation rules) and performs validation
at runtime without code generation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml
from pydantic import BaseModel

from pycharter.contract_parser import ContractMetadata, parse_contract_file
from pycharter.metadata_store import MetadataStoreClient
from pycharter.pydantic_generator import from_dict
from pycharter.runtime_validator.utils import merge_rules_into_schema
from pycharter.runtime_validator.validator_core import ValidationResult, validate, validate_batch
from pycharter.utils.value_injector import resolve_values


class Validator:
    """
    Generic Validator that performs validation from contract artifacts.
    
    This class can be instantiated with contract files (schema.yaml, coercion_rules.yaml,
    validation_rules.yaml) or a contract directory, and then used to validate data.
    
    Example:
        >>> from pycharter.runtime_validator import Validator
        >>> 
        >>> # Initialize with contract directory
        >>> validator = Validator(
        ...     contract_dir="data/examples/fmp_stock_list"
        ... )
        >>> 
        >>> # Validate single record
        >>> result = validator.validate({"symbol": "AAPL", "company_name": "Apple Inc."})
        >>> if result.is_valid:
        ...     print(f"Valid: {result.data}")
        >>> 
        >>> # Validate batch
        >>> results = validator.validate_batch([record1, record2, record3])
        >>> valid_count = sum(1 for r in results if r.is_valid)
    """
    
    def __init__(
        self,
        contract_dir: Optional[str] = None,
        contract_file: Optional[str] = None,
        contract_dict: Optional[Dict[str, Any]] = None,
        contract_metadata: Optional[ContractMetadata] = None,
        store: Optional[MetadataStoreClient] = None,
        schema_id: Optional[str] = None,
        schema_version: Optional[str] = None,
    ):
        """
        Initialize the validator with contract artifacts.
        
        This is the primary and recommended way to perform validation in pycharter.
        The Validator class handles loading contracts from various sources and generates
        Pydantic models for validation.
        
        Args:
            contract_dir: Directory containing contract files (schema.yaml, coercion_rules.yaml, validation_rules.yaml)
            contract_file: Path to complete contract file (YAML/JSON)
            contract_dict: Contract as dictionary with 'schema', 'coercion_rules', 'validation_rules' keys
            contract_metadata: ContractMetadata object (from parse_contract)
            store: MetadataStoreClient instance (for loading from metadata store)
            schema_id: Schema identifier (required when using store)
            schema_version: Optional schema version (defaults to latest when using store)
        
        Example:
            >>> # From contract directory
            >>> validator = Validator(contract_dir="data/contracts/user")
            >>> result = validator.validate({"name": "Alice", "age": 30})
            
            >>> # From metadata store
            >>> store = SQLiteMetadataStore("metadata.db")
            >>> validator = Validator(store=store, schema_id="user_schema")
            >>> result = validator.validate({"name": "Alice", "age": 30})
        """
        self.schema = None
        self.coercion_rules = {}
        self.validation_rules = {}
        self.model: Optional[Type[BaseModel]] = None
        self._schema_from_store = False  # Flag to track if schema came from store (already merged)
        
        # Load from various sources (order matters - store takes precedence)
        if store and schema_id:
            self._load_from_store(store, schema_id, schema_version)
        elif contract_metadata:
            self._load_from_metadata(contract_metadata)
        elif contract_dict:
            self._load_from_dict(contract_dict)
        elif contract_file:
            self._load_from_file(Path(contract_file))
        elif contract_dir:
            self._load_from_directory(Path(contract_dir))
        else:
            raise ValueError(
                "Must provide one of: contract_dir, contract_file, contract_dict, "
                "contract_metadata, or (store + schema_id)"
            )
        
        # Generate Pydantic model from complete schema
        self._generate_model()
    
    def _load_from_store(
        self, store: MetadataStoreClient, schema_id: str, version: Optional[str] = None
    ) -> None:
        """
        Load contract from metadata store.
        
        The complete schema from the store already has rules merged,
        so we skip the merging step.
        
        Args:
            store: MetadataStoreClient instance
            schema_id: Schema identifier
            version: Optional schema version
            
        Raises:
            ValueError: If schema not found in store
        """
        complete_schema = store.get_complete_schema(schema_id, version)
        if not complete_schema:
            raise ValueError(f"Schema '{schema_id}' not found in store" + 
                           (f" (version: {version})" if version else ""))
        
        # The complete_schema already has rules merged by get_complete_schema()
        # Store it directly - no need to merge again
        self.schema = complete_schema
        self.coercion_rules = {}  # Already merged into schema
        self.validation_rules = {}  # Already merged into schema
        self._schema_from_store = True  # Flag to skip merging
    
    def _load_from_metadata(self, metadata: ContractMetadata) -> None:
        """
        Load contract from ContractMetadata object.
        
        Args:
            metadata: ContractMetadata object containing schema and rules
        """
        self.schema = metadata.schema
        self.coercion_rules = metadata.coercion_rules or {}
        self.validation_rules = metadata.validation_rules or {}
    
    def _load_from_dict(self, contract: Dict[str, Any]) -> None:
        """
        Load contract from dictionary.
        
        Args:
            contract: Dictionary with 'schema', 'coercion_rules', 'validation_rules' keys
            
        Raises:
            ValueError: If 'schema' key is missing
        """
        self.schema = contract.get("schema")
        if not self.schema:
            raise ValueError("Contract dictionary must contain 'schema' key")
        
        self.coercion_rules = self._extract_rules(contract.get("coercion_rules", {}))
        self.validation_rules = self._extract_rules(contract.get("validation_rules", {}))
    
    @staticmethod
    def _extract_rules(rules_data: Any) -> Dict[str, Any]:
        """
        Extract rules from various formats.
        
        Handles:
        - Direct rules dict: {"field1": "rule1", "field2": "rule2"}
        - Wrapped rules dict: {"rules": {"field1": "rule1"}}
        - Metadata dict with rules: {"version": "1.0", "rules": {...}}
        
        Args:
            rules_data: Rules data in various formats
            
        Returns:
            Dictionary of field_name -> rule mappings
        """
        if not isinstance(rules_data, dict):
            return {}
        
        # If "rules" key exists, extract it
        if "rules" in rules_data:
            return rules_data["rules"]
        
        # If it looks like a metadata dict (has version/description/title), return empty
        # Otherwise, assume it's a direct rules dict
        metadata_keys = {"version", "description", "title"}
        if metadata_keys.intersection(rules_data.keys()):
            return {}
        
        return rules_data
    
    def _load_from_file(self, file_path: Path) -> None:
        """
        Load contract from file.
        
        Args:
            file_path: Path to contract file (YAML/JSON)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        contract_metadata = parse_contract_file(str(file_path))
        self._load_from_metadata(contract_metadata)
    
    def _load_from_directory(self, contract_dir: Path):
        """
        Load contract components from directory.
        
        Expected files:
        - schema.yaml (required)
        - coercion_rules.yaml (optional)
        - validation_rules.yaml (optional)
        
        Args:
            contract_dir: Path to contract directory
            
        Raises:
            ValueError: If directory or schema file doesn't exist
        """
        if not contract_dir.exists():
            raise ValueError(f"Contract directory not found: {contract_dir}")
        
        # Load schema (required)
        schema_path = contract_dir / "schema.yaml"
        if not schema_path.exists():
            raise ValueError(f"Schema file not found: {schema_path}")
        
        self.schema = self._load_yaml(schema_path)
        
        # Load coercion rules (optional)
        coercion_path = contract_dir / "coercion_rules.yaml"
        if coercion_path.exists():
            coercion_data = self._load_yaml(coercion_path)
            self.coercion_rules = self._extract_rules(coercion_data)
        
        # Load validation rules (optional)
        validation_path = contract_dir / "validation_rules.yaml"
        if validation_path.exists():
            validation_data = self._load_yaml(validation_path)
            self.validation_rules = self._extract_rules(validation_data)
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse YAML file with variable substitution.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed YAML data as dictionary
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        # Resolve variable substitutions if data exists
        if data:
            data = resolve_values(data, source_file=str(file_path))
        
        return data
    
    def _merge_rules_into_schema(self) -> Dict[str, Any]:
        """
        Merge coercion and validation rules into schema.
        
        Returns:
            Complete schema with rules merged
            
        Raises:
            ValueError: If schema not loaded
        """
        if not self.schema:
            raise ValueError("Schema not loaded. Check contract loading.")
        
        # If schema came from store, it's already merged
        if self._schema_from_store:
            return self.schema
        
        return merge_rules_into_schema(self.schema, self.coercion_rules, self.validation_rules)
    
    def _generate_model(self) -> None:
        """
        Generate Pydantic model from complete schema.
        
        Raises:
            ValueError: If schema cannot be converted to model
        """
        complete_schema = self._merge_rules_into_schema()
        model_name = complete_schema.get("title", "DynamicModel")
        self.model = from_dict(complete_schema, model_name)
    
    def validate(
        self,
        data: Dict[str, Any],
        strict: bool = False,
    ) -> ValidationResult:
        """
        Validate a single data record against the contract.
        
        Args:
            data: Data dictionary to validate
            strict: If True, raise exceptions on validation errors
        
        Returns:
            ValidationResult object
        
        Example:
            >>> validator = Validator(contract_dir="data/examples/fmp_stock_list")
            >>> result = validator.validate({"symbol": "AAPL", "company_name": "Apple Inc."})
            >>> if result.is_valid:
            ...     print(f"Valid: {result.data.symbol}")
        """
        if not self.model:
            raise ValueError("Model not initialized. Check contract loading.")
        
        return validate(self.model, data, strict=strict)
    
    def validate_batch(
        self,
        data_list: List[Dict[str, Any]],
        strict: bool = False,
    ) -> List[ValidationResult]:
        """
        Validate a batch of data records against the contract.
        
        Args:
            data_list: List of data dictionaries to validate
            strict: If True, stop on first validation error
        
        Returns:
            List of ValidationResult objects
        
        Example:
            >>> validator = Validator(contract_dir="data/examples/fmp_stock_list")
            >>> results = validator.validate_batch([record1, record2, record3])
            >>> valid_count = sum(1 for r in results if r.is_valid)
            >>> invalid_count = sum(1 for r in results if not r.is_valid)
        """
        if not self.model:
            raise ValueError("Model not initialized. Check contract loading.")
        
        return validate_batch(self.model, data_list, strict=strict)
    
    def get_model(self) -> Type[BaseModel]:
        """
        Get the generated Pydantic model.
        
        Returns:
            Pydantic model class
        
        Example:
            >>> validator = Validator(contract_dir="data/examples/fmp_stock_list")
            >>> Model = validator.get_model()
            >>> # Use model directly
            >>> instance = Model(symbol="AAPL", company_name="Apple Inc.")
        """
        if not self.model:
            raise ValueError("Model not initialized. Check contract loading.")
        
        return self.model
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the complete schema (with rules merged).
        
        Returns:
            Complete schema dictionary
        """
        return self._merge_rules_into_schema()


# Convenience function for easy import
def create_validator(
    contract_dir: Optional[str] = None,
    **kwargs,
) -> Validator:
    """
    Create a Validator instance.
    
    Args:
        contract_dir: Directory containing contract files
        **kwargs: Additional arguments passed to Validator
    
    Returns:
        Validator instance
    
    Example:
        >>> from pycharter.runtime_validator import create_validator
        >>> validator = create_validator("data/examples/fmp_stock_list")
        >>> result = validator.validate({"symbol": "AAPL"})
    """
    return Validator(contract_dir=contract_dir, **kwargs)

