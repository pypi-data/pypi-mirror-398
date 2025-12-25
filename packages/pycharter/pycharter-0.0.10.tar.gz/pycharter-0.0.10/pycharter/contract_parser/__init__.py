"""
Contract Parser Service

Reads data contract files (YAML or JSON) and decomposes them into distinct metadata components.
"""

from pycharter.contract_parser.parser import (
    ContractMetadata,
    parse_contract,
    parse_contract_file,
)

__all__ = [
    "parse_contract",
    "parse_contract_file",
    "ContractMetadata",
]
