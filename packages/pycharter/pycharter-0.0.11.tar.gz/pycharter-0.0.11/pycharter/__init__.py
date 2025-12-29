"""
PyCharter - Data Contract Management and Validation

Six core services:
1. Contract Parser - Reads and decomposes data contract files
1b. Contract Builder - Constructs consolidated contracts from separate artifacts
2. Metadata Store Client - Database operations for metadata storage
3. Pydantic Generator - Generates Pydantic models from JSON Schema
4. JSON Schema Converter - Converts Pydantic models to JSON Schema
5. Runtime Validator - Lightweight validation utility
"""

__version__ = "0.0.2"

# Service 1b: Contract Builder
from pycharter.contract_builder import (
    ContractArtifacts,
    build_contract,
    build_contract_from_store,
)

# Service 1: Contract Parser
from pycharter.contract_parser import (
    ContractMetadata,
    parse_contract,
    parse_contract_file,
)

# Service 2: Metadata Store Client
from pycharter.metadata_store import MetadataStoreClient

# Optional metadata store implementations
try:
    from pycharter.metadata_store import InMemoryMetadataStore
except ImportError:
    InMemoryMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store import MongoDBMetadataStore
except ImportError:
    MongoDBMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store import PostgresMetadataStore
except ImportError:
    PostgresMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store import RedisMetadataStore
except ImportError:
    RedisMetadataStore = None  # type: ignore[assignment,misc]

# Service 4: JSON Schema Converter
from pycharter.json_schema_converter import (
    model_to_schema,
    to_dict,
    to_file,
    to_json,
)

# Service 3: Pydantic Generator
from pycharter.pydantic_generator import (
    from_dict,
    from_file,
    from_json,
    from_url,
    generate_model,
    generate_model_file,
)

# Service 5: Runtime Validator
from pycharter.runtime_validator import (
    ValidationResult,
    get_model_from_contract,
    get_model_from_store,
    validate,
    validate_batch,
    validate_batch_with_contract,
    validate_batch_with_store,
    validate_input,
    validate_output,
    validate_with_contract,
    validate_with_contract_decorator,
    validate_with_store,
)

# Service 6: Quality Assurance
from pycharter.quality import (
    DataProfiler,
    FieldQualityMetrics,
    QualityCheck,
    QualityCheckOptions,
    QualityMetrics,
    QualityReport,
    QualityScore,
    QualityThresholds,
    ViolationRecord,
    ViolationTracker,
)

__all__ = [
    # Contract Parser
    "parse_contract",
    "parse_contract_file",
    "ContractMetadata",
    # Contract Builder
    "build_contract",
    "build_contract_from_store",
    "ContractArtifacts",
    # Metadata Store Client
    "MetadataStoreClient",
    "InMemoryMetadataStore",
    "MongoDBMetadataStore",
    "PostgresMetadataStore",
    "RedisMetadataStore",
    # Pydantic Generator
    "generate_model",
    "generate_model_file",
    "from_dict",
    "from_file",
    "from_json",
    "from_url",
    # JSON Schema Converter
    "to_dict",
    "to_file",
    "to_json",
    "model_to_schema",
    # Runtime Validator
    "validate",
    "validate_batch",
    "ValidationResult",
    # Database-backed validation
    "validate_with_store",
    "validate_batch_with_store",
    "get_model_from_store",
    # Contract-based validation (no database)
    "validate_with_contract",
    "validate_batch_with_contract",
    "get_model_from_contract",
    # Decorators
    "validate_input",
    "validate_output",
    "validate_with_contract_decorator",
    # Quality Assurance
    "QualityCheck",
    "QualityMetrics",
    "QualityScore",
    "QualityReport",
    "QualityThresholds",
    "QualityCheckOptions",
    "FieldQualityMetrics",
    "ViolationTracker",
    "ViolationRecord",
    "DataProfiler",
]
