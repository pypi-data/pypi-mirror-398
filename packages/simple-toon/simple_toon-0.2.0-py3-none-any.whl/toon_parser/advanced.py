"""Advanced TOON features: nested objects, streaming, and configuration."""

from typing import Any, Dict, Iterator, List, Optional, Tuple
import re


class ToonConfig:
    """Configuration for TOON serialization."""

    def __init__(
        self,
        indent_size: int = 2,
        flatten_nested: bool = True,
        max_nesting_depth: int = 5,
        separator: str = ".",
    ):
        """
        Initialize TOON configuration.

        Args:
            indent_size: Number of spaces for indentation (default: 2)
            flatten_nested: Flatten nested objects with dot notation (default: True)
            max_nesting_depth: Maximum nesting depth for objects (default: 5)
            separator: Separator for nested field names (default: ".")
        """
        self.indent_size = indent_size
        self.flatten_nested = flatten_nested
        self.max_nesting_depth = max_nesting_depth
        self.separator = separator


def flatten_object(obj: Dict[str, Any], separator: str = ".", max_depth: int = 5) -> Dict[str, Any]:
    """
    Flatten a nested object into a single-level dict with dot notation.

    Args:
        obj: Nested dictionary to flatten
        separator: Separator for nested keys (default: ".")
        max_depth: Maximum nesting depth to flatten

    Returns:
        Flattened dictionary

    Example:
        {"name": "Alice", "address": {"city": "NYC", "zip": "10001"}}
        becomes
        {"name": "Alice", "address.city": "NYC", "address.zip": "10001"}
    """

    def _flatten(current: Any, prefix: str = "", depth: int = 0) -> Dict[str, Any]:
        if depth >= max_depth or not isinstance(current, dict):
            return {prefix.rstrip(separator): current} if prefix else {"_": current}

        items: Dict[str, Any] = {}
        for key, value in current.items():
            new_key = f"{prefix}{key}"
            if isinstance(value, dict):
                items.update(_flatten(value, f"{new_key}{separator}", depth + 1))
            else:
                items[new_key] = value
        return items

    return _flatten(obj)


def unflatten_object(obj: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    Unflatten a dictionary with dot notation into nested objects.

    Args:
        obj: Flattened dictionary
        separator: Separator used in flattened keys

    Returns:
        Nested dictionary

    Example:
        {"name": "Alice", "address.city": "NYC", "address.zip": "10001"}
        becomes
        {"name": "Alice", "address": {"city": "NYC", "zip": "10001"}}
    """
    result: Dict[str, Any] = {}

    for key, value in obj.items():
        parts = key.split(separator)
        current = result

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # Conflict: key exists as both leaf and branch
                # Keep the leaf value
                continue
            current = current[part]

        # Set the final value
        current[parts[-1]] = value

    return result


def stringify_advanced(obj: Any, config: Optional[ToonConfig] = None) -> str:
    """
    Serialize Python object to TOON with advanced features.

    Args:
        obj: Python object to serialize
        config: TOON configuration options

    Returns:
        TOON formatted string with nested object support
    """
    from .serializer import ToonSerializeError, _format_value, _quote_if_needed

    if config is None:
        config = ToonConfig()

    if not isinstance(obj, dict):
        raise ToonSerializeError("Advanced stringify requires root object to be a dict")

    lines = []

    for key, value in obj.items():
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            # Flatten nested objects if enabled
            if config.flatten_nested:
                flattened_items = [
                    flatten_object(item, config.separator, config.max_nesting_depth)
                    for item in value
                ]

                # Check if all items have the same keys (uniform after flattening)
                first_keys = set(flattened_items[0].keys())
                if all(set(item.keys()) == first_keys for item in flattened_items):
                    fields = list(flattened_items[0].keys())
                    count = len(flattened_items)

                    # Header
                    header = f"{key}[{count}]{{{','.join(fields)}}}:"
                    lines.append(header)

                    # Data rows
                    for item in flattened_items:
                        row_values = [_format_value(item.get(field)) for field in fields]
                        row = f"{' ' * config.indent_size}{','.join(row_values)}"
                        lines.append(row)
                else:
                    raise ToonSerializeError(
                        f"Array '{key}' has non-uniform structure even after flattening"
                    )
            else:
                raise ToonSerializeError(
                    f"Array '{key}' contains nested objects. Enable flatten_nested or use simple objects."
                )
        elif isinstance(value, list):
            # Empty or non-dict list
            lines.append(f"{key}[{len(value)}]{{}}:")
        else:
            raise ToonSerializeError(f"Top-level values must be arrays, got {type(value).__name__}")

    return "\n".join(lines)


def parse_advanced(toon: str, config: Optional[ToonConfig] = None) -> Any:
    """
    Parse TOON format with nested object support.

    Args:
        toon: TOON formatted string
        config: TOON configuration options

    Returns:
        Python object with nested structures restored
    """
    from .parser import parse

    if config is None:
        config = ToonConfig()

    # Parse using standard parser
    result = parse(toon)

    if not isinstance(result, dict):
        return result

    # Unflatten nested objects if enabled
    if config.flatten_nested:
        for key, value in result.items():
            if isinstance(value, list):
                result[key] = [
                    unflatten_object(item, config.separator) if isinstance(item, dict) else item
                    for item in value
                ]

    return result


def stream_parse(toon: str, config: Optional[ToonConfig] = None) -> Iterator[Tuple[str, List[Dict[str, Any]]]]:
    """
    Stream parse TOON format, yielding one array at a time.

    This is memory-efficient for large TOON documents with multiple arrays.

    Args:
        toon: TOON formatted string
        config: TOON configuration options

    Yields:
        Tuples of (array_name, items) for each array in the document

    Example:
        ```
        for array_name, items in stream_parse(toon_data):
            print(f"Processing {array_name}: {len(items)} items")
            for item in items:
                process(item)
        ```
    """
    if config is None:
        config = ToonConfig()

    lines = toon.strip().split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].lstrip()
        if not line:
            i += 1
            continue

        # Check for array header
        match = re.match(r"^(\w+)\[(\d+)\]\{([^}]*)\}:\s*$", line)
        if match:
            array_name = match.group(1)
            count = int(match.group(2))
            fields_str = match.group(3)
            fields = [f.strip() for f in fields_str.split(",")] if fields_str else []

            # Parse rows
            items = []
            i += 1
            indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0

            while i < len(lines) and len(items) < count:
                data_line = lines[i]
                if not data_line.strip():
                    i += 1
                    continue

                current_indent = len(data_line) - len(data_line.lstrip())
                if current_indent < indent:
                    break

                # Parse row values
                values = _parse_row_simple(data_line.strip(), len(fields))
                if fields:
                    row_obj = dict(zip(fields, values))
                    # Unflatten if needed
                    if config.flatten_nested:
                        row_obj = unflatten_object(row_obj, config.separator)
                    items.append(row_obj)

                i += 1

            yield array_name, items
        else:
            i += 1


def _parse_row_simple(row: str, expected_count: int) -> List[Any]:
    """Simple CSV-style row parser."""
    from .parser import _parse_row
    return _parse_row(row, expected_count)
