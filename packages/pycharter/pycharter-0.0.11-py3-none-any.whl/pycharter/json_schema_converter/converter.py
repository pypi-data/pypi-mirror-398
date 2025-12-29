"""
Convert Pydantic models to JSON Schema.

This module handles the reverse conversion: Pydantic models → JSON Schema,
including field validators (pre and post) and nested schemas.
"""

import inspect
import re
from typing import Any, Dict, List, Optional, Set, Type, Union, get_args, get_origin

from pydantic import BaseModel, Field, field_validator
from pydantic.fields import FieldInfo

from pycharter.shared.coercions import get_coercion
from pycharter.shared.validations import get_validation


def _python_type_to_json_type(python_type: Type[Any]) -> str:
    """
    Map Python type to JSON Schema type.

    Args:
        python_type: Python type

    Returns:
        JSON Schema type string
    """
    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    # Handle Optional types
    origin = get_origin(python_type)
    if origin is Union:
        args = get_args(python_type)
        # Filter out None for Optional
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            return _python_type_to_json_type(non_none_args[0])

    # Check direct mapping
    if python_type in type_mapping:
        return type_mapping[python_type]

    # Check if it's a subclass of BaseModel (nested model)
    if inspect.isclass(python_type) and issubclass(python_type, BaseModel):
        return "object"

    # Default to string
    return "string"


def _extract_field_constraints(field_info: FieldInfo) -> Dict[str, Any]:
    """
    Extract JSON Schema constraints from Pydantic Field.

    Args:
        field_info: Pydantic FieldInfo object

    Returns:
        Dictionary of JSON Schema constraints
    """
    constraints: Dict[str, Any] = {}

    # In Pydantic v2, constraints are stored in json_schema_extra or as attributes
    # Try to get JSON schema from the field
    try:
        # Get the JSON schema for this field
        json_schema = field_info.json_schema()  # type: ignore[attr-defined]

        # Extract constraints from JSON schema
        if "minLength" in json_schema:
            constraints["minLength"] = json_schema["minLength"]
        if "maxLength" in json_schema:
            constraints["maxLength"] = json_schema["maxLength"]
        if "pattern" in json_schema:
            constraints["pattern"] = json_schema["pattern"]
        if "minimum" in json_schema:
            constraints["minimum"] = json_schema["minimum"]
        if "exclusiveMinimum" in json_schema:
            constraints["exclusiveMinimum"] = json_schema["exclusiveMinimum"]
        if "maximum" in json_schema:
            constraints["maximum"] = json_schema["maximum"]
        if "exclusiveMaximum" in json_schema:
            constraints["exclusiveMaximum"] = json_schema["exclusiveMaximum"]
        if "multipleOf" in json_schema:
            constraints["multipleOf"] = json_schema["multipleOf"]
        if "minItems" in json_schema:
            constraints["minItems"] = json_schema["minItems"]
        if "maxItems" in json_schema:
            constraints["maxItems"] = json_schema["maxItems"]
    except (AttributeError, TypeError):
        # Fallback: try direct attribute access (Pydantic v1 or different structure)
        if hasattr(field_info, "min_length") and field_info.min_length is not None:
            constraints["minLength"] = field_info.min_length
        if hasattr(field_info, "max_length") and field_info.max_length is not None:
            constraints["maxLength"] = field_info.max_length
        if hasattr(field_info, "pattern") and field_info.pattern:
            constraints["pattern"] = field_info.pattern
        if hasattr(field_info, "ge") and field_info.ge is not None:
            constraints["minimum"] = field_info.ge
        if hasattr(field_info, "gt") and field_info.gt is not None:
            constraints["exclusiveMinimum"] = field_info.gt
        if hasattr(field_info, "le") and field_info.le is not None:
            constraints["maximum"] = field_info.le
        if hasattr(field_info, "lt") and field_info.lt is not None:
            constraints["exclusiveMaximum"] = field_info.lt
        if hasattr(field_info, "multiple_of") and field_info.multiple_of is not None:
            constraints["multipleOf"] = field_info.multiple_of

    # Description
    if hasattr(field_info, "description") and field_info.description:
        constraints["description"] = field_info.description

    return constraints


def _extract_literal_values(python_type: Type[Any]) -> Optional[List[Any]]:
    """
    Extract values from Literal type for enum/const.

    Args:
        python_type: Python type (may be Literal)

    Returns:
        List of literal values if Literal type, None otherwise
    """
    origin = get_origin(python_type)

    if origin is not None:
        # Handle Union[Literal[...], None] (Optional Literal)
        if origin is Union:
            args = get_args(python_type)
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                return _extract_literal_values(non_none_args[0])
        return None

    # Check if it's a Literal type (Python 3.8+)
    if hasattr(python_type, "__origin__") and python_type.__origin__ is Union:
        # Handle Literal types
        args = get_args(python_type)
        # Check if all args are literals (not types)
        if args and all(not inspect.isclass(arg) for arg in args):
            return list(args)

    # Try to get literal values from __args__
    if hasattr(python_type, "__args__"):
        args = python_type.__args__
        if args and all(not inspect.isclass(arg) for arg in args):
            return list(args)

    return None


