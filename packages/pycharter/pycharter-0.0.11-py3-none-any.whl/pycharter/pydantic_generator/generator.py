"""
Model generator module for creating Pydantic models from JSON schemas.
"""

from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, ValidationInfo, create_model, field_validator

from pycharter.shared.coercions import get_coercion
from pycharter.shared.json_schema_support import (
    apply_json_schema_constraints,
    create_const_validator,
    create_enum_validator,
    create_pattern_validator,
    create_unique_items_validator,
)
from pycharter.shared.schema_resolver import normalize_schema_structure, resolve_refs
from pycharter.shared.validations import get_validation


def _map_json_type_to_python(
    schema: Dict[str, Any], field_name: Optional[str] = None
) -> Type[Any]:
    """
    Map JSON Schema type to Python type.

    Handles:
    - Single types: "number" -> float
    - Nullable types: ["number", "null"] -> float (Optional handled later)
    - Union types: ["string", "number"] -> Union[str, float]
    - Union + nullable: ["string", "number", "null"] -> Union[str, float]

    Args:
        schema: The schema for the field
        field_name: Optional field name for better error messages

    Returns:
        Python type corresponding to the JSON Schema type
    """
    schema_type = schema.get("type", "string")

    type_mapping: Dict[str, Type[Any]] = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    # Handle array type (union types in JSON Schema Draft 2020-12)
    if isinstance(schema_type, list):
        # Filter out "null" - nullability is handled separately via Optional
        non_null_types = [t for t in schema_type if t != "null"]

        if not non_null_types:
            # All nulls (rare edge case)
            return type(None)
        elif len(non_null_types) == 1:
            # Single non-null type (nullable case: ["number", "null"])
            schema_type = non_null_types[0]
        else:
            # Multiple non-null types (union type: ["string", "number"])
            # Map each type and create a Union
            python_types = [type_mapping.get(t, str) for t in non_null_types]
            # Remove duplicates while preserving order
            unique_types = []
            seen = set()
            for t in python_types:
                if t not in seen:
                    unique_types.append(t)
                    seen.add(t)

            if len(unique_types) == 1:
                return unique_types[0]
            else:
                # Create Union type
                return Union[tuple(unique_types)]  # type: ignore[return-value]

    # Handle single type
    if schema_type in type_mapping:
        return type_mapping[schema_type]

    # Handle null type (optional)
    if schema_type == "null":
        return type(None)

    # Default to string if type is unknown
    return str


def _get_default_value(schema: Dict[str, Any]) -> Any:
    """
    Extract default value from schema if present.

    Args:
        schema: The schema dictionary

    Returns:
        Default value or ... (Ellipsis) if no default
    """
    if "default" in schema:
        return schema["default"]
    return ...


def _create_field_definition(
    schema: Dict[str, Any], field_name: str, required: bool = True
) -> tuple[Type[Any], Any]:
    """
    Create a Pydantic field definition from a JSON schema field.

    Applies standard JSON Schema constraints (minLength, maxLength, pattern, enum, etc.)
    and handles charter extensions (coercion, validations).

    Args:
        schema: The field schema
        field_name: Name of the field
        required: Whether the field is required

    Returns:
        Tuple of (type, Field or default value)
    """
    python_type = _map_json_type_to_python(schema, field_name)
    default_value = _get_default_value(schema)

    # Handle enum - use Literal type if enum is specified
    if "enum" in schema and len(schema["enum"]) > 0:
        from typing import Literal

        enum_values = schema["enum"]
        if len(enum_values) == 1:
            python_type = Literal[enum_values[0]]  # type: ignore[assignment]
        else:
            # Create union of literals
            python_type = Literal[tuple(enum_values)]  # type: ignore[assignment]

    # Handle const - single allowed value
    if "const" in schema:
        from typing import Literal

        python_type = Literal[schema["const"]]  # type: ignore[assignment]

    # Handle optional fields
    if not required or default_value is not ...:
        python_type = Optional[python_type]  # type: ignore[assignment]
        if default_value is ...:
            default_value = None

    # Apply standard JSON Schema constraints
    field_kwargs = apply_json_schema_constraints(schema, field_name)

    if default_value is ...:
        # Required field, no default
        if field_kwargs:
            return (python_type, Field(**field_kwargs))
        return (python_type, ...)
    else:
        # Has default value
        if field_kwargs:
            return (python_type, Field(default=default_value, **field_kwargs))
        return (python_type, default_value)


