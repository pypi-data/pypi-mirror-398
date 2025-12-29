"""
Tests for Contract Parser service.

Tests the functionality of parsing data contract files and dictionaries
into ContractMetadata objects.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from pycharter.contract_parser import (
    ContractMetadata,
    parse_contract,
    parse_contract_file,
)


class TestParseContract:
    """Tests for parse_contract function."""

    def test_parse_basic_contract(self):
        """Test parsing a basic contract with schema only."""
        contract = {
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
            },
        }
        metadata = parse_contract(contract)

        assert isinstance(metadata, ContractMetadata)
        assert metadata.schema == contract["schema"]
        assert metadata.governance_rules == {}
        assert metadata.ownership == {}
        assert metadata.metadata == {}

    def test_parse_contract_with_all_components(self):
        """Test parsing a contract with all components."""
        contract = {
            "schema": {
                "type": "object",
                "version": "1.0.0",
                "properties": {"name": {"type": "string"}},
            },
            "governance_rules": {
                "data_retention": {"days": 365},
                "encryption": {"required": True},
            },
            "ownership": {
                "owner": "data-team",
                "team": "engineering",
            },
            "metadata": {
                "version": "1.0.0",
                "description": "User contract",
            },
        }
        metadata = parse_contract(contract)

        assert metadata.schema == contract["schema"]
        assert metadata.governance_rules == contract["governance_rules"]
        assert metadata.ownership == contract["ownership"]
        assert metadata.metadata == contract["metadata"]
        assert metadata.versions == {"schema": "1.0.0", "metadata": "1.0.0"}

    def test_parse_contract_with_version_tracking(self):
        """Test that versions are extracted from all components."""
        contract = {
            "schema": {"type": "object", "version": "2.0.0"},
            "metadata": {"version": "1.5.0"},
            "coercion_rules": {"version": "1.0.0", "rules": {}},
            "validation_rules": {"version": "1.2.0", "rules": {}},
            "versions": {"schema": "2.0.0", "custom": "1.0.0"},
        }
        metadata = parse_contract(contract)

        assert metadata.versions["schema"] == "2.0.0"
        assert metadata.versions["metadata"] == "1.5.0"
        assert metadata.versions["coercion_rules"] == "1.0.0"
        assert metadata.versions["validation_rules"] == "1.2.0"
        assert metadata.versions["custom"] == "1.0.0"  # From explicit versions dict

    def test_parse_contract_schema_as_root(self):
        """Test parsing when entire contract is a schema."""
        contract = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "governance_rules": {"retention": 365},
        }
        metadata = parse_contract(contract)

        assert metadata.schema["type"] == "object"
        assert "properties" in metadata.schema
        assert metadata.governance_rules == {"retention": 365}

    def test_parse_contract_minimal(self):
        """Test parsing minimal contract with just schema."""
        contract = {"schema": {"type": "string"}}
        metadata = parse_contract(contract)

        assert metadata.schema == {"type": "string"}
        assert metadata.versions == {}

    def test_contract_metadata_to_dict(self):
        """Test ContractMetadata.to_dict() method."""
        contract = {
            "schema": {"type": "object"},
            "ownership": {"owner": "team"},
            "metadata": {"description": "Test"},
        }
        metadata = parse_contract(contract)
        result = metadata.to_dict()

        assert result["schema"] == {"type": "object"}
        assert result["ownership"] == {"owner": "team"}
        assert result["metadata"] == {"description": "Test"}
        assert "versions" not in result  # Only included if versions exist

    def test_contract_metadata_to_dict_with_versions(self):
        """Test ContractMetadata.to_dict() includes versions when present."""
        contract = {
            "schema": {"type": "object", "version": "1.0.0"},
            "metadata": {"version": "1.0.0"},
        }
        metadata = parse_contract(contract)
        result = metadata.to_dict()

        assert "versions" in result
        assert result["versions"]["schema"] == "1.0.0"
        assert result["versions"]["metadata"] == "1.0.0"


class TestParseContractFile:
    """Tests for parse_contract_file function."""

    def test_parse_yaml_file(self):
        """Test parsing a YAML contract file."""
        contract_data = {
            "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
            "metadata": {"description": "Test contract"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(contract_data, f)
            temp_path = f.name

        try:
            metadata = parse_contract_file(temp_path)
            assert metadata.schema == contract_data["schema"]
            assert metadata.metadata == contract_data["metadata"]
        finally:
            Path(temp_path).unlink()

    def test_parse_json_file(self):
        """Test parsing a JSON contract file."""
        contract_data = {
            "schema": {"type": "object", "properties": {"age": {"type": "integer"}}},
            "ownership": {"owner": "data-team"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(contract_data, f)
            temp_path = f.name

        try:
            metadata = parse_contract_file(temp_path)
            assert metadata.schema == contract_data["schema"]
            assert metadata.ownership == contract_data["ownership"]
        finally:
            Path(temp_path).unlink()

    def test_parse_yml_file(self):
        """Test parsing a .yml file (alternative YAML extension)."""
        contract_data = {
            "schema": {"type": "string"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(contract_data, f)
            temp_path = f.name

        try:
            metadata = parse_contract_file(temp_path)
            assert metadata.schema == contract_data["schema"]
        finally:
            Path(temp_path).unlink()

    def test_parse_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            parse_contract_file("nonexistent_contract.yaml")

    def test_parse_unsupported_format(self):
        """Test that ValueError is raised for unsupported file formats."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("not a contract")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                parse_contract_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_invalid_file_content(self):
        """Test that ValueError is raised for invalid file content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not a valid json object")
            temp_path = f.name

        try:
            with pytest.raises((ValueError, json.JSONDecodeError)):
                parse_contract_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_file_with_version_tracking(self):
        """Test parsing file with version information."""
        contract_data = {
            "schema": {"type": "object", "version": "1.0.0"},
            "metadata": {"version": "1.0.0", "description": "Test"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(contract_data, f)
            temp_path = f.name

        try:
            metadata = parse_contract_file(temp_path)
            assert metadata.versions["schema"] == "1.0.0"
            assert metadata.versions["metadata"] == "1.0.0"
        finally:
            Path(temp_path).unlink()


class TestContractMetadata:
    """Tests for ContractMetadata class."""

    def test_contract_metadata_initialization(self):
        """Test ContractMetadata initialization."""
        schema = {"type": "object"}
        governance = {"retention": 365}
        ownership = {"owner": "team"}
        metadata_dict = {"description": "Test"}

        metadata = ContractMetadata(
            schema=schema,
            governance_rules=governance,
            ownership=ownership,
            metadata=metadata_dict,
        )

        assert metadata.schema == schema
        assert metadata.governance_rules == governance
        assert metadata.ownership == ownership
        assert metadata.metadata == metadata_dict

    def test_contract_metadata_defaults(self):
        """Test ContractMetadata with default values."""
        schema = {"type": "string"}
        metadata = ContractMetadata(schema=schema)

        assert metadata.schema == schema
        assert metadata.governance_rules == {}
        assert metadata.ownership == {}
        assert metadata.metadata == {}
        assert metadata.versions == {}

    def test_contract_metadata_with_versions(self):
        """Test ContractMetadata with version tracking."""
        schema = {"type": "object", "version": "1.0.0"}
        versions = {"schema": "1.0.0", "custom": "2.0.0"}

        metadata = ContractMetadata(schema=schema, versions=versions)

        assert metadata.versions == versions