def _identify_validator_function(
    validator_func: Any, field_name: str
) -> Optional[Dict[str, Any]]:
    """
    Try to identify if a validator function matches a known coercion or validation.

    Args:
        validator_func: The validator function
        field_name: Name of the field

    Returns:
        Dict with 'coercion' or 'validation' info, or None if not recognized
    """
    func_name = getattr(validator_func, "__name__", "")
    func_code = getattr(validator_func, "__code__", None)

    # Check if it's a known coercion
    try:
        # Try to match by function reference or name
        for coercion_name in [
            "coerce_to_string",
            "coerce_to_integer",
            "coerce_to_float",
            "coerce_to_boolean",
            "coerce_to_datetime",
            "coerce_to_uuid",
        ]:
            try:
                registered_coercion = get_coercion(coercion_name)
                if validator_func == registered_coercion or func_name == coercion_name:
                    return {"coercion": coercion_name}
            except ValueError:
                continue
    except Exception:
        pass

    # Check if it's a known validation
    # This is trickier because validations are factory functions
    # We'll need to inspect the function more carefully
    try:
        for validation_name in [
            "min_length",
            "max_length",
            "only_allow",
            "greater_than_or_equal_to",
            "less_than_or_equal_to",
            "no_capital_characters",
            "no_special_characters",
        ]:
            try:
                # Get the factory function
                validation_factory = get_validation(validation_name)
                # Check if validator_func was created by this factory
                # This is a heuristic - we check function attributes
                if (
                    hasattr(validator_func, "__closure__")
                    and validator_func.__closure__
                ):
                    # Check if closure contains the factory
                    closure_vars = [c.cell_contents for c in validator_func.__closure__]
                    if any(
                        callable(v) and v == validation_factory for v in closure_vars
                    ):
                        # Try to extract config from closure
                        # This is approximate - we may need to store metadata
                        return {"validation": validation_name, "config": {}}
            except (ValueError, AttributeError):
                continue
    except Exception:
        pass

    return None


def _extract_validators_from_model(model: Type[BaseModel]) -> Dict[str, Dict[str, Any]]:
    """
    Extract field validators from a Pydantic model.

    Args:
        model: Pydantic model class

    Returns:
        Dict mapping field_name to validator info (coercion/validations)
    """
    validators: Dict[str, Dict[str, Any]] = {}

    # Get all class attributes
    for attr_name in dir(model):
        if attr_name.startswith("_coerce_") or attr_name.startswith("_validate_"):
            attr = getattr(model, attr_name)

            # Extract field name from attribute name
            if attr_name.startswith("_coerce_"):
                field_name = attr_name.replace("_coerce_", "")
            else:
                # _validate_fieldname_0 -> fieldname
                field_name = re.sub(r"_validate_([^_]+).*", r"\1", attr_name)

            if field_name not in validators:
                validators[field_name] = {"coercion": None, "validations": {}}

            # Check if it's a field_validator
            if hasattr(attr, "__wrapped__"):
                wrapped = attr.__wrapped__
                # Check mode
                if hasattr(attr, "__pydantic_field_validator__"):
                    validator_info = attr.__pydantic_field_validator__
                    mode = getattr(validator_info, "mode", "after")

                    # Get the actual validator function
                    if hasattr(wrapped, "__func__"):
                        validator_func = wrapped.__func__
                    else:
                        validator_func = wrapped

                    # Try to identify the validator
                    validator_id = _identify_validator_function(
                        validator_func, field_name
                    )

                    if validator_id:
                        if "coercion" in validator_id and mode == "before":
                            validators[field_name]["coercion"] = validator_id[
                                "coercion"
                            ]
                        elif "validation" in validator_id and mode == "after":
                            validation_name = validator_id["validation"]
                            validators[field_name]["validations"][validation_name] = (
                                validator_id.get("config", {})
                            )

    return validators