def _process_array_schema(schema: Dict[str, Any], model_name: str) -> Type[Any]:
    """
    Process an array schema, handling nested objects.

    Args:
        schema: The array schema
        model_name: Base name for generating nested model names

    Returns:
        Python type for the array (List[item_type])
    """
    items_schema = schema.get("items", {})

    if isinstance(items_schema, dict) and items_schema.get("type") == "object":
        # Nested object in array - create a model for it
        item_model = schema_to_model(items_schema, f"{model_name}Item")
        return List[item_model]  # type: ignore[valid-type]

    # Simple array type
    item_type = _map_json_type_to_python(items_schema)
    return List[item_type]  # type: ignore[valid-type]


def schema_to_model(
    schema: Dict[str, Any], model_name: str = "DynamicModel"
) -> Type[BaseModel]:
    """
    Convert a JSON schema to a Pydantic model.

    Args:
        schema: The JSON schema dictionary
        model_name: Name for the generated Pydantic model class

    Returns:
        A Pydantic model class generated from the schema

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {"type": "string"},
        ...         "age": {"type": "integer"}
        ...     },
        ...     "required": ["name"]
        ... }
        >>> Model = schema_to_model(schema, "Person")
        >>> person = Model(name="Alice", age=30)
        >>> person.name
        'Alice'
    """
    from pycharter.shared.schema_parser import (
        get_schema_type,
        is_required,
        normalize_schema,
        validate_schema,
    )

    # Validate and normalize schema
    validate_schema(schema)
    schema = normalize_schema(schema)

    # Normalize structure (handle definitions/$defs, $schema, $id)
    schema = normalize_schema_structure(schema)

    # Resolve $ref references
    schema = resolve_refs(schema)

    schema_type = get_schema_type(schema)

    if schema_type != "object":
        raise ValueError(
            f"Schema must be of type 'object' to create a model. Got '{schema_type}'"
        )

    properties = schema.get("properties", {})
    if not properties:
        # Empty object schema
        return create_model(model_name)

    # Build field definitions and collect validators
    field_definitions: Dict[str, tuple[Type[Any], Any]] = {}
    coercion_validators: Dict[str, Any] = {}  # field_name -> coercion function
    validation_validators: Dict[str, List[Any]] = (
        {}
    )  # field_name -> list of validation functions

    for field_name, field_schema in properties.items():
        if not isinstance(field_schema, dict):
            continue

        required = is_required(field_name, schema)
        field_type = field_schema.get("type")

        # Extract x-validators (alternative format: array of validator objects)
        x_validators = field_schema.get("x-validators", [])
        if x_validators and isinstance(x_validators, list):
            for validator_spec in x_validators:
                if isinstance(validator_spec, dict):
                    validator_name = validator_spec.get("name")
                    is_pre = validator_spec.get("pre", False)
                    params = validator_spec.get("params", {})

                    if is_pre:
                        # Pre-validation (coercion)
                        try:
                            coercion_func = get_coercion(validator_name)  # type: ignore[arg-type]
                            coercion_validators[field_name] = coercion_func
                        except ValueError as e:
                            import warnings

                            warnings.warn(
                                f"Unknown coercion '{validator_name}' for field '{field_name}': {e}"
                            )
                    else:
                        # Post-validation
                        # Handle special cases first (not in registry)
                        if validator_name == "matches_regex":
                            # Handle regex pattern validation
                            pattern = params.get("pattern", "")
                            if pattern:
                                validation_func = create_pattern_validator(pattern)
                                if field_name not in validation_validators:
                                    validation_validators[field_name] = []
                                validation_validators[field_name].append(
                                    validation_func
                                )
                            continue

                        try:
                            validation_factory = get_validation(validator_name)  # type: ignore[arg-type]
                            # Create validation function with params
                            if validator_name in ["min_length", "max_length"]:
                                threshold = params.get(
                                    "threshold", params.get("value", 0)
                                )
                                validation_func = validation_factory(threshold)
                            elif validator_name == "only_allow":
                                allowed_values = params.get(
                                    "allowed_values", params.get("value", [])
                                )
                                validation_func = validation_factory(allowed_values)
                            elif validator_name in [
                                "greater_than_or_equal_to",
                                "less_than_or_equal_to",
                            ]:
                                threshold = params.get(
                                    "threshold", params.get("value", 0)
                                )
                                validation_func = validation_factory(threshold)
                            elif validator_name == "is_positive":
                                # Handle is_positive with optional threshold
                                threshold = params.get("threshold", 0)
                                validation_func = validation_factory(threshold)
                            else:
                                # For validations that don't need config (like non_empty_string, no_capital_characters, is_email, is_url)
                                # Call factory with no args
                                validation_func = validation_factory()

                            if field_name not in validation_validators:
                                validation_validators[field_name] = []
                            validation_validators[field_name].append(validation_func)
                        except ValueError as e:
                            import warnings

                            warnings.warn(
                                f"Unknown validation '{validator_name}' for field '{field_name}': {e}"
                            )

        # Extract coercion if present (charter extension - original format)
        coercion_name = field_schema.get("coercion")
        if coercion_name:
            try:
                coercion_func = get_coercion(coercion_name)
                coercion_validators[field_name] = coercion_func
            except ValueError as e:
                # Log warning but continue - don't fail on unknown coercion
                import warnings

                warnings.warn(
                    f"Unknown coercion '{coercion_name}' for field '{field_name}': {e}"
                )

        # Handle standard JSON Schema enum constraint
        if "enum" in field_schema and len(field_schema["enum"]) > 0:
            enum_validator = create_enum_validator(field_schema["enum"])
            if field_name not in validation_validators:
                validation_validators[field_name] = []
            validation_validators[field_name].append(enum_validator)

        # Handle standard JSON Schema const constraint
        if "const" in field_schema:
            const_validator = create_const_validator(field_schema["const"])
            if field_name not in validation_validators:
                validation_validators[field_name] = []
            validation_validators[field_name].append(const_validator)

        # Handle standard JSON Schema pattern constraint
        if "pattern" in field_schema:
            pattern_validator = create_pattern_validator(field_schema["pattern"])
            if field_name not in validation_validators:
                validation_validators[field_name] = []
            validation_validators[field_name].append(pattern_validator)

        # Handle standard JSON Schema uniqueItems constraint
        if field_type == "array" and field_schema.get("uniqueItems") is True:
            if field_name not in validation_validators:
                validation_validators[field_name] = []
            validation_validators[field_name].append(create_unique_items_validator)

        # Extract charter validations if present (extension)
        validations = field_schema.get("validations", {})
        if validations and isinstance(validations, dict):
            if field_name not in validation_validators:
                validation_validators[field_name] = []
            for validation_name, validation_config in validations.items():
                # Handle special cases first
                if validation_name == "matches_regex":
                    # Handle regex pattern validation
                    if isinstance(validation_config, dict):
                        pattern = validation_config.get("pattern", "")
                    else:
                        pattern = str(validation_config) if validation_config else ""
                    if pattern:
                        validation_func = create_pattern_validator(pattern)
                        validation_validators[field_name].append(validation_func)
                    continue

                try:
                    validation_factory = get_validation(validation_name)
                    # Handle None/null config
                    if validation_config is None:
                        validation_config = {}
                    elif not isinstance(validation_config, dict):
                        # If config is not a dict, wrap it appropriately
                        validation_config = {"value": validation_config}

                    # Create validation function with config
                    # All validations are factory functions that return a validator
                    if validation_name in ["min_length", "max_length"]:
                        threshold = validation_config.get(
                            "threshold", validation_config.get("value", 0)
                        )
                        validation_func = validation_factory(threshold)
                    elif validation_name == "only_allow":
                        allowed_values = validation_config.get(
                            "allowed_values", validation_config.get("value", [])
                        )
                        validation_func = validation_factory(allowed_values)
                    elif validation_name in [
                        "greater_than_or_equal_to",
                        "less_than_or_equal_to",
                        "is_positive",
                    ]:
                        threshold = validation_config.get(
                            "threshold", validation_config.get("value", 0)
                        )
                        validation_func = validation_factory(threshold)
                    elif validation_name == "matches_regex":
                        # This should be handled above, but just in case
                        pattern = validation_config.get("pattern", "")
                        validation_func = validation_factory(pattern)
                    else:
                        # For validations that don't need config (like non_empty_string, no_capital_characters, is_email, is_url)
                        # Call factory with no args
                        validation_func = validation_factory()

                    validation_validators[field_name].append(validation_func)
                except ValueError as e:
                    import warnings

                    warnings.warn(
                        f"Unknown validation '{validation_name}' for field '{field_name}': {e}"
                    )

        # Handle array types with nested objects
        if field_type == "array":
            array_type = _process_array_schema(
                field_schema, f"{model_name}{field_name.capitalize()}"
            )
            default_value = _get_default_value(field_schema)

            # Apply JSON Schema constraints for arrays (minItems, maxItems, uniqueItems)
            field_kwargs = apply_json_schema_constraints(field_schema, field_name)

            if not required or default_value is not ...:
                array_type = Optional[array_type]  # type: ignore[assignment]
                if default_value is ...:
                    default_value = []

            # Create field with constraints
            if field_kwargs:
                field_definitions[field_name] = (
                    array_type,
                    Field(
                        default=default_value if default_value is not ... else ...,
                        **field_kwargs,
                    ),
                )
            else:
                field_definitions[field_name] = (
                    array_type,
                    default_value if default_value is not ... else ...,
                )
        elif field_type == "object":
            # Nested object - recursively create a model
            nested_model = schema_to_model(
                field_schema, f"{model_name}{field_name.capitalize()}"
            )
            field_definitions[field_name] = _create_field_definition(
                {"type": "object"}, field_name, required
            )
            # Replace with the nested model type
            field_type_tuple = field_definitions[field_name]
            field_definitions[field_name] = (  # type: ignore[assignment]
                Optional[nested_model] if not required else nested_model,
                field_type_tuple[1],
            )
        else:
            # Simple field
            field_definitions[field_name] = _create_field_definition(
                field_schema, field_name, required
            )

    # Build class dictionary with validators
    class_dict = {}

    # Add coercion validators (mode='before')
    for field_name, coercion_func in coercion_validators.items():
        # Use a factory function to properly capture closure
        def make_coercion_validator(field: str, func: Any):
            @field_validator(field, mode="before")  # type: ignore[misc]
            @classmethod  # type: ignore[misc]
            def _coerce_field(cls, value: Any) -> Any:
                if value is None:
                    return value
                return func(value)

            return _coerce_field

        class_dict[f"_coerce_{field_name}"] = make_coercion_validator(
            field_name, coercion_func
        )

    # Add validation validators (mode='after')
    for field_name, validation_funcs in validation_validators.items():
        for idx, validation_func in enumerate(validation_funcs):
            # Use a factory function to properly capture closure
            def make_validation_validator(field: str, func: Any):
                @field_validator(field, mode="after")  # type: ignore[misc]
                @classmethod  # type: ignore[misc]
                def _validate_field(cls, value: Any, info: ValidationInfo) -> Any:
                    return func(value, info)

                return _validate_field

            class_dict[f"_validate_{field_name}_{idx}"] = make_validation_validator(
                field_name, validation_func
            )

    # Create the model with validators
    if class_dict:
        # Create base model first, then subclass with validators
        base_model = create_model(model_name, **field_definitions)  # type: ignore[call-overload]
        return type(model_name, (base_model,), class_dict)
    else:
        # No validators, just create the model
        return create_model(model_name, **field_definitions)  # type: ignore[call-overload]


