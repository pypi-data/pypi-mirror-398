"""
ETL Orchestrator - Runtime ETL pipeline execution from contract artifacts.

PRIMARY INTERFACE: ETLOrchestrator Class
========================================

The ETLOrchestrator class is the recommended and primary way to execute ETL pipelines
in pycharter. It can be instantiated with contract artifacts from various sources:

    >>> from pycharter.etl_generator import ETLOrchestrator
    >>> 
    >>> # From contract directory (contains schema, coercion_rules, validation_rules, extract, transform, load)
    >>> orchestrator = ETLOrchestrator(contract_dir="data/contracts/user")
    >>> await orchestrator.run()
    >>> 
    >>> # From contract file
    >>> orchestrator = ETLOrchestrator(contract_file="contracts/user.yaml")
    >>> await orchestrator.run(dry_run=False)
    >>> 
    >>> # With direct ETL config dictionaries (overrides directory configs)
    >>> orchestrator = ETLOrchestrator(
    ...     contract_dir="data/contracts/user",
    ...     extract_config={"base_url": "https://api.example.com", "api_endpoint": "/v1/data"},
    ...     transform_config={"rename": {"oldName": "new_name"}},
    ...     load_config={"target_table": "users"}
    ... )
    >>> await orchestrator.run()
    >>> 
    >>> # With separate ETL config file paths (overrides directory configs)
    >>> orchestrator = ETLOrchestrator(
    ...     contract_dir="data/contracts/user",
    ...     extract_file="custom/extract.yaml",
    ...     transform_file="custom/transform.yaml",
    ...     load_file="custom/load.yaml"
    ... )
    >>> await orchestrator.run()
    >>> 
    >>> # Mixed approach - override specific configs
    >>> orchestrator = ETLOrchestrator(
    ...     contract_dir="data/contracts/user",
    ...     extract_config={"base_url": "https://custom.api.com"}  # Override extract only
    ...     # transform.yaml and load.yaml loaded from contract_dir
    ... )
    >>> await orchestrator.run()
    >>> 
    >>> # With direct ETL config dictionaries (overrides directory configs)
    >>> orchestrator = ETLOrchestrator(
    ...     contract_dir="data/contracts/user",
    ...     extract_config={"base_url": "https://api.example.com", ...},
    ...     transform_config={"rename": {...}},
    ...     load_config={"target_table": "users"}
    ... )
    >>> await orchestrator.run()
    >>> 
    >>> # With separate ETL config file paths (overrides directory configs)
    >>> orchestrator = ETLOrchestrator(
    ...     contract_dir="data/contracts/user",
    ...     extract_file="custom/extract.yaml",
    ...     transform_file="custom/transform.yaml",
    ...     load_file="custom/load.yaml"
    ... )
    >>> await orchestrator.run()

Core Components:
- orchestrator: ETLOrchestrator class (PRIMARY INTERFACE - use this for all ETL execution)
- config_generator: Utility functions for generating ETL configs from contracts (helper utilities)
"""

from pycharter.etl_generator.checkpoint import CheckpointManager, CheckpointState
from pycharter.etl_generator.config_generator import (
    generate_etl_config,
    generate_etl_config_from_contract,
    generate_etl_config_from_store,
)
from pycharter.etl_generator.orchestrator import (
    ETLOrchestrator,
    create_orchestrator,
)
from pycharter.etl_generator.progress import ETLProgress, ProgressTracker

__all__ = [
    # PRIMARY INTERFACE: ETLOrchestrator class (use this for all ETL execution)
    "ETLOrchestrator",
    "create_orchestrator",
    # Config generation utilities (helper functions for generating ETL configs)
    "generate_etl_config",
    "generate_etl_config_from_contract",
    "generate_etl_config_from_store",
    # Progress tracking
    "ETLProgress",
    "ProgressTracker",
    # Checkpoint/resume
    "CheckpointManager",
    "CheckpointState",
]
