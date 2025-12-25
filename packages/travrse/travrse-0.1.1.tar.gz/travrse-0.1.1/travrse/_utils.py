"""
Internal utilities for the Travrse SDK.
"""

from __future__ import annotations

import re
from typing import Any, Callable


def to_snake_case(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    # Handle consecutive uppercase letters followed by lowercase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Handle lowercase followed by uppercase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_camel_case(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def transform_keys(
    data: dict[str, Any] | list[Any] | Any,
    transform_fn: Callable[[str], str],
    preserve_keys: set[str] | None = None,
) -> dict[str, Any] | list[Any] | Any:
    """
    Recursively transform dictionary keys using the provided function.

    Args:
        data: The data to transform
        transform_fn: Function to transform each key
        preserve_keys: Set of keys whose nested structure should not be transformed
    """
    if preserve_keys is None:
        preserve_keys = {"metadata", "parameters_schema", "parametersSchema", "config"}

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            new_key = transform_fn(key)
            # Preserve certain nested structures
            if key in preserve_keys or new_key in preserve_keys:
                result[new_key] = value
            else:
                result[new_key] = transform_keys(value, transform_fn, preserve_keys)
        return result
    elif isinstance(data, list):
        return [transform_keys(item, transform_fn, preserve_keys) for item in data]
    else:
        return data


def transform_request(data: dict[str, Any] | Any) -> dict[str, Any] | Any:
    """Transform request data from Python snake_case to API snake_case."""
    # API also uses snake_case, so minimal transformation needed
    # But we handle some edge cases
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Handle special field name mappings
            if key == "from_":
                result["from"] = value
            else:
                result[key] = transform_request(value) if isinstance(value, (dict, list)) else value
        return result
    elif isinstance(data, list):
        return [transform_request(item) for item in data]
    return data


def transform_response(data: dict[str, Any] | Any) -> dict[str, Any] | Any:
    """Transform response data from API format to Python format."""
    # API uses snake_case which matches Python, minimal transformation needed
    return data


def clean_none_values(data: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from a dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def parse_sse_event(line: str) -> tuple[str | None, str | None]:
    """
    Parse a single SSE line.

    Returns:
        Tuple of (event_type, data) or (None, None) if not a data line.
    """
    line = line.strip()
    if line.startswith("data: "):
        return "data", line[6:]
    elif line.startswith("event: "):
        return "event", line[7:]
    return None, None