def generate_model(
    schema: Dict[str, Any], model_name: str = "DynamicModel"
) -> Type[BaseModel]:
    """
    Generate a Pydantic model from a JSON Schema.

    This is an alias for schema_to_model for consistency with the service API.

    Args:
        schema: The JSON schema dictionary
        model_name: Name for the generated Pydantic model class

    Returns:
        A Pydantic model class
    """
    return schema_to_model(schema, model_name)


def generate_model_file(
    schema: Dict[str, Any],
    output_path: str,
    model_name: str = "DynamicModel",
    imports: Optional[List[str]] = None,
) -> None:
    """
    Generate a Python file containing a Pydantic model from a JSON Schema.

    Args:
        schema: The JSON schema dictionary
        output_path: Path to the output Python file
        model_name: Name for the generated Pydantic model class
        imports: Optional list of additional import statements

    Example:
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> generate_model_file(schema, "person_model.py", "Person")
    """
    from pathlib import Path

    # Generate the model
    model = generate_model(schema, model_name)

    # Get model fields and their types
    fields: Any = {}
    if hasattr(model, "model_fields"):
        fields = model.model_fields  # type: ignore[assignment]
    elif hasattr(model, "__fields__"):
        fields = model.__fields__  # type: ignore[assignment]

    # Build Python code
    lines = [
        '"""',
        f"Generated Pydantic model: {model_name}",
        f"Generated from JSON Schema",
        '"""',
        "",
        "from pydantic import BaseModel, Field",
        "from typing import Optional, List, Dict, Any",
    ]

    if imports:
        lines.extend(imports)

    lines.extend(
        [
            "",
            f"class {model_name}(BaseModel):",
            '    """',
            f"    {model_name} model generated from JSON Schema",
            '    """',
        ]
    )

    # Add field definitions
    for field_name, field_info in fields.items():
        # Get field type annotation
        if hasattr(field_info, "annotation"):
            field_type = field_info.annotation
        elif hasattr(field_info, "type_"):
            field_type = field_info.type_
        else:
            field_type = Any

        # Convert type to string representation
        type_str = str(field_type).replace("typing.", "")

        # Check if optional
        is_optional = "Optional" in type_str or "None" in str(field_type)

        # Get default value
        default = "..."
        if hasattr(field_info, "default"):
            default_val = field_info.default
            if default_val is not ...:
                if default_val is None:
                    default = "None"
                elif isinstance(default_val, str):
                    default = f'"{default_val}"'
                else:
                    default = str(default_val)

        # Build field definition
        if default == "...":
            lines.append(f"    {field_name}: {type_str}")
        else:
            lines.append(f"    {field_name}: {type_str} = {default}")

    lines.append("")

    # Write to file
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
