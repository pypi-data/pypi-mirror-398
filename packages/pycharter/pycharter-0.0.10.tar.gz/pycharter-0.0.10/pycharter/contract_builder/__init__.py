"""
Contract Builder Service

Constructs consolidated data contracts from separate artifacts (schema, coercion rules,
validation rules, metadata). Tracks versions of all components and produces a single
contract artifact suitable for runtime validation.
"""

from pycharter.contract_builder.builder import (
    ContractArtifacts,
    build_contract,
    build_contract_from_store,
)

__all__ = [
    "build_contract",
    "build_contract_from_store",
    "ContractArtifacts",
]
