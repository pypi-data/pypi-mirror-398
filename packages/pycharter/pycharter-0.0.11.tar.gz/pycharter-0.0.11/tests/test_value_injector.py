"""
Tests for value injection engine.
"""

import os
import tempfile
from configparser import ConfigParser
from pathlib import Path

import pytest

from pycharter.utils.value_injector import ValueInjector, resolve_values


class TestValueInjector:
    """Test ValueInjector class."""
    
    def test_basic_substitution(self):
        """Test basic ${VAR} substitution."""
        os.environ["TEST_VAR"] = "test_value"
        try:
            injector = ValueInjector()
            result = injector.resolve("${TEST_VAR}")
            assert result == "test_value"
        finally:
            os.environ.pop("TEST_VAR", None)
    
    def test_default_value(self):
        """Test ${VAR:-default} syntax."""
        injector = ValueInjector()
        # Variable not set, should use default
        result = injector.resolve("${MISSING_VAR:-default_value}")
        assert result == "default_value"
        
        # Variable set, should use variable
        os.environ["TEST_VAR"] = "actual_value"
        try:
            result = injector.resolve("${TEST_VAR:-default_value}")
            assert result == "actual_value"
        finally:
            os.environ.pop("TEST_VAR", None)
    
    def test_required_variable(self):
        """Test ${VAR:?error} syntax."""
        injector = ValueInjector()
        
        # Variable not set, should raise error
        with pytest.raises(ValueError, match="MISSING_VAR is required"):
            injector.resolve("${MISSING_VAR:?MISSING_VAR is required}")
        
        # Variable set, should use variable
        os.environ["TEST_VAR"] = "actual_value"
        try:
            result = injector.resolve("${TEST_VAR:?error}")
            assert result == "actual_value"
        finally:
            os.environ.pop("TEST_VAR", None)
    
    def test_escaped_variable(self):
        """Test $${VAR} escape syntax."""
        injector = ValueInjector()
        result = injector.resolve("$${TEST_VAR}")
        assert result == "${TEST_VAR}"
    
    def test_partial_substitution(self):
        """Test partial string substitution."""
        os.environ["API_HOST"] = "api.example.com"
        try:
            injector = ValueInjector()
            result = injector.resolve("https://${API_HOST}/v1/endpoint")
            assert result == "https://api.example.com/v1/endpoint"
        finally:
            os.environ.pop("API_HOST", None)
    
    def test_nested_dict(self):
        """Test substitution in nested dictionaries."""
        os.environ["API_KEY"] = "secret_key"
        os.environ["TIMEOUT"] = "30"
        try:
            injector = ValueInjector()
            data = {
                "params": {
                    "apikey": "${API_KEY}",
                    "timeout": "${TIMEOUT}"
                },
                "headers": {
                    "Authorization": "Bearer ${API_KEY}"
                }
            }
            result = injector.resolve(data)
            assert result["params"]["apikey"] == "secret_key"
            assert result["params"]["timeout"] == "30"
            assert result["headers"]["Authorization"] == "Bearer secret_key"
        finally:
            os.environ.pop("API_KEY", None)
            os.environ.pop("TIMEOUT", None)
    
    def test_nested_list(self):
        """Test substitution in lists."""
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"
        try:
            injector = ValueInjector()
            data = ["${VAR1}", "static", "${VAR2}"]
            result = injector.resolve(data)
            assert result == ["value1", "static", "value2"]
        finally:
            os.environ.pop("VAR1", None)
            os.environ.pop("VAR2", None)
    
    def test_missing_variable_no_default(self):
        """Test missing variable without default returns original."""
        injector = ValueInjector()
        result = injector.resolve("${MISSING_VAR}")
        # Should return original string if variable not found
        assert result == "${MISSING_VAR}"
    
    def test_context_variables(self):
        """Test context dictionary as variable source."""
        injector = ValueInjector(context={"CTX_VAR": "context_value"})
        result = injector.resolve("${CTX_VAR}")
        assert result == "context_value"
    
    def test_priority_order(self):
        """Test priority: context > env > config > default."""
        # Set up context and env var
        injector = ValueInjector(context={"TEST_VAR": "context_value"})
        os.environ["TEST_VAR"] = "env_value"
        try:
            # Context should win
            result = injector.resolve("${TEST_VAR}")
            assert result == "context_value"
        finally:
            os.environ.pop("TEST_VAR", None)
    
    def test_config_file_variable(self, tmp_path):
        """Test reading variables from config file."""
        # Create temporary config file
        config_file = tmp_path / "pycharter.cfg"
        config = ConfigParser()
        config.add_section("variables")
        config.set("variables", "CONFIG_VAR", "config_value")
        with open(config_file, "w") as f:
            config.write(f)
        
        # Mock _find_config_file to return our temp file
        from pycharter import config as config_module
        original_find = config_module._find_config_file
        
        def mock_find(filename):
            if filename == "pycharter.cfg":
                return config_file
            return original_find(filename)
        
        config_module._find_config_file = mock_find
        
        try:
            injector = ValueInjector()
            result = injector.resolve("${CONFIG_VAR}")
            assert result == "config_value"
        finally:
            config_module._find_config_file = original_find
    
    def test_multiple_substitutions_in_string(self):
        """Test multiple variable substitutions in one string."""
        os.environ["HOST"] = "api.example.com"
        os.environ["PORT"] = "8080"
        try:
            injector = ValueInjector()
            result = injector.resolve("https://${HOST}:${PORT}/v1")
            assert result == "https://api.example.com:8080/v1"
        finally:
            os.environ.pop("HOST", None)
            os.environ.pop("PORT", None)
    
    def test_empty_string_default(self):
        """Test that empty string uses default value."""
        os.environ["EMPTY_VAR"] = ""
        try:
            injector = ValueInjector()
            result = injector.resolve("${EMPTY_VAR:-default}")
            assert result == "default"
        finally:
            os.environ.pop("EMPTY_VAR", None)
    
    def test_source_file_in_error(self):
        """Test that source file is included in error messages."""
        injector = ValueInjector()
        with pytest.raises(ValueError, match="from extract.yaml"):
            injector.resolve("${MISSING_VAR:?error}", source_file="extract.yaml")
    
    def test_complex_nested_structure(self):
        """Test complex nested structure with multiple variable types."""
        os.environ["API_KEY"] = "secret"
        os.environ["HOST"] = "api.example.com"
        try:
            injector = ValueInjector()
            data = {
                "extract": {
                    "params": {
                        "apikey": "${API_KEY:?API key required}",
                        "timeout": "${TIMEOUT:-30}"
                    },
                    "base_url": "https://${HOST}/v1",
                    "headers": ["Authorization: Bearer ${API_KEY}", "Content-Type: application/json"]
                }
            }
            result = injector.resolve(data)
            assert result["extract"]["params"]["apikey"] == "secret"
            assert result["extract"]["params"]["timeout"] == "30"
            assert result["extract"]["base_url"] == "https://api.example.com/v1"
            assert result["extract"]["headers"][0] == "Authorization: Bearer secret"
        finally:
            os.environ.pop("API_KEY", None)
            os.environ.pop("HOST", None)


class TestResolveValuesFunction:
    """Test resolve_values convenience function."""
    
    def test_basic_usage(self):
        """Test basic usage of resolve_values function."""
        os.environ["TEST_VAR"] = "test_value"
        try:
            result = resolve_values("${TEST_VAR}")
            assert result == "test_value"
        finally:
            os.environ.pop("TEST_VAR", None)
    
    def test_with_context(self):
        """Test resolve_values with context."""
        result = resolve_values("${CTX_VAR}", context={"CTX_VAR": "context_value"})
        assert result == "context_value"
    
    def test_with_source_file(self):
        """Test resolve_values with source file."""
        with pytest.raises(ValueError, match="from config.yaml"):
            resolve_values("${MISSING:?error}", source_file="config.yaml")

