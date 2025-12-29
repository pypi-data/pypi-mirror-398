"""Streaming serializer for memory-efficient TOON generation."""

from typing import Any, Dict, Iterator, List, Optional, TextIO, Union
from pathlib import Path
from contextlib import contextmanager

from .advanced import ToonConfig, flatten_object
from .serializer import _format_value


class StreamingSerializer:
    """
    Stream TOON output for memory-efficient serialization.

    Useful for generating large TOON files from database queries,
    APIs, or other streaming sources without loading all data into memory.

    Example:
        ```python
        with StreamingSerializer("output.toon") as writer:
            writer.begin_array("users", ["id", "name", "email"])

            for user in database.query_users():  # Streaming from DB
                writer.write_row([user.id, user.name, user.email])

            writer.end_array()
        ```
    """

    def __init__(
        self,
        output: Union[str, Path, TextIO],
        config: Optional[ToonConfig] = None,
        auto_flush: bool = True,
    ):
        """
        Initialize streaming serializer.

        Args:
            output: File path or file-like object to write to
            config: TOON configuration
            auto_flush: Flush after each row (slower but safer)
        """
        self.config = config or ToonConfig()
        self.auto_flush = auto_flush
        self._file_owned = False
        self._file: Optional[TextIO] = None
        self._current_array: Optional[str] = None
        self._current_fields: Optional[List[str]] = None
        self._row_count = 0

        # Handle file path vs file object
        if isinstance(output, (str, Path)):
            self._output_path = Path(output)
            self._file_owned = True
        else:
            self._file = output
            self._output_path = None

    def __enter__(self) -> "StreamingSerializer":
        """Context manager entry."""
        if self._file_owned and self._output_path:
            self._output_path.parent.mkdir(parents=True, exist_ok=True)
            self._file = open(self._output_path, "w", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._current_array:
            # Auto-close any open array
            self.end_array()

        if self._file_owned and self._file:
            self._file.close()

    def begin_array(
        self,
        array_name: str,
        fields: List[str],
        total_count: Optional[int] = None,
    ) -> None:
        """
        Begin writing an array.

        Args:
            array_name: Name of the array
            fields: Field names for the array
            total_count: Total number of rows (if known). If None, will be updated when array ends.

        Raises:
            RuntimeError: If another array is already open
        """
        if self._current_array:
            raise RuntimeError(f"Array '{self._current_array}' is still open. Call end_array() first.")

        if not self._file:
            raise RuntimeError("No output file opened")

        self._current_array = array_name
        self._current_fields = fields
        self._row_count = 0

        # Write header with placeholder count if not known
        indent = "  " * 0  # Root level
        count_str = str(total_count) if total_count is not None else "?"
        header = f"{indent}{array_name}[{count_str}]{{{','.join(fields)}}}:\n"

        self._file.write(header)

        if self.auto_flush:
            self._file.flush()

    def write_row(self, values: List[Any]) -> None:
        """
        Write a single row to the current array.

        Args:
            values: Values for the row (must match field count)

        Raises:
            RuntimeError: If no array is open
            ValueError: If value count doesn't match field count
        """
        if not self._current_array or not self._current_fields:
            raise RuntimeError("No array is open. Call begin_array() first.")

        if len(values) != len(self._current_fields):
            raise ValueError(
                f"Expected {len(self._current_fields)} values, got {len(values)}"
            )

        if not self._file:
            raise RuntimeError("No output file opened")

        # Format values
        formatted = [_format_value(v) for v in values]

        # Write row with indentation
        indent = "  " * 1  # Data rows are indented
        row = f"{indent}{','.join(formatted)}\n"

        self._file.write(row)
        self._row_count += 1

        if self.auto_flush:
            self._file.flush()

    def write_item(self, item: Dict[str, Any]) -> None:
        """
        Write a dictionary item to the current array.

        The item's values are extracted in the order of the fields
        defined when the array was started.

        Args:
            item: Dictionary with values for current fields

        Raises:
            RuntimeError: If no array is open
            KeyError: If item is missing required fields
        """
        if not self._current_fields:
            raise RuntimeError("No array is open. Call begin_array() first.")

        # Extract values in field order
        values = [item.get(field) for field in self._current_fields]

        self.write_row(values)

    def write_items(self, items: Iterator[Dict[str, Any]]) -> int:
        """
        Write multiple items from an iterator.

        Args:
            items: Iterator of dictionary items

        Returns:
            Number of items written
        """
        count = 0
        for item in items:
            self.write_item(item)
            count += 1
        return count

    def end_array(self) -> int:
        """
        End the current array.

        Returns:
            Number of rows written

        Raises:
            RuntimeError: If no array is open
        """
        if not self._current_array:
            raise RuntimeError("No array is currently open")

        row_count = self._row_count

        # Reset state
        self._current_array = None
        self._current_fields = None
        self._row_count = 0

        if self._file and self.auto_flush:
            self._file.flush()

        return row_count

    def write_array(
        self,
        array_name: str,
        items: Iterator[Dict[str, Any]],
        fields: Optional[List[str]] = None,
    ) -> int:
        """
        Write an entire array from an iterator in one call.

        Args:
            array_name: Name of the array
            items: Iterator of dictionary items
            fields: Field names (if None, inferred from first item)

        Returns:
            Number of items written
        """
        # Peek at first item to get fields if not provided
        items_list = list(items)  # Convert to list to peek

        if not items_list:
            # Empty array
            fields = fields or []
            self.begin_array(array_name, fields, total_count=0)
            self.end_array()
            return 0

        if fields is None:
            fields = list(items_list[0].keys())

        # Begin array with known count
        self.begin_array(array_name, fields, total_count=len(items_list))

        # Write all items
        for item in items_list:
            self.write_item(item)

        self.end_array()
        return len(items_list)


@contextmanager
def streaming_serializer(
    output: Union[str, Path, TextIO],
    config: Optional[ToonConfig] = None,
) -> Iterator[StreamingSerializer]:
    """
    Context manager for streaming TOON serialization.

    Args:
        output: Output file path or file object
        config: TOON configuration

    Yields:
        StreamingSerializer instance

    Example:
        ```python
        with streaming_serializer("output.toon") as writer:
            writer.begin_array("users", ["id", "name"])
            for user in get_users():
                writer.write_row([user.id, user.name])
            writer.end_array()
        ```
    """
    serializer = StreamingSerializer(output, config)
    with serializer as s:
        yield s


def stream_from_database(
    query_func,
    array_name: str,
    fields: List[str],
    output: Union[str, Path],
    batch_size: int = 100,
    config: Optional[ToonConfig] = None,
) -> int:
    """
    Stream data from a database query to TOON file.

    Args:
        query_func: Function that yields rows from database
        array_name: Name for the TOON array
        fields: Field names
        output: Output file path
        batch_size: Number of rows to buffer (for progress tracking)
        config: TOON configuration

    Returns:
        Total number of rows written

    Example:
        ```python
        def query():
            for row in db.execute("SELECT id, name FROM users"):
                yield {"id": row[0], "name": row[1]}

        count = stream_from_database(query, "users", ["id", "name"], "output.toon")
        ```
    """
    with streaming_serializer(output, config) as writer:
        writer.begin_array(array_name, fields)

        count = 0
        for item in query_func():
            writer.write_item(item)
            count += 1

            if count % batch_size == 0:
                # Flush periodically for large datasets
                if writer._file:
                    writer._file.flush()

        writer.end_array()
        return count
