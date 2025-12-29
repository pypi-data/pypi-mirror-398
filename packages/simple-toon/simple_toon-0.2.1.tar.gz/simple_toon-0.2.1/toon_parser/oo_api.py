"""Object-oriented API for TOON parser.

This module provides a class-based interface as an alternative to the
functional API. Both APIs are fully supported and can be used interchangeably.

Why both?
- Functional API: Simple, stateless, easy for one-off conversions
- OO API: Stateful, configurable, better for repeated operations
"""

from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from pathlib import Path

from .parser import parse as _parse
from .serializer import stringify as _stringify
from .advanced import (
    parse_advanced as _parse_advanced,
    stringify_advanced as _stringify_advanced,
    stream_parse as _stream_parse,
    ToonConfig,
)
from .schema import Schema, ValidationError
from .io import read_toon, write_toon


class ToonParser:
    """
    Object-oriented TOON parser.

    Example:
        ```python
        parser = ToonParser(advanced=True, config=ToonConfig(separator="_"))

        # Parse strings
        data = parser.parse(toon_string)

        # Parse files
        data = parser.parse_file("input.toon")

        # Streaming parse
        for array_name, items in parser.stream(toon_string):
            process(array_name, items)
        ```
    """

    def __init__(
        self,
        advanced: bool = False,
        config: Optional[ToonConfig] = None,
        schema: Optional[Schema] = None,
    ):
        """
        Initialize parser with configuration.

        Args:
            advanced: Use advanced parser (nested objects, multiple arrays)
            config: TOON configuration
            schema: Optional schema for validation
        """
        self.advanced = advanced
        self.config = config or ToonConfig()
        self.schema = schema

    def parse(self, toon: str) -> Any:
        """
        Parse TOON string to Python object.

        Args:
            toon: TOON formatted string

        Returns:
            Parsed data

        Raises:
            ValidationError: If schema validation fails
        """
        if self.advanced:
            data = _parse_advanced(toon, self.config)
        else:
            data = _parse(toon)

        if self.schema:
            self.schema.validate(data)

        return data

    def parse_file(self, file_path: Union[str, Path]) -> Any:
        """
        Parse TOON file.

        Args:
            file_path: Path to TOON file

        Returns:
            Parsed data
        """
        return read_toon(file_path, advanced=self.advanced, config=self.config, schema=self.schema)

    def stream(self, toon: str) -> Iterator[Tuple[str, List[Dict[str, Any]]]]:
        """
        Stream parse TOON data (memory efficient).

        Args:
            toon: TOON formatted string

        Yields:
            Tuples of (array_name, items)
        """
        return _stream_parse(toon, self.config)

    def set_schema(self, schema: Schema) -> None:
        """Set validation schema."""
        self.schema = schema

    def clear_schema(self) -> None:
        """Clear validation schema."""
        self.schema = None


class ToonSerializer:
    """
    Object-oriented TOON serializer.

    Example:
        ```python
        serializer = ToonSerializer(advanced=True, config=ToonConfig(indent_size=4))

        # Serialize to string
        toon = serializer.stringify(data)

        # Serialize to file
        serializer.stringify_to_file(data, "output.toon")
        ```
    """

    def __init__(
        self,
        advanced: bool = False,
        config: Optional[ToonConfig] = None,
        schema: Optional[Schema] = None,
    ):
        """
        Initialize serializer with configuration.

        Args:
            advanced: Use advanced serializer (nested objects)
            config: TOON configuration
            schema: Optional schema for validation
        """
        self.advanced = advanced
        self.config = config or ToonConfig()
        self.schema = schema

    def stringify(self, data: Any) -> str:
        """
        Serialize Python object to TOON string.

        Args:
            data: Data to serialize

        Returns:
            TOON formatted string

        Raises:
            ValidationError: If schema validation fails
        """
        if self.schema:
            self.schema.validate(data)

        if self.advanced:
            return _stringify_advanced(data, self.config)
        else:
            return _stringify(data)

    def stringify_to_file(
        self,
        data: Any,
        file_path: Union[str, Path],
        overwrite: bool = True,
    ) -> None:
        """
        Serialize data to TOON file.

        Args:
            data: Data to serialize
            file_path: Output file path
            overwrite: Whether to overwrite existing file
        """
        write_toon(
            data,
            file_path,
            advanced=self.advanced,
            config=self.config,
            schema=self.schema,
            overwrite=overwrite,
        )

    def set_schema(self, schema: Schema) -> None:
        """Set validation schema."""
        self.schema = schema

    def clear_schema(self) -> None:
        """Clear validation schema."""
        self.schema = None


