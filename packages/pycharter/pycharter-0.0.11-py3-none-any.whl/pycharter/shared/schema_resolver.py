"""
Schema resolver for handling $ref references and definitions/$defs.
"""

from typing import Any, Dict, Optional


def resolve_refs(
    schema: Dict[str, Any],
    base_schema: Optional[Dict[str, Any]] = None,
    definitions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Resolve $ref references in a JSON schema.

    Supports both 'definitions' (Draft 7) and '$defs' (Draft 2020-12).

    Args:
        schema: The schema to resolve
        base_schema: The root schema (for resolving relative refs)
        definitions: Dictionary of definitions (if not in schema)

    Returns:
        Schema with all $ref references resolved
    """
    if base_schema is None:
        base_schema = schema

    # Get definitions from schema (support both 'definitions' and '$defs')
    if definitions is None:
        definitions = {}
        if "definitions" in base_schema:
            definitions.update(base_schema["definitions"])
        if "$defs" in base_schema:
            definitions.update(base_schema["$defs"])

    def _resolve(obj: Any, path: str = "#") -> Any:
        """Recursively resolve references."""
        if isinstance(obj, dict):
            # Check for $ref
            if "$ref" in obj:
                ref_path = obj["$ref"]

                # Handle local references (#/definitions/Name or #/$defs/Name)
                if ref_path.startswith("#/"):
                    ref_parts = ref_path[2:].split("/")

                    if ref_parts[0] in ["definitions", "$defs"]:
                        def_name = "/".join(ref_parts[1:])
                        if def_name in definitions:
                            # Resolve the referenced definition
                            resolved = _resolve(definitions[def_name], f"{path}/$ref")
                            # Merge any other properties from the $ref object
                            other_props = {k: v for k, v in obj.items() if k != "$ref"}
                            if other_props:
                                if isinstance(resolved, dict):
                                    resolved = {**resolved, **other_props}
                            return resolved

                # If we can't resolve it, return as-is
                return obj

            # Recursively process all values
            return {k: _resolve(v, f"{path}/{k}") for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_resolve(item, f"{path}[{i}]") for i, item in enumerate(obj)]
        else:
            return obj

    return _resolve(schema)


def normalize_schema_structure(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize schema structure to handle both Draft 7 and Draft 2020-12 formats.

    - Converts 'definitions' to '$defs' internally for consistency
    - Handles $schema and $id fields

    Args:
        schema: The schema to normalize

    Returns:
        Normalized schema
    """
    normalized = schema.copy()

    # If schema has 'definitions', also add it to '$defs' for internal use
    if "definitions" in normalized and "$defs" not in normalized:
        normalized["$defs"] = normalized["definitions"].copy()

    return normalized
