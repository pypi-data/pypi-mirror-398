"""
Shared utilities for runtime validation.
"""

import copy
from typing import Any, Dict, Optional


def merge_rules_into_schema(
    schema: Dict[str, Any],
    coercion_rules: Optional[Dict[str, Any]] = None,
    validation_rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Merge coercion and validation rules into a schema dictionary.
    
    This function deep copies the schema and merges rules into the properties.
    Coercion rules are added as a "coercion" field, while validation rules
    are merged directly into each property.
    
    Args:
        schema: Schema dictionary (will be deep copied)
        coercion_rules: Optional coercion rules dictionary mapping field names to coercion types
        validation_rules: Optional validation rules dictionary mapping field names to rule configs
    
    Returns:
        Complete schema with rules merged into properties
        
    Example:
        >>> schema = {"properties": {"age": {"type": "integer"}}}
        >>> coercion_rules = {"age": "coerce_to_integer"}
        >>> validation_rules = {"age": {"greater_than_or_equal_to": {"threshold": 0}}}
        >>> merged = merge_rules_into_schema(schema, coercion_rules, validation_rules)
        >>> merged["properties"]["age"]["coercion"]
        'coerce_to_integer'
    """
    complete_schema = copy.deepcopy(schema)
    
    # Early return if no rules to merge
    if not coercion_rules and not validation_rules:
        return complete_schema
    
    # Early return if schema has no properties
    if "properties" not in complete_schema:
        return complete_schema
    
    properties = complete_schema["properties"]
    
    # Merge coercion rules
    if coercion_rules:
        for field_name, coercion_name in coercion_rules.items():
            if field_name in properties:
                properties[field_name]["coercion"] = coercion_name
    
    # Merge validation rules
    if validation_rules:
        for field_name, rule_config in validation_rules.items():
            if field_name not in properties:
                continue
                
            if isinstance(rule_config, dict):
                # Merge each rule into the property
                for rule_name, rule_params in rule_config.items():
                    # Normalize None to empty dict for consistency
                    properties[field_name][rule_name] = rule_params if rule_params is not None else {}
            else:
                # Single validation rule (legacy format)
                properties[field_name]["validation"] = rule_config
    
    return complete_schema

