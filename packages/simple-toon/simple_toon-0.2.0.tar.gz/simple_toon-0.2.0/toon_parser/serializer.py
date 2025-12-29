"""JSON to TOON serializer implementation."""

from typing import Any, Dict, List


class ToonSerializeError(Exception):
    """Exception raised for TOON serialization errors."""

    pass


def stringify(obj: Any, indent: int = 0) -> str:
    """
    Serialize Python object (JSON-compatible) to TOON format string.

    Args:
        obj: Python object to serialize (dict, list, or primitive)
        indent: Current indentation level (for internal use)

    Returns:
        TOON formatted string

    Raises:
        ToonSerializeError: If object cannot be serialized to TOON
    """
    if obj is None:
        return "null"

    if isinstance(obj, bool):
        return "true" if obj else "false"

    if isinstance(obj, (int, float)):
        return str(obj)

    if isinstance(obj, str):
        return _quote_if_needed(obj)

    if isinstance(obj, dict):
        return _stringify_dict(obj, indent)

    if isinstance(obj, list):
        return _stringify_list(obj, indent)

    raise ToonSerializeError(f"Cannot serialize type {type(obj).__name__} to TOON")


def _stringify_dict(obj: Dict[str, Any], indent: int) -> str:
    """
    Serialize a dictionary to TOON format.

    For dicts containing uniform arrays, use tabular format.
    """
    lines = []
    indent_str = "  " * indent

    for key, value in obj.items():
        if isinstance(value, list) and value and _is_uniform_array(value):
            # Use tabular format for uniform arrays
            fields = _extract_fields(value)
            count = len(value)

            # Header line: arrayName[N]{field1,field2}:
            header = f"{indent_str}{key}[{count}]{{{','.join(fields)}}}:"
            lines.append(header)

            # Data rows
            for item in value:
                row_values = [_format_value(item.get(field)) for field in fields]
                row = f"{indent_str}  {','.join(row_values)}"
                lines.append(row)

        elif isinstance(value, list):
            # Non-uniform list - could be improved
            raise ToonSerializeError(
                f"Non-uniform arrays are not yet supported in TOON format (key: '{key}')"
            )
        elif isinstance(value, dict):
            # Nested object
            nested = _stringify_dict(value, indent + 1)
            lines.append(f"{indent_str}{key}:")
            lines.append(nested)
        else:
            # Simple key-value pair
            formatted_value = _format_value(value)
            lines.append(f"{indent_str}{key}: {formatted_value}")

    return "\n".join(lines)


def _stringify_list(obj: List[Any], indent: int) -> str:
    """
    Serialize a list to TOON format.

    Note: Top-level lists are not well-defined in TOON spec.
    They should typically be wrapped in an object.
    """
    if _is_uniform_array(obj):
        raise ToonSerializeError(
            "Top-level uniform arrays should be wrapped in an object with a key"
        )

    # Handle as a simple list (non-standard TOON)
    indent_str = "  " * indent
    lines = []
    for item in obj:
        if isinstance(item, (dict, list)):
            serialized = stringify(item, indent + 1)
            lines.append(f"{indent_str}- {serialized}")
        else:
            lines.append(f"{indent_str}- {_format_value(item)}")

    return "\n".join(lines)


def _is_uniform_array(arr: List[Any]) -> bool:
    """
    Check if an array is uniform (all items are dicts with same keys).

    Args:
        arr: List to check

    Returns:
        True if array is uniform, False otherwise
    """
    if not arr:
        return False

    if not all(isinstance(item, dict) for item in arr):
        return False

    # Check if all dicts have the same keys
    first_keys = set(arr[0].keys())
    return all(set(item.keys()) == first_keys for item in arr)


def _extract_fields(arr: List[Dict[str, Any]]) -> List[str]:
    """
    Extract field names from a uniform array (order preserved from first item).

    Args:
        arr: Uniform array of dictionaries

    Returns:
        List of field names in consistent order
    """
    if not arr:
        return []

    # Use the first item to determine field order
    return list(arr[0].keys())


def _format_value(value: Any) -> str:
    """
    Format a single value for TOON output.

    Quotes strings if they contain special characters.
    """
    if value is None:
        return "null"

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        return _quote_if_needed(value)

    raise ToonSerializeError(f"Cannot format value of type {type(value).__name__}")


def _quote_if_needed(s: str) -> str:
    """
    Quote a string if it contains special characters.

    Strings with commas, quotes, colons, or leading/trailing whitespace must be quoted.
    """
    if not s:
        return '""'

    # Check if quoting is needed
    needs_quotes = (
        "," in s
        or '"' in s
        or ":" in s
        or " " in s
        or s != s.strip()
        or s.lower() in ("true", "false", "null")
        or _is_numeric(s)
    )

    if needs_quotes:
        # Escape internal quotes
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    return s


def _is_numeric(s: str) -> bool:
    """Check if string looks like a number."""
    try:
        float(s)
        return True
    except ValueError:
        return False