def _process_field_type(
    field_type: Type[Any], model: Type[BaseModel], processed_models: Set[str]
) -> Dict[str, Any]:
    """
    Process a field type and convert it to JSON Schema.

    Args:
        field_type: Python type of the field
        model: The model this field belongs to (for nested models)
        processed_models: Set of already processed model names (to avoid cycles)

    Returns:
        JSON Schema dictionary for the field type
    """
    schema: Dict[str, Any] = {}

    # Check for Literal (enum/const)
    literal_values = _extract_literal_values(field_type)
    if literal_values:
        if len(literal_values) == 1:
            schema["const"] = literal_values[0]
        else:
            schema["enum"] = literal_values
        # Still need to determine base type
        if literal_values:
            first_value = literal_values[0]
            if isinstance(first_value, str):
                schema["type"] = "string"
            elif isinstance(first_value, int):
                schema["type"] = "integer"
            elif isinstance(first_value, float):
                schema["type"] = "number"
            elif isinstance(first_value, bool):
                schema["type"] = "boolean"
        return schema

    # Handle Optional
    origin = get_origin(field_type)
    if origin is Union:
        args = get_args(field_type)
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            field_type = non_none_args[0]
            origin = get_origin(field_type)

    # Handle List/Array
    if origin is list or (
        hasattr(field_type, "__origin__") and field_type.__origin__ is list
    ):
        schema["type"] = "array"
        args = get_args(field_type)
        if args:
            item_schema = _process_field_type(args[0], model, processed_models)
            schema["items"] = item_schema
        else:
            schema["items"] = {}
        return schema

    # Handle nested BaseModel
    if inspect.isclass(field_type) and issubclass(field_type, BaseModel):
        nested_schema = model_to_schema(field_type, processed_models=processed_models)
        schema.update(nested_schema)
        return schema

    # Basic type
    json_type = _python_type_to_json_type(field_type)
    schema["type"] = json_type

    return schema


