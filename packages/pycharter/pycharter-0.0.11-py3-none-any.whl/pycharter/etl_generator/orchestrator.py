"""
Generic ETL Orchestrator - Runtime ETL pipeline execution from contract artifacts.

This orchestrator reads contract artifacts (schema, coercion rules, validation rules)
and ETL configuration files (extract, transform, load) and executes the ETL pipeline
dynamically using streaming mode for memory-efficient processing.
"""

import asyncio
import gc
import warnings
from datetime import date, datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import yaml

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from pycharter.contract_parser import ContractMetadata, parse_contract_file
from pycharter.etl_generator.checkpoint import CheckpointManager
from pycharter.etl_generator.database import (
    get_database_connection,
    load_data,
)
from pycharter.etl_generator.extraction import extract_with_pagination_streaming
from pycharter.etl_generator.progress import ETLProgress, ProgressTracker
from pycharter.utils.value_injector import resolve_values


class ETLOrchestrator:
    """
    Generic ETL Orchestrator that executes pipelines from contract artifacts and ETL configs.
    
    Processes data in streaming mode: Extract-Batch → Transform-Batch → Load-Batch.
    This ensures constant memory usage regardless of dataset size.
    
    Example:
        >>> from pycharter.etl_generator import ETLOrchestrator
        >>> orchestrator = ETLOrchestrator(contract_dir="data/examples/my_contract")
        >>> await orchestrator.run()
    """
    
    def __init__(
        self,
        contract_dir: Optional[str] = None,
        contract_file: Optional[str] = None,
        contract_dict: Optional[Dict[str, Any]] = None,
        contract_metadata: Optional[ContractMetadata] = None,
        checkpoint_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[ETLProgress], None]] = None,
        verbose: bool = True,
        max_memory_mb: Optional[int] = None,
        config_context: Optional[Dict[str, Any]] = None,
        # ETL config options (alternative to loading from contract_dir)
        extract_config: Optional[Dict[str, Any]] = None,
        transform_config: Optional[Dict[str, Any]] = None,
        load_config: Optional[Dict[str, Any]] = None,
        extract_file: Optional[str] = None,
        transform_file: Optional[str] = None,
        load_file: Optional[str] = None,
    ):
        """
        Initialize the ETL orchestrator with contract artifacts.
        
        Args:
            contract_dir: Directory containing contract files and ETL configs
            contract_file: Path to complete contract file (YAML/JSON)
            contract_dict: Contract as dictionary
            contract_metadata: ContractMetadata object (from parse_contract)
            checkpoint_dir: Directory for checkpoint files (None = disabled)
            progress_callback: Optional callback for progress updates
            verbose: If True, print progress to stdout
            max_memory_mb: Maximum memory usage in MB (None = no limit)
            config_context: Optional context dictionary for value injection.
                          Values in this dict have highest priority when resolving
                          variables in config files (e.g., ${VAR}).
                          Useful for injecting application-level settings.
            extract_config: Optional extract configuration as dictionary.
                           If provided, overrides extract.yaml from contract_dir.
            transform_config: Optional transform configuration as dictionary.
                            If provided, overrides transform.yaml from contract_dir.
            load_config: Optional load configuration as dictionary.
                        If provided, overrides load.yaml from contract_dir.
            extract_file: Optional path to extract.yaml file.
                         If provided, overrides extract.yaml from contract_dir.
            transform_file: Optional path to transform.yaml file.
                           If provided, overrides transform.yaml from contract_dir.
            load_file: Optional path to load.yaml file.
                      If provided, overrides load.yaml from contract_dir.
        
        Note:
            ETL config priority: direct dict > file path > contract_dir
            If contract_dir is not provided, you must provide extract_config/transform_config/load_config
            or extract_file/transform_file/load_file.
        """
        self.contract_dir: Optional[Path] = None
        self.schema: Optional[Dict[str, Any]] = None
        self.coercion_rules: Dict[str, Any] = {}
        self.validation_rules: Dict[str, Any] = {}
        self.input_params: Dict[str, Dict[str, Any]] = {}
        
        # Configuration context for value injection
        self.config_context = config_context or {}
        
        # Store ETL config parameters for later loading
        self._extract_config_param = extract_config
        self._transform_config_param = transform_config
        self._load_config_param = load_config
        self._extract_file_param = extract_file
        self._transform_file_param = transform_file
        self._load_file_param = load_file
        
        # Enhanced features
        self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        self.progress_tracker = ProgressTracker(progress_callback, verbose)
        self.max_memory_mb = max_memory_mb
        self.process = None
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process()
        
        # Load contract artifacts
        if contract_metadata:
            self._load_from_metadata(contract_metadata)
        elif contract_dict:
            self._load_from_dict(contract_dict)
        elif contract_file:
            file_path = Path(contract_file)
            self.contract_dir = file_path.parent
            self._load_from_file(file_path)
        elif contract_dir:
            self.contract_dir = Path(contract_dir)
            self._load_from_directory(self.contract_dir)
        else:
            # If no contract source provided, we still need contract_dir for ETL configs
            # unless all ETL configs are provided directly
            if not (extract_config or extract_file) and not contract_dir:
                raise ValueError(
                    "Must provide one of: contract_dir, contract_file, contract_dict, "
                    "contract_metadata, or extract_config/extract_file"
                )
            # Set contract_dir to None if not provided (ETL configs will be loaded from params)
            self.contract_dir = None
        
        # Load ETL configurations (extract, transform, load)
        # Priority: direct dict > file path > contract_dir
        self._load_etl_configs()
    
    def _load_from_metadata(self, metadata: ContractMetadata) -> None:
        """Load contract from ContractMetadata object."""
        self.schema = metadata.schema
        self.coercion_rules = metadata.coercion_rules or {}
        self.validation_rules = metadata.validation_rules or {}
    
    def _load_from_dict(self, contract: Dict[str, Any]) -> None:
        """Load contract from dictionary."""
        self.schema = contract.get("schema")
        if not self.schema:
            raise ValueError("Contract dictionary must contain 'schema'")
        
        self.coercion_rules = self._extract_rules(contract.get("coercion_rules", {}))
        self.validation_rules = self._extract_rules(contract.get("validation_rules", {}))
    
    @staticmethod
    def _extract_rules(rules_data: Any) -> Dict[str, Any]:
        """Extract rules from various formats."""
        if not isinstance(rules_data, dict):
            return {}
        
        if "rules" in rules_data:
            return rules_data["rules"]
        elif not any(k in rules_data for k in ["version", "description", "title"]):
            return rules_data
        else:
            return {}
    
    def _load_from_file(self, file_path: Path) -> None:
        """Load contract from file."""
        contract_metadata = parse_contract_file(str(file_path))
        self._load_from_metadata(contract_metadata)
    
    def _load_from_directory(self, contract_dir: Path) -> None:
        """Load contract components from directory."""
        if not contract_dir.exists():
            raise ValueError(f"Contract directory not found: {contract_dir}")
        
        # Load schema (required) - support both YAML and JSON
        schema_path_yaml = contract_dir / "schema.yaml"
        schema_path_json = contract_dir / "schema.json"
        
        schema_path = None
        if schema_path_yaml.exists():
            schema_path = schema_path_yaml
        elif schema_path_json.exists():
            schema_path = schema_path_json
        else:
            # Try to find JSON schema files with dataset name pattern
            dataset_name = contract_dir.name
            possible_json_schemas = [
                contract_dir / f"{dataset_name}_schema.json",
                contract_dir / f"{dataset_name}.schema.json",
                contract_dir / "schema.json",
            ]
            for possible_path in possible_json_schemas:
                if possible_path.exists():
                    schema_path = possible_path
                    break
        
        if schema_path and schema_path.exists():
            if schema_path.suffix == '.json':
                import json
                with open(schema_path, 'r', encoding='utf-8') as f:
                    self.schema = json.load(f)
            else:
                self.schema = self._load_yaml(schema_path)
        else:
            raise ValueError(
                f"Schema file not found in {contract_dir}. "
                f"Expected: schema.yaml, schema.json, or {contract_dir.name}_schema.json"
            )
        
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
    
    def _load_etl_configs(self) -> None:
        """
        Load ETL configuration files (extract, transform, load).
        
        Priority order:
        1. Direct dictionary parameters (extract_config, transform_config, load_config)
        2. File path parameters (extract_file, transform_file, load_file)
        3. Files in contract_dir (extract.yaml, transform.yaml, load.yaml)
        """
        # Load extract config
        if self._extract_config_param is not None:
            # Priority 1: Direct dictionary
            self.extract_config = self._extract_config_param
        elif self._extract_file_param:
            # Priority 2: File path
            extract_path = Path(self._extract_file_param)
            if not extract_path.exists():
                raise ValueError(f"Extract config file not found: {extract_path}")
            self.extract_config = self._load_yaml(extract_path)
            # Set contract_dir from extract_file if not already set
            if not self.contract_dir:
                self.contract_dir = extract_path.parent
        elif self.contract_dir and self.contract_dir.exists():
            # Priority 3: From contract_dir
            self.extract_config = self._load_yaml(self.contract_dir / "extract.yaml")
        else:
            raise ValueError(
                "Extract configuration not found. Provide one of: "
                "extract_config (dict), extract_file (path), or contract_dir with extract.yaml"
            )
        
        if not self.extract_config:
            raise ValueError("Extract configuration is empty")
        
        # Load transform config
        if self._transform_config_param is not None:
            # Priority 1: Direct dictionary
            self.transform_config = self._transform_config_param
        elif self._transform_file_param:
            # Priority 2: File path
            transform_path = Path(self._transform_file_param)
            if not transform_path.exists():
                raise ValueError(f"Transform config file not found: {transform_path}")
            self.transform_config = self._load_yaml(transform_path)
        elif self.contract_dir and self.contract_dir.exists():
            # Priority 3: From contract_dir
            self.transform_config = self._load_yaml(self.contract_dir / "transform.yaml")
        else:
            # Transform config is optional
            self.transform_config = {}
        
        # Load load config
        if self._load_config_param is not None:
            # Priority 1: Direct dictionary
            self.load_config = self._load_config_param
        elif self._load_file_param:
            # Priority 2: File path
            load_path = Path(self._load_file_param)
            if not load_path.exists():
                raise ValueError(f"Load config file not found: {load_path}")
            self.load_config = self._load_yaml(load_path)
        elif self.contract_dir and self.contract_dir.exists():
            # Priority 3: From contract_dir
            self.load_config = self._load_yaml(self.contract_dir / "load.yaml")
        else:
            raise ValueError(
                "Load configuration not found. Provide one of: "
                "load_config (dict), load_file (path), or contract_dir with load.yaml"
            )
        
        if not self.load_config:
            raise ValueError("Load configuration is empty")
        
        # Parse input parameters from extract config
        input_params_config = self.extract_config.get('input_params', [])
        if isinstance(input_params_config, list):
            self.input_params = {name: {} for name in input_params_config}
        elif isinstance(input_params_config, dict):
            self.input_params = input_params_config
        else:
            self.input_params = {}
        
        if not self.schema:
            raise ValueError("Schema not loaded")
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file, return empty dict if not found."""
        if not file_path.exists():
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _prepare_params(self, **kwargs) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Prepare params and headers from config and kwargs."""
        params = self.extract_config.get('params', {}).copy()
        headers = self.extract_config.get('headers', {})
        
        # Merge input arguments
        for param_name, param_value in kwargs.items():
            if param_name in self.input_params:
                params[param_name] = param_value
            else:
                warnings.warn(
                    f"Unknown input parameter '{param_name}'. "
                    f"Available: {list(self.input_params.keys())}",
                    UserWarning
                )
        
        # Validate required input parameters
        for param_name, param_meta in self.input_params.items():
            if param_meta.get('required', False) and param_name not in params:
                raise ValueError(
                    f"Required input parameter '{param_name}' not provided. "
                    f"Please provide: {param_name}=value"
                )
        
        # Resolve values with config context
        source_file = str(self.contract_dir / "extract.yaml") if self.contract_dir else None
        params = resolve_values(params, context=self.config_context, source_file=source_file)
        headers = resolve_values(headers, context=self.config_context, source_file=source_file)
        
        return params, headers
    
    async def extract(
        self,
        batch_size: Optional[int] = None,
        max_records: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data in batches using async generator.
        
        Yields batches of records for memory-efficient processing.
        
        Args:
            batch_size: Number of records per batch (defaults to extract.yaml config)
            max_records: Maximum total records to extract (None = all)
            **kwargs: Input parameters defined in extract.yaml's input_params section
        
        Yields:
            Batches of extracted records (lists of dictionaries)
        
        Example:
            >>> async for batch in orchestrator.extract(symbol="AAPL"):
            ...     print(f"Extracted {len(batch)} records")
        """
        if batch_size is None:
            batch_size = self.extract_config.get('batch_size', 1000)
        
        params, headers = self._prepare_params(**kwargs)
        
        async for batch in extract_with_pagination_streaming(
            self.extract_config, params, headers, self.contract_dir, batch_size, max_records, config_context=self.config_context
        ):
            yield batch
    
    def transform(self, raw_data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Transform extracted data according to transformation rules.
        
        Args:
            raw_data: Raw data from extraction
            **kwargs: Additional transformation parameters
        
        Returns:
            Transformed data
        """
        if not self.transform_config:
            return raw_data
        
        transformed_data = []
        rename_rules = self.transform_config.get('rename', {})
        type_rules = self.transform_config.get('type', {})
        fill_null_rules = self.transform_config.get('fill_null', {})
        drop_fields = self.transform_config.get('drop', [])
        
        for record in raw_data:
            transformed_record = {}
            
            # Apply rename transformations
            for source_field, target_field in rename_rules.items():
                if source_field in record:
                    transformed_record[target_field] = record[source_field]
                elif target_field in record:
                    transformed_record[target_field] = record[target_field]
            
            # Copy remaining fields
            for key, value in record.items():
                if key not in rename_rules and key not in transformed_record:
                    if key not in drop_fields:
                        transformed_record[key] = value
            
            # Apply type conversions
            for field, field_type in type_rules.items():
                if field in transformed_record:
                    transformed_record[field] = self._convert_type(
                        transformed_record[field], field_type
                    )
            
            # Apply fill_null transformations
            for field, config in fill_null_rules.items():
                if field in transformed_record and transformed_record[field] is None:
                    if isinstance(config, dict):
                        transformed_record[field] = config.get('default')
                    else:
                        transformed_record[field] = config
            
            # Drop specified fields
            for field in drop_fields:
                transformed_record.pop(field, None)
            
            transformed_data.append(transformed_record)
        
        return transformed_data
    
    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        if value is None:
            return None
        
        type_map = {
            'string': str,
            'integer': int,
            'int': int,
            'float': float,
            'double': float,
            'boolean': bool,
            'bool': bool,
            'datetime': self._parse_datetime,
            'timestamp': self._parse_datetime,
            'date': self._parse_date,
        }
        
        converter = type_map.get(target_type.lower())
        if converter:
            try:
                return converter(value) if not callable(converter) else converter(value)
            except (ValueError, TypeError):
                return value
        
        return value
    
    def _parse_datetime(self, value: Any) -> Any:
        """Parse datetime value."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return value
    
    def _parse_date(self, value: Any) -> Any:
        """Parse date value."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                pass
        return value
    
    async def load(
        self,
        transformed_data: List[Dict[str, Any]],
        session: Any = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Load transformed data into the database."""
        target_table = self.load_config.get('target_table')
        schema_name = self.load_config.get('schema_name', 'scraper')
        write_method = self.load_config.get('write_method', 'upsert')
        primary_key = self.load_config.get('primary_key')
        batch_size = self.load_config.get('batch_size', 1000)
        
        if not target_table:
            raise ValueError("target_table not specified in load configuration")
        
        tunnel = None
        if session is None:
            try:
                engine, db_session, db_type, tunnel = get_database_connection(
                    self.load_config, self.contract_dir, config_context=self.config_context
                )
                try:
                    result = load_data(
                        transformed_data,
                        db_session,
                        schema_name,
                        target_table,
                        write_method,
                        primary_key,
                        batch_size,
                        db_type,
                    )
                    return result
                finally:
                    db_session.close()
                    if tunnel:
                        tunnel.stop()
            except Exception as e:
                if tunnel:
                    try:
                        tunnel.stop()
                    except Exception:
                        pass
                raise
        else:
            from pycharter.etl_generator.database import detect_database_type
            
            db_type = "postgresql"
            if hasattr(session, 'bind') and hasattr(session.bind, 'url'):
                db_url = str(session.bind.url)
                db_type = detect_database_type(db_url)
            
            return load_data(
                transformed_data,
                session,
                schema_name,
                target_table,
                write_method,
                primary_key,
                batch_size,
                db_type,
            )
    
    def _check_memory(self) -> Optional[float]:
        """Get current memory usage in MB, or None if psutil not available."""
        if not PSUTIL_AVAILABLE or not self.process:
            return None
        return self.process.memory_info().rss / 1024 / 1024
    
    def _enforce_memory_limit(self):
        """Check and enforce memory limits."""
        if self.max_memory_mb:
            current = self._check_memory()
            if current and current > self.max_memory_mb:
                gc.collect()
                current = self._check_memory()
                
                if current and current > self.max_memory_mb:
                    raise MemoryError(
                        f"Memory limit exceeded: {current:.1f}MB > {self.max_memory_mb}MB. "
                        f"Consider increasing batch_size."
                    )
    
    async def run(
        self,
        dry_run: bool = False,
        session: Any = None,
        checkpoint_id: Optional[str] = None,
        resume: bool = False,
        batch_size: Optional[int] = None,
        max_retries: int = 3,
        error_threshold: float = 0.1,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run the complete ETL pipeline in streaming mode.
        
        Processes data incrementally: Extract-Batch → Transform-Batch → Load-Batch.
        This ensures constant memory usage regardless of dataset size.
        
        Args:
            dry_run: If True, skip database operations
            session: Optional database session
            checkpoint_id: Optional checkpoint ID for resume capability
            resume: If True, resume from checkpoint
            batch_size: Batch size for processing (defaults to extract.yaml config)
            max_retries: Maximum retries for failed batches
            error_threshold: Error rate threshold (0.0-1.0) before aborting
            **kwargs: Additional parameters passed to extract()
            
        Returns:
            Pipeline execution results dictionary
        """
        if batch_size is None:
            batch_size = self.extract_config.get('batch_size', 1000)
        
        results = {
            'extraction': {'batches_processed': 0, 'total_records': 0},
            'transformation': {'batches_processed': 0, 'total_records': 0},
            'loading': {'batches_processed': 0, 'total_records': 0, 'inserted': 0, 'updated': 0},
            'success': False,
            'failed_batches': [],
        }
        
        # Load checkpoint if resuming
        start_batch = 0
        if resume and checkpoint_id:
            checkpoint_state = self.checkpoint_manager.load(checkpoint_id)
            if checkpoint_state:
                kwargs.update(checkpoint_state.last_processed_params)
                start_batch = checkpoint_state.batch_num
        
        self.progress_tracker.start()
        batch_num = 0
        total_records = 0
        failed_batches = []
        
        try:
            async for batch in self.extract(batch_size=batch_size, **kwargs):
                batch_num += 1
                
                # Skip batches if resuming
                if batch_num <= start_batch:
                    continue
                
                batch_start_time = datetime.now()
                
                try:
                    self._enforce_memory_limit()
                    
                    # Transform batch
                    transformed_batch = self.transform(batch, **kwargs)
                    
                    # Load batch
                    if not dry_run:
                        load_result = await self.load(transformed_batch, session=session, **kwargs)
                        results['loading']['inserted'] += load_result.get('inserted', 0)
                        results['loading']['updated'] += load_result.get('updated', 0)
                        results['loading']['total_records'] += load_result.get('total', 0)
                    
                    # Update counters
                    total_records += len(batch)
                    results['extraction']['total_records'] += len(batch)
                    results['extraction']['batches_processed'] = batch_num
                    results['transformation']['total_records'] += len(transformed_batch)
                    results['transformation']['batches_processed'] = batch_num
                    results['loading']['batches_processed'] = batch_num
                    
                    # Report progress
                    memory_usage = self._check_memory()
                    batch_time = (datetime.now() - batch_start_time).total_seconds()
                    self.progress_tracker.record_batch_time(batch_time)
                    self.progress_tracker.report(
                        'extract',
                        batch_num,
                        total_records,
                        memory_usage_mb=memory_usage,
                    )
                    
                    # Save checkpoint
                    if checkpoint_id:
                        self.checkpoint_manager.save(
                            checkpoint_id,
                            'extract',
                            batch_num,
                            total_records,
                            kwargs,
                        )
                    
                    # Cleanup
                    del batch, transformed_batch
                    gc.collect()
                    
                except Exception as e:
                    failed_batches.append({
                        'batch_num': batch_num,
                        'error': str(e),
                        'records': len(batch),
                    })
                    
                    # Check error rate
                    error_rate = len(failed_batches) / batch_num if batch_num > 0 else 1.0
                    if error_rate > error_threshold:
                        raise RuntimeError(
                            f"Error rate too high: {error_rate:.1%} > {error_threshold:.1%}. "
                            f"Aborting pipeline."
                        )
                    
                    # Retry logic
                    if len(failed_batches) <= max_retries:
                        await asyncio.sleep(2 ** len(failed_batches))
                        continue
                    else:
                        self.progress_tracker.report(
                            'extract',
                            batch_num,
                            total_records,
                            error_count=len(failed_batches),
                        )
            
            results['failed_batches'] = failed_batches
            results['success'] = len(failed_batches) < batch_num * error_threshold
            
            # Delete checkpoint on success
            if checkpoint_id and results['success']:
                self.checkpoint_manager.delete(checkpoint_id)
            
        except Exception as e:
            # Save error checkpoint
            if checkpoint_id:
                self.checkpoint_manager.save(
                    checkpoint_id,
                    'error',
                    batch_num,
                    total_records,
                    kwargs,
                    error=str(e),
                )
            results['error'] = str(e)
            results['success'] = False
            raise
        
        return results
    
    async def run_multiple(
        self,
        param_name: Optional[str] = None,
        param_values: Optional[List[Any]] = None,
        param_sets: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 5,
        delay_between_runs: float = 1.0,
        dry_run: bool = False,
        session: Any = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Run ETL pipeline multiple times with different parameter sets.
        
        This method allows you to efficiently run the same ETL pipeline multiple times
        with varying parameters. You can either:
        1. Provide a single parameter name and list of values (simple case)
        2. Provide a list of parameter dictionaries (complex case with multiple varying params)
        
        Args:
            param_name: Name of the parameter to vary (e.g., 'symbol', 'ticker', 'date')
                       Required if using param_values.
            param_values: List of values for the specified parameter.
                         Each value will be passed as {param_name: value} to run().
            param_sets: List of parameter dictionaries. Each dict will be unpacked
                       and passed to run() as **params. Use this when multiple
                       parameters vary between runs.
            batch_size: Number of runs to process before a brief pause (for rate limiting)
            delay_between_runs: Delay in seconds between individual runs (for rate limiting)
            dry_run: If True, skip database operations
            session: Optional database session
            **kwargs: Additional parameters passed to each run() call (common to all runs)
        
        Returns:
            List of result dictionaries, each containing:
            - 'params': The parameters used for this run
            - 'success': Whether the run succeeded
            - 'records': Number of records processed (if successful)
            - 'result': Full result dictionary from run() (if successful)
            - 'error': Error message (if failed)
        
        Examples:
            # Simple case: vary a single parameter
            >>> results = await orchestrator.run_multiple(
            ...     param_name='symbol',
            ...     param_values=['AAPL', 'MSFT', 'GOOGL'],
            ...     batch_size=5,
            ...     delay_between_runs=1.0
            ... )
            
            # Complex case: vary multiple parameters
            >>> results = await orchestrator.run_multiple(
            ...     param_sets=[
            ...         {'symbol': 'AAPL', 'date': '2024-01-01'},
            ...         {'symbol': 'MSFT', 'date': '2024-01-02'},
            ...     ],
            ...     batch_size=3,
            ...     delay_between_runs=0.5
            ... )
        """
        # Validate inputs
        if param_sets is not None:
            if param_name is not None or param_values is not None:
                raise ValueError(
                    "Cannot use both param_sets and param_name/param_values. "
                    "Use either param_sets OR param_name+param_values."
                )
            if not isinstance(param_sets, list) or len(param_sets) == 0:
                raise ValueError("param_sets must be a non-empty list of dictionaries")
            # Convert param_sets to list of dicts
            runs = [dict(params) for params in param_sets]
        elif param_name is not None and param_values is not None:
            if not isinstance(param_values, list) or len(param_values) == 0:
                raise ValueError("param_values must be a non-empty list")
            # Convert param_name + param_values to list of dicts
            runs = [{param_name: value} for value in param_values]
        else:
            raise ValueError(
                "Must provide either (param_name + param_values) OR param_sets"
            )
        
        results = []
        
        for i in range(0, len(runs), batch_size):
            run_batch = runs[i:i + batch_size]
            
            for run_params in run_batch:
                try:
                    # Merge run_params with common kwargs
                    merged_params = {**kwargs, **run_params}
                    result = await self.run(
                        dry_run=dry_run,
                        session=session,
                        **merged_params
                    )
                    results.append({
                        'params': run_params,
                        'success': result['success'],
                        'records': result.get('loading', {}).get('total_records', 0),
                        'result': result,
                    })
                except Exception as e:
                    results.append({
                        'params': run_params,
                        'success': False,
                        'error': str(e),
                    })
                
                # Rate limiting
                if i + batch_size < len(runs) or run_params != run_batch[-1]:
                    await asyncio.sleep(delay_between_runs)
        
        return results


def create_orchestrator(
    contract_dir: Optional[str] = None,
    **kwargs,
) -> ETLOrchestrator:
    """
    Create an ETL orchestrator instance.
    
    Args:
        contract_dir: Directory containing contract files and ETL configs
        **kwargs: Additional arguments passed to ETLOrchestrator
    
    Returns:
        ETLOrchestrator instance
    """
    return ETLOrchestrator(contract_dir=contract_dir, **kwargs)