class ToonDocument:
    """
    Represents a parsed TOON document with helper methods.

    This provides a more object-oriented way to work with TOON data,
    with methods for accessing, querying, and manipulating the data.

    Example:
        ```python
        doc = ToonDocument.from_file("data.toon")

        # Access arrays
        users = doc.get_array("users")
        print(f"Found {len(users)} users")

        # Query data
        active_users = doc.query("users", lambda u: u["active"] == True)

        # Add data
        doc.add_item("users", {"id": 99, "name": "New User"})

        # Save back
        doc.save("output.toon")
        ```
    """

    def __init__(self, data: Dict[str, List[Dict[str, Any]]], config: Optional[ToonConfig] = None):
        """
        Initialize document with data.

        Args:
            data: Dictionary of array name -> items
            config: TOON configuration
        """
        self.data = data
        self.config = config or ToonConfig()
        self._schemas: Dict[str, Schema] = {}

    @classmethod
    def from_string(cls, toon: str, config: Optional[ToonConfig] = None) -> "ToonDocument":
        """
        Create document from TOON string.

        Args:
            toon: TOON formatted string
            config: TOON configuration

        Returns:
            ToonDocument instance
        """
        config = config or ToonConfig()
        data = _parse_advanced(toon, config)
        return cls(data, config)

    @classmethod
    def from_file(cls, file_path: Union[str, Path], config: Optional[ToonConfig] = None) -> "ToonDocument":
        """
        Create document from TOON file.

        Args:
            file_path: Path to TOON file
            config: TOON configuration

        Returns:
            ToonDocument instance
        """
        config = config or ToonConfig()
        data = read_toon(file_path, advanced=True, config=config)
        return cls(data, config)

    def get_array(self, array_name: str) -> List[Dict[str, Any]]:
        """
        Get array by name.

        Args:
            array_name: Name of array

        Returns:
            List of items

        Raises:
            KeyError: If array doesn't exist
        """
        if array_name not in self.data:
            raise KeyError(f"Array '{array_name}' not found")
        return self.data[array_name]

    def get_array_names(self) -> List[str]:
        """Get list of all array names."""
        return list(self.data.keys())

    def has_array(self, array_name: str) -> bool:
        """Check if array exists."""
        return array_name in self.data

    def add_array(self, array_name: str, items: List[Dict[str, Any]]) -> None:
        """
        Add new array to document.

        Args:
            array_name: Name for new array
            items: List of items
        """
        self.data[array_name] = items

    def add_item(self, array_name: str, item: Dict[str, Any]) -> None:
        """
        Add item to existing array.

        Args:
            array_name: Array to add to
            item: Item to add

        Raises:
            KeyError: If array doesn't exist
        """
        if array_name not in self.data:
            raise KeyError(f"Array '{array_name}' not found. Use add_array() to create it.")
        self.data[array_name].append(item)

    def query(self, array_name: str, predicate) -> List[Dict[str, Any]]:
        """
        Query array with predicate function.

        Args:
            array_name: Array to query
            predicate: Function that returns True for matching items

        Returns:
            List of matching items
        """
        items = self.get_array(array_name)
        return [item for item in items if predicate(item)]

    def count(self, array_name: str) -> int:
        """Get count of items in array."""
        return len(self.get_array(array_name))

    def total_items(self) -> int:
        """Get total number of items across all arrays."""
        return sum(len(items) for items in self.data.values())

    def set_schema(self, array_name: str, schema: Schema) -> None:
        """
        Set validation schema for an array.

        Args:
            array_name: Array name
            schema: Schema to apply
        """
        self._schemas[array_name] = schema

    def validate(self) -> None:
        """
        Validate all arrays with their schemas.

        Raises:
            ValidationError: If any validation fails
        """
        for array_name, schema in self._schemas.items():
            if array_name in self.data:
                schema.validate_array(self.data[array_name])

    def to_string(self) -> str:
        """
        Serialize document to TOON string.

        Returns:
            TOON formatted string
        """
        return _stringify_advanced(self.data, self.config)

    def save(self, file_path: Union[str, Path], overwrite: bool = True) -> None:
        """
        Save document to file.

        Args:
            file_path: Output file path
            overwrite: Whether to overwrite existing file
        """
        write_toon(self.data, file_path, advanced=True, config=self.config, overwrite=overwrite)

    def __repr__(self) -> str:
        """String representation."""
        arrays = ", ".join(f"{name}({len(items)})" for name, items in self.data.items())
        return f"ToonDocument({arrays})"


class ToonConverter:
    """
    Convenience class for converting between TOON and JSON.

    Example:
        ```python
        converter = ToonConverter(advanced=True)

        # Convert JSON to TOON
        converter.json_to_toon("input.json", "output.toon")

        # Convert TOON to JSON
        converter.toon_to_json("input.toon", "output.json")

        # Get conversion stats
        stats = converter.get_savings("input.json", "output.toon")
        print(f"Saved {stats['savings_percent']}%")
        ```
    """

    def __init__(self, advanced: bool = True, config: Optional[ToonConfig] = None):
        """
        Initialize converter.

        Args:
            advanced: Use advanced parser/serializer
            config: TOON configuration
        """
        self.parser = ToonParser(advanced=advanced, config=config)
        self.serializer = ToonSerializer(advanced=advanced, config=config)

    def json_to_toon(self, json_path: Union[str, Path], toon_path: Union[str, Path]) -> None:
        """Convert JSON file to TOON."""
        from .io import convert_json_to_toon
        convert_json_to_toon(json_path, toon_path, advanced=self.parser.advanced, config=self.parser.config)

    def toon_to_json(self, toon_path: Union[str, Path], json_path: Union[str, Path]) -> None:
        """Convert TOON file to JSON."""
        from .io import convert_toon_to_json
        convert_toon_to_json(toon_path, json_path, advanced=self.parser.advanced, config=self.parser.config)

    def get_savings(self, json_path: Union[str, Path], toon_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Calculate token/byte savings between JSON and TOON files.

        Returns:
            Dictionary with size comparison stats
        """
        json_path = Path(json_path)
        toon_path = Path(toon_path)

        json_size = json_path.stat().st_size
        toon_size = toon_path.stat().st_size

        savings = json_size - toon_size
        savings_percent = 100 * (savings / json_size) if json_size > 0 else 0

        return {
            "json_size_bytes": json_size,
            "toon_size_bytes": toon_size,
            "savings_bytes": savings,
            "savings_percent": round(savings_percent, 2),
        }
