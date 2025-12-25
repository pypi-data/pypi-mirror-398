"""
Reverse converter module providing a clean API for Pydantic model to JSON Schema conversion.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Type

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel

from pycharter.json_schema_converter.converter import model_to_schema


def to_dict(
    model: Type[BaseModel],
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert a Pydantic model to a JSON Schema dictionary.

    Args:
        model: The Pydantic model class to convert
        title: Optional title for the schema
        description: Optional description for the schema
        version: Optional version string (if not provided, extracted from model)

    Returns:
        JSON Schema as a dictionary with version included if available

    Example:
        >>> from pydantic import BaseModel, Field
        >>> class Person(BaseModel):
        ...     __version__ = "1.0.0"
        ...     name: str = Field(..., min_length=3)
        ...     age: int = Field(ge=0)
        >>> schema = to_dict(Person)
        >>> schema["version"]
        "1.0.0"
        >>> schema["properties"]["name"]["minLength"]
        3
    """
    return model_to_schema(model, title=title, description=description, version=version)


def to_json(
    model: Type[BaseModel],
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    indent: int = 2,
) -> str:
    """
    Convert a Pydantic model to a JSON Schema string.

    Args:
        model: The Pydantic model class to convert
        title: Optional title for the schema
        description: Optional description for the schema
        version: Optional version string (if not provided, extracted from model)
        indent: JSON indentation level

    Returns:
        JSON Schema as a JSON string

    Example:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     __version__ = "1.0.0"
        ...     name: str
        >>> schema_json = to_json(User)
        >>> print(schema_json)
    """
    schema = model_to_schema(
        model, title=title, description=description, version=version
    )
    return json.dumps(schema, indent=indent)


def to_file(
    model: Type[BaseModel],
    file_path: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    indent: int = 2,
) -> None:
    """
    Convert a Pydantic model to a JSON Schema file.

    Supports both JSON (.json) and YAML (.yaml, .yml) output formats.
    Format is automatically determined by file extension.

    Args:
        model: The Pydantic model class to convert
        file_path: Path to the output file (JSON or YAML)
        title: Optional title for the schema
        description: Optional description for the schema
        version: Optional version string (if not provided, extracted from model)
        indent: JSON indentation level (ignored for YAML)

    Example:
        >>> from pydantic import BaseModel
        >>> class Product(BaseModel):
        ...     __version__ = "1.0.0"
        ...     name: str
        ...     price: float
        >>> to_file(Product, "product_schema.json")  # JSON output
        >>> to_file(Product, "product_schema.yaml")  # YAML output
    """
    schema = model_to_schema(
        model, title=title, description=description, version=version
    )
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Determine output format
    suffix = path.suffix.lower()

    if suffix in [".yaml", ".yml"]:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True
            )
    elif suffix == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=indent)
    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. Supported formats: .json, .yaml, .yml"
        )
