"""TOON Parser - A Python parser and serializer for Token-Oriented Object Notation."""

from .parser import parse
from .serializer import stringify
from .advanced import (
    ToonConfig,
    stringify_advanced,
    parse_advanced,
    stream_parse,
    flatten_object,
    unflatten_object,
)
from .schema import (
    Field,
    FieldType,
    Schema,
    MultiSchema,
    ValidationError,
    infer_schema,
)
from .io import (
    ToonFileError,
    read_toon,
    write_toon,
    read_json,
    write_json,
    convert_json_to_toon,
    convert_toon_to_json,
    batch_convert,
    get_file_stats,
)
from .streaming import (
    StreamingSerializer,
    streaming_serializer,
    stream_from_database,
)
from .oo_api import (
    ToonParser,
    ToonSerializer,
    ToonDocument,
    ToonConverter,
)

__version__ = "0.2.0"  # Bumped for new OO API and streaming serializer
__all__ = [
    # Basic parsing/serializing (functional API)
    "parse",
    "stringify",
    # Advanced features (functional API)
    "ToonConfig",
    "stringify_advanced",
    "parse_advanced",
    "stream_parse",
    "flatten_object",
    "unflatten_object",
    # Schema validation
    "Field",
    "FieldType",
    "Schema",
    "MultiSchema",
    "ValidationError",
    "infer_schema",
    # File I/O
    "ToonFileError",
    "read_toon",
    "write_toon",
    "read_json",
    "write_json",
    "convert_json_to_toon",
    "convert_toon_to_json",
    "batch_convert",
    "get_file_stats",
    # Streaming serializer
    "StreamingSerializer",
    "streaming_serializer",
    "stream_from_database",
    # Object-oriented API
    "ToonParser",
    "ToonSerializer",
    "ToonDocument",
    "ToonConverter",
]