def _normalize_anyof_to_type_list(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert anyOf patterns for nullable types to the more readable list notation.
    
    Converts:
        {"anyOf": [{"type": "number"}, {"type": "null"}]}
        {"anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}]}
    To:
        {"type": ["number", "null"]}
        {"type": ["string", "null"], "format": "date-time"}
    
    Args:
        schema: JSON Schema dictionary (can be nested)
    
    Returns:
        Normalized schema with anyOf converted to type arrays
    """
    if isinstance(schema, dict):
        # Check if this is an anyOf pattern we can simplify
        if "anyOf" in schema and isinstance(schema["anyOf"], list):
            anyof_items = schema["anyOf"]
            # Check if it's a simple nullable type pattern
            if len(anyof_items) == 2:
                null_item = None
                type_item = None
                
                for item in anyof_items:
                    if isinstance(item, dict):
                        if item.get("type") == "null":
                            null_item = item
                        elif "type" in item:
                            type_item = item
                
                # If we have exactly one type + null, convert to list notation
                if null_item is not None and type_item is not None:
                    new_schema = schema.copy()
                    del new_schema["anyOf"]
                    
                    # Extract the type
                    type_value = type_item["type"]
                    new_schema["type"] = [type_value, "null"]
                    
                    # Copy other properties from the type item (like format, etc.)
                    for key, value in type_item.items():
                        if key != "type":
                            new_schema[key] = value
                    
                    return new_schema
        
        # Recursively process nested schemas
        return {k: _normalize_anyof_to_type_list(v) for k, v in schema.items()}
    elif isinstance(schema, list):
        return [_normalize_anyof_to_type_list(item) for item in schema]
    else:
        return schema


def _extract_version_from_model(model: Type[BaseModel]) -> Optional[str]:
    """
    Extract version from a Pydantic model.

    Checks multiple sources in order:
    1. __version__ class variable (ClassVar or regular attribute)
    2. schema_version class variable (ClassVar or regular attribute)
    3. model_config.json_schema_extra["version"]
    4. model_config.json_schema_extra.get("version")

    Args:
        model: Pydantic model class

    Returns:
        Version string if found, None otherwise
    """
    # Check class variables (including ClassVar)
    if hasattr(model, "__version__"):
        version = getattr(model, "__version__")
        # Handle ClassVar - it's stored in __annotations__
        if isinstance(version, str):
            return version
        # If it's a ClassVar descriptor, try to get the actual value
        if hasattr(version, "__get__"):
            try:
                actual_version = version.__get__(None, model)
                if isinstance(actual_version, str):
                    return actual_version
            except (AttributeError, TypeError):
                pass

    if hasattr(model, "schema_version"):
        version = getattr(model, "schema_version")
        if isinstance(version, str):
            return version
        # Handle ClassVar
        if hasattr(version, "__get__"):
            try:
                actual_version = version.__get__(None, model)
                if isinstance(actual_version, str):
                    return actual_version
            except (AttributeError, TypeError):
                pass

    # Check model_config (Pydantic v2)
    if hasattr(model, "model_config"):
        config = model.model_config
        if hasattr(config, "json_schema_extra"):  # type: ignore[attr-defined]
            json_schema_extra = config.json_schema_extra  # type: ignore[attr-defined]
            if isinstance(json_schema_extra, dict) and "version" in json_schema_extra:
                version = json_schema_extra["version"]
                if isinstance(version, str):
                    return version
        # Also check if it's a callable that returns a dict
        elif callable(getattr(config, "json_schema_extra", None)):  # type: ignore[attr-defined]
            try:
                extra = config.json_schema_extra({})  # type: ignore[attr-defined]
                if isinstance(extra, dict) and "version" in extra:
                    version = extra["version"]
                    if isinstance(version, str):
                        return version
            except Exception:
                pass

    return None


def model_to_schema(
    model: Type[BaseModel],
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    processed_models: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Convert a Pydantic model to JSON Schema.

    Handles:
    - Field types and constraints
    - Field validators (pre and post)
    - Nested models
    - Default values
    - Required fields
    - Version information

    Args:
        model: Pydantic model class to convert
        title: Optional title for the schema
        description: Optional description for the schema
        version: Optional version string (if not provided, extracted from model)
        processed_models: Set of already processed model names (to avoid cycles)

    Returns:
        JSON Schema dictionary with version included if available

    Example:
        >>> from pydantic import BaseModel, Field
        >>> class Person(BaseModel):
        ...     __version__ = "1.0.0"
        ...     name: str = Field(..., min_length=3)
        ...     age: int = Field(ge=0, le=120)
        >>> schema = model_to_schema(Person)
        >>> schema["version"]
        "1.0.0"
        >>> schema["properties"]["name"]["minLength"]
        3
    """
    if processed_models is None:
        processed_models = set()

    model_name = model.__name__
    if model_name in processed_models:
        # Return a reference to avoid infinite recursion
        return {"type": "object", "$ref": f"#/definitions/{model_name}"}

    processed_models.add(model_name)

    schema: Dict[str, Any] = {
        "type": "object",
    }

    if title:
        schema["title"] = title
    elif model_name:
        schema["title"] = model_name

    if description:
        schema["description"] = description
    elif model.__doc__:
        schema["description"] = model.__doc__.strip()

    # Extract version from model if not provided
    if version is None:
        version = _extract_version_from_model(model)

    if version:
        schema["version"] = version

    # Extract validators
    validators = _extract_validators_from_model(model)

    # Get model's JSON schema first (Pydantic v2 has this built-in)
    # This gives us the most accurate schema with all constraints
    try:
        pydantic_schema = model.model_json_schema()
        # Use Pydantic's schema as base, but we'll enhance it with our custom validators
        if "properties" in pydantic_schema:
            properties = pydantic_schema["properties"].copy()
        else:
            properties = {}
        required = pydantic_schema.get("required", [])

        # Process nested models in the schema
        # Pydantic's schema may have $defs for nested models
        # We need to inline them instead of using $ref for simplicity
        if "$defs" in pydantic_schema:
            defs = pydantic_schema["$defs"]

            # Replace $ref references with actual schemas
            def resolve_refs(obj: Any) -> Any:
                if isinstance(obj, dict):
                    if "$ref" in obj:
                        ref_path = obj["$ref"]
                        if ref_path.startswith("#/$defs/"):
                            def_name = ref_path.replace("#/$defs/", "")
                            if def_name in defs:
                                return resolve_refs(defs[def_name])
                    return {k: resolve_refs(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [resolve_refs(item) for item in obj]
                return obj

            properties = resolve_refs(properties)

    except (AttributeError, TypeError):
        # Fallback for Pydantic v1 or if method doesn't exist
        properties = {}
        required = []
        # Use model_fields (Pydantic v2) or __fields__ (Pydantic v1)
        if hasattr(model, "model_fields"):
            fields: Any = model.model_fields  # type: ignore[assignment]
        elif hasattr(model, "__fields__"):
            fields = model.__fields__  # type: ignore[assignment]
        else:
            fields = {}

        for field_name, field_info in fields.items():
            field_schema: Dict[str, Any] = {}

            # Get field type
            if hasattr(field_info, "annotation"):
                field_type = field_info.annotation
            elif hasattr(field_info, "type_"):
                field_type = field_info.type_
            else:
                field_type = str  # Default

            # Process field type
            type_schema = _process_field_type(field_type, model, processed_models)  # type: ignore[arg-type]
            field_schema.update(type_schema)

            # Extract constraints from Field
            if isinstance(field_info, FieldInfo):
                constraints = _extract_field_constraints(field_info)
                field_schema.update(constraints)

            properties[field_name] = field_schema

    # Now enhance with custom validators (coercion/validations)
    for field_name in properties:
        field_schema = properties[field_name]

        # Add validators (coercion and validations)
        if field_name in validators:
            validator_info = validators[field_name]
            if validator_info.get("coercion"):
                field_schema["coercion"] = validator_info["coercion"]
            if validator_info.get("validations"):
                field_schema["validations"] = validator_info["validations"]

        properties[field_name] = field_schema

    schema["properties"] = properties

    if required:
        schema["required"] = required

    # Normalize anyOf patterns to type arrays for better readability
    schema = _normalize_anyof_to_type_list(schema)

    return schema
