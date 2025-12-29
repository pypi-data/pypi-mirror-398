"""
Value injection engine for PyCharter configuration files.

Supports Docker Compose-style variable substitution syntax:
- ${VAR} - Basic substitution
- ${VAR:-default} - Default value if VAR is unset or empty
- ${VAR:?error} - Required variable with error message
- $${VAR} - Escape literal ${VAR}

Values are resolved from:
1. Environment variables (highest priority)
2. pycharter.cfg config file [variables] section
3. Default values (if specified)
4. Error (if required and not found)
"""

import os
import re
from typing import Any, Dict, Optional

from pycharter.config import get_config_variable


class ValueInjector:
    """
    Value injection engine for resolving variables in configuration files.
    
    Supports Docker Compose-style syntax and resolves values from multiple sources
    with a clear priority order.
    
    Example:
        >>> injector = ValueInjector()
        >>> config = {"apikey": "${FMP_API_KEY:?API key required}", "timeout": "${TIMEOUT:-30}"}
        >>> resolved = injector.resolve(config)
    """
    
    # Pattern to match ${VAR}, ${VAR:-default}, ${VAR:?error}, or $${VAR}
    # Group 1: variable name
    # Group 2: default value (after :-) or None
    # Group 3: error message (after :?) or None
    # Group 4: escaped variable name
    # Uses alternation to correctly handle both :- and :? syntax
    _VAR_PATTERN = re.compile(
        r'\$\{([^}:]+)(?::-([^}]+)|:\?([^}]+))?\}|\$\$\{([^}]+)\}'
    )
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize value injector.
        
        Args:
            context: Optional context dictionary for additional variable sources
        """
        self.context = context or {}
    
    def resolve(self, data: Any, source_file: Optional[str] = None) -> Any:
        """
        Resolve all variable substitutions in data structure.
        
        Recursively processes dictionaries, lists, and strings to replace
        variable references with their resolved values.
        
        Args:
            data: Data structure to process (dict, list, str, or other)
            source_file: Optional source file path for error messages
            
        Returns:
            Data structure with all variables resolved
            
        Raises:
            ValueError: If a required variable (${VAR:?error}) is not found
        """
        if isinstance(data, dict):
            return {key: self.resolve(value, source_file) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.resolve(item, source_file) for item in data]
        elif isinstance(data, str):
            return self._resolve_string(data, source_file)
        else:
            return data
    
    def _resolve_string(self, value: str, source_file: Optional[str] = None) -> str:
        """
        Resolve variable substitutions in a string.
        
        Supports:
        - ${VAR} - Basic substitution
        - ${VAR:-default} - Default value
        - ${VAR:?error} - Required with error
        - $${VAR} - Escaped literal
        
        Args:
            value: String to process
            source_file: Optional source file path for error messages
            
        Returns:
            String with variables resolved
            
        Raises:
            ValueError: If a required variable is not found
        """
        if not isinstance(value, str):
            return value
        
        # Check if string contains any variable patterns
        if not self._VAR_PATTERN.search(value):
            return value
        
        def replace_var(match):
            """Replace a single variable match."""
            # Handle escaped variables: $${VAR} -> ${VAR}
            if match.group(4):
                return f"${{{match.group(4)}}}"
            
            var_name = match.group(1).strip()
            default_value = match.group(2)  # Default value (after :-)
            error_message = match.group(3)  # Error message (after :?)
            is_required = match.group(3) is not None  # Has :? syntax
            
            # Get value from sources (priority order)
            resolved_value = self._get_value(var_name)
            
            # Required variable (${VAR:?error})
            if is_required:
                if resolved_value is None or resolved_value == '':
                    error_msg = error_message or f"Environment variable {var_name} is required"
                    if source_file:
                        error_msg = f"{error_msg} (from {source_file})"
                    raise ValueError(error_msg)
                return resolved_value
            
            # Default value (${VAR:-default})
            if default_value is not None:
                return resolved_value if (resolved_value is not None and resolved_value != '') else default_value
            
            # Basic substitution (${VAR})
            if resolved_value is None:
                # Return original match if not found (backward compatibility)
                return match.group(0)  # Return the full ${VAR} string
            
            return resolved_value
        
        # Replace all occurrences
        result = self._VAR_PATTERN.sub(replace_var, value)
        return result
    
    def _get_value(self, var_name: str) -> Optional[str]:
        """
        Get variable value from available sources.
        
        Priority order:
        1. Context dictionary (if provided)
        2. Environment variables
        3. pycharter.cfg config file [variables] section
        4. pycharter.cfg config file [etl] section
        
        Args:
            var_name: Variable name to look up
            
        Returns:
            Variable value, or None if not found
        """
        # 1. Check context (highest priority)
        if var_name in self.context:
            value = self.context[var_name]
            return str(value) if value is not None else None
        
        # 2. Check environment variables
        env_value = os.getenv(var_name)
        if env_value is not None:
            return env_value
        
        # 3. Check config file [variables] section
        config_value = get_config_variable(var_name, section="variables")
        if config_value is not None:
            return config_value
        
        # 4. Check config file [etl] section
        config_value = get_config_variable(var_name, section="etl")
        if config_value is not None:
            return config_value
        
        return None


def resolve_values(data: Any, context: Optional[Dict[str, Any]] = None, source_file: Optional[str] = None) -> Any:
    """
    Convenience function to resolve variable substitutions in data.
    
    Args:
        data: Data structure to process
        context: Optional context dictionary for additional variables
        source_file: Optional source file path for error messages
        
    Returns:
        Data structure with all variables resolved
        
    Example:
        >>> config = {"apikey": "${FMP_API_KEY}", "timeout": "${TIMEOUT:-30}"}
        >>> resolved = resolve_values(config, source_file="extract.yaml")
    """
    injector = ValueInjector(context=context)
    return injector.resolve(data, source_file=source_file)

