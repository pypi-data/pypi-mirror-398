"""TOON to JSON parser implementation."""

import re
from typing import Any, List, Tuple


class ToonParseError(Exception):
    """Exception raised for TOON parsing errors."""

    pass


def parse(toon: str) -> Any:
    """
    Parse TOON format string to Python object (JSON-compatible).

    Args:
        toon: TOON formatted string

    Returns:
        Python object (dict, list, or primitive)

    Raises:
        ToonParseError: If TOON format is invalid
    """
    if not toon or not toon.strip():
        return None

    lines = toon.strip().split("\n")

    # Parse multiple arrays at root level
    result = {}
    idx = 0
    while idx < len(lines):
        # Skip empty lines
        if not lines[idx].strip():
            idx += 1
            continue

        parsed, next_idx = _parse_lines(lines, idx, 0)

        if parsed is None:
            idx += 1
            continue

        if isinstance(parsed, dict):
            result.update(parsed)
        else:
            # Single value at root - return as-is
            return parsed

        idx = next_idx

    return result if result else None


def _parse_lines(
    lines: List[str], start_idx: int, current_indent: int
) -> Tuple[Any, int]:
    """
    Parse lines starting from start_idx with expected indentation.

    Args:
        lines: All lines to parse
        start_idx: Starting line index
        current_indent: Expected indentation level

    Returns:
        Tuple of (parsed_value, next_line_index)
    """
    if start_idx >= len(lines):
        return None, start_idx

    line = lines[start_idx]
    stripped = line.lstrip()
    indent = len(line) - len(stripped)

    # Check if this is an array header: arrayName[N]{field1,field2}:
    array_match = re.match(r"^(\w+)\[(\d+)\]\{([^}]+)\}:\s*$", stripped)

    # Check for malformed array header (missing count or brackets)
    if re.match(r"^(\w+)(\{[^}]+\}:|\[\d+\])", stripped) and not array_match:
        raise ToonParseError(f"Malformed array header: '{stripped}'. Expected format: arrayName[N]{{field1,field2}}:")

    if array_match:
        array_name = array_match.group(1)
        count = int(array_match.group(2))
        fields = [f.strip() for f in array_match.group(3).split(",")]

        # Parse data rows
        rows = []
        idx = start_idx + 1
        expected_indent = indent + 2  # TOON uses 2-space indentation

        while idx < len(lines) and len(rows) < count:
            data_line = lines[idx]
            data_stripped = data_line.lstrip()
            data_indent = len(data_line) - len(data_stripped)

            if data_indent < expected_indent or not data_stripped:
                break

            if data_indent == expected_indent:
                values = _parse_row(data_stripped, len(fields))
                if len(values) != len(fields):
                    raise ToonParseError(
                        f"Row has {len(values)} values but header defines {len(fields)} fields"
                    )
                row_obj = dict(zip(fields, values))
                rows.append(row_obj)
                idx += 1
            else:
                break

        if len(rows) != count:
            raise ToonParseError(
                f"Array '{array_name}' declares {count} items but found {len(rows)}"
            )

        # If we're at the root level, return as a dict with array name as key
        if current_indent == 0:
            return {array_name: rows}, idx

        return rows, idx

    # Simple value or object
    return _parse_value(stripped), start_idx + 1


def _parse_row(row: str, expected_fields: int) -> List[Any]:
    """
    Parse a comma-separated row of values, handling quoted strings.

    Args:
        row: Raw row string (e.g., '1,Alice,true')
        expected_fields: Number of fields expected

    Returns:
        List of parsed values
    """
    values = []
    current = ""
    in_quotes = False
    was_quoted = False
    escape_next = False

    for char in row:
        if escape_next:
            current += char
            escape_next = False
            continue

        if char == "\\" and in_quotes:
            escape_next = True
            continue

        if char == '"':
            in_quotes = not in_quotes
            was_quoted = True
            continue

        if char == "," and not in_quotes:
            # If value was quoted, keep it as string
            if was_quoted:
                values.append(current)
            else:
                values.append(_parse_value(current.strip()))
            current = ""
            was_quoted = False
            continue

        current += char

    # Add the last value
    if was_quoted:
        values.append(current)
    elif current or len(values) < expected_fields:
        values.append(_parse_value(current.strip()))

    return values


def _parse_value(value: str) -> Any:
    """
    Parse a single value, inferring type from string representation.

    Args:
        value: String representation of value

    Returns:
        Parsed value (str, int, float, bool, or None)
    """
    if not value:
        return ""

    # Check for null
    if value.lower() == "null":
        return None

    # Check for boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Try to parse as number
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # Return as string
    return value
