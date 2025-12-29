"""File I/O utilities for TOON format."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .parser import parse
from .serializer import stringify
from .advanced import parse_advanced, stringify_advanced, ToonConfig
from .schema import Schema, MultiSchema, ValidationError


class ToonFileError(Exception):
    """Exception raised for TOON file I/O errors."""

    pass


def read_toon(
    file_path: Union[str, Path],
    advanced: bool = False,
    config: Optional[ToonConfig] = None,
    schema: Optional[Union[Schema, MultiSchema]] = None,
) -> Any:
    """
    Read and parse a TOON file.

    Args:
        file_path: Path to TOON file
        advanced: Use advanced parser (for nested objects, multiple arrays)
        config: TOON configuration (only used with advanced=True)
        schema: Optional schema for validation

    Returns:
        Parsed data

    Raises:
        ToonFileError: If file cannot be read
        ValidationError: If schema validation fails
    """
    path = Path(file_path)

    if not path.exists():
        raise ToonFileError(f"File not found: {file_path}")

    if not path.is_file():
        raise ToonFileError(f"Not a file: {file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise ToonFileError(f"Failed to read file {file_path}: {str(e)}")

    try:
        if advanced:
            data = parse_advanced(content, config)
        else:
            data = parse(content)
    except Exception as e:
        raise ToonFileError(f"Failed to parse TOON file {file_path}: {str(e)}")

    # Validate if schema provided
    if schema is not None:
        try:
            schema.validate(data)
        except ValidationError as e:
            raise ValidationError(f"Schema validation failed for {file_path}: {str(e)}")

    return data


def write_toon(
    data: Any,
    file_path: Union[str, Path],
    advanced: bool = False,
    config: Optional[ToonConfig] = None,
    schema: Optional[Union[Schema, MultiSchema]] = None,
    overwrite: bool = True,
) -> None:
    """
    Write data to a TOON file.

    Args:
        data: Data to write
        file_path: Path to output file
        advanced: Use advanced serializer (for nested objects)
        config: TOON configuration (only used with advanced=True)
        schema: Optional schema for validation before writing
        overwrite: If False, raise error if file exists

    Raises:
        ToonFileError: If file cannot be written
        ValidationError: If schema validation fails
    """
    path = Path(file_path)

    # Check if file exists
    if path.exists() and not overwrite:
        raise ToonFileError(f"File already exists: {file_path}")

    # Validate if schema provided
    if schema is not None:
        try:
            schema.validate(data)
        except ValidationError as e:
            raise ValidationError(f"Schema validation failed: {str(e)}")

    # Serialize to TOON
    try:
        if advanced:
            content = stringify_advanced(data, config)
        else:
            content = stringify(data)
    except Exception as e:
        raise ToonFileError(f"Failed to serialize data: {str(e)}")

    # Write to file
    try:
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise ToonFileError(f"Failed to write file {file_path}: {str(e)}")


def read_json(file_path: Union[str, Path]) -> Any:
    """
    Read a JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        ToonFileError: If file cannot be read
    """
    path = Path(file_path)

    if not path.exists():
        raise ToonFileError(f"File not found: {file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ToonFileError(f"Failed to read JSON file {file_path}: {str(e)}")


def write_json(
    data: Any,
    file_path: Union[str, Path],
    indent: int = 2,
    overwrite: bool = True,
) -> None:
    """
    Write data to a JSON file.

    Args:
        data: Data to write
        file_path: Path to output file
        indent: Indentation level (default: 2)
        overwrite: If False, raise error if file exists

    Raises:
        ToonFileError: If file cannot be written
    """
    path = Path(file_path)

    if path.exists() and not overwrite:
        raise ToonFileError(f"File already exists: {file_path}")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        raise ToonFileError(f"Failed to write JSON file {file_path}: {str(e)}")


def convert_json_to_toon(
    json_path: Union[str, Path],
    toon_path: Union[str, Path],
    advanced: bool = True,
    config: Optional[ToonConfig] = None,
) -> None:
    """
    Convert a JSON file to TOON format.

    Args:
        json_path: Path to input JSON file
        toon_path: Path to output TOON file
        advanced: Use advanced serializer
        config: TOON configuration

    Raises:
        ToonFileError: If conversion fails
    """
    data = read_json(json_path)
    write_toon(data, toon_path, advanced=advanced, config=config)


def convert_toon_to_json(
    toon_path: Union[str, Path],
    json_path: Union[str, Path],
    advanced: bool = True,
    config: Optional[ToonConfig] = None,
    indent: int = 2,
) -> None:
    """
    Convert a TOON file to JSON format.

    Args:
        toon_path: Path to input TOON file
        json_path: Path to output JSON file
        advanced: Use advanced parser
        config: TOON configuration
        indent: JSON indentation level

    Raises:
        ToonFileError: If conversion fails
    """
    data = read_toon(toon_path, advanced=advanced, config=config)
    write_json(data, json_path, indent=indent)


def batch_convert(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    from_format: str = "json",
    to_format: str = "toon",
    pattern: str = "*",
    advanced: bool = True,
) -> Dict[str, str]:
    """
    Batch convert files between JSON and TOON formats.

    Args:
        input_dir: Directory containing input files
        output_dir: Directory for output files
        from_format: Input format ('json' or 'toon')
        to_format: Output format ('json' or 'toon')
        pattern: Glob pattern for input files (e.g., "*.json")
        advanced: Use advanced parser/serializer

    Returns:
        Dictionary mapping input files to output files

    Raises:
        ToonFileError: If conversion fails
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise ToonFileError(f"Input directory not found: {input_dir}")

    if not input_path.is_dir():
        raise ToonFileError(f"Not a directory: {input_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    # Determine file extension for input
    if from_format == "json":
        input_ext = ".json"
    elif from_format == "toon":
        input_ext = ".toon"
    else:
        raise ToonFileError(f"Invalid from_format: {from_format}")

    # Determine file extension for output
    if to_format == "json":
        output_ext = ".json"
    elif to_format == "toon":
        output_ext = ".toon"
    else:
        raise ToonFileError(f"Invalid to_format: {to_format}")

    # Find input files
    if pattern.endswith(input_ext):
        glob_pattern = pattern
    else:
        glob_pattern = f"{pattern}{input_ext}"

    input_files = list(input_path.glob(glob_pattern))

    if not input_files:
        raise ToonFileError(f"No files matching '{glob_pattern}' found in {input_dir}")

    results = {}

    for input_file in input_files:
        # Determine output filename
        output_file = output_path / f"{input_file.stem}{output_ext}"

        try:
            if from_format == "json" and to_format == "toon":
                convert_json_to_toon(input_file, output_file, advanced=advanced)
            elif from_format == "toon" and to_format == "json":
                convert_toon_to_json(input_file, output_file, advanced=advanced)
            else:
                raise ToonFileError(f"Unsupported conversion: {from_format} to {to_format}")

            results[str(input_file)] = str(output_file)
        except Exception as e:
            raise ToonFileError(f"Failed to convert {input_file}: {str(e)}")

    return results


def get_file_stats(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get statistics about a TOON or JSON file.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file statistics

    Raises:
        ToonFileError: If file cannot be read
    """
    path = Path(file_path)

    if not path.exists():
        raise ToonFileError(f"File not found: {file_path}")

    # Get file size
    file_size = path.stat().st_size

    # Determine format and read
    if path.suffix == ".toon":
        data = read_toon(path, advanced=True)
        format_type = "toon"
    elif path.suffix == ".json":
        data = read_json(path)
        format_type = "json"
    else:
        raise ToonFileError(f"Unknown file format: {path.suffix}")

    # Collect stats
    stats = {
        "file_path": str(path),
        "format": format_type,
        "file_size_bytes": file_size,
        "arrays": {},
    }

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                stats["arrays"][key] = {
                    "count": len(value),
                    "fields": list(value[0].keys()) if value and isinstance(value[0], dict) else [],
                }

    stats["total_arrays"] = len(stats["arrays"])
    stats["total_items"] = sum(arr["count"] for arr in stats["arrays"].values())

    return stats
