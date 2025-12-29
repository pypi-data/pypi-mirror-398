# TOON Parser (Python)

A Python parser and serializer for **TOON (Token-Oriented Object Notation)**, a compact data format designed to reduce LLM token consumption by 30-60% compared to JSON.

## Installation

```bash
pip install simple-toon
```

## Quick Start

### Functional API (Recommended for simple use cases)

```python
from toon_parser import parse, stringify

# Convert TOON to JSON
toon_data = """
users[2]{id,name,active}:
  1,Alice,true
  2,Bob,false
"""
json_data = parse(toon_data)
# Result: {"users": [{"id": 1, "name": "Alice", "active": true}, ...]}

# Convert JSON to TOON
json_obj = {
    "users": [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False}
    ]
}
toon_string = stringify(json_obj)
```

### Object-Oriented API (Recommended for complex applications)

```python
from toon_parser import ToonParser, ToonSerializer, ToonDocument

# Create configured parser
parser = ToonParser(advanced=True)
data = parser.parse(toon_string)

# Create configured serializer
serializer = ToonSerializer(advanced=True)
toon = serializer.stringify(data)

# Work with documents
doc = ToonDocument.from_file("data.toon")
active_users = doc.query("users", lambda u: u["active"])
doc.add_item("users", {"id": 99, "name": "New User"})
doc.save("updated.toon")
```

## Advanced Features

### Nested Objects

Automatically flatten and unflatten nested objects:

```python
from toon_parser import stringify_advanced, parse_advanced

data = {
    "users": [
        {"id": 1, "name": "Alice", "address": {"city": "NYC", "zip": "10001"}},
        {"id": 2, "name": "Bob", "address": {"city": "LA", "zip": "90001"}}
    ]
}

# Serializes with dot notation: users[2]{id,name,address.city,address.zip}:
toon = stringify_advanced(data)

# Parse restores nested structure
result = parse_advanced(toon)
```

### Multiple Arrays

Handle multiple arrays in a single TOON document:

```python
data = {
    "users": [{"id": 1, "name": "Alice"}],
    "products": [{"sku": "A001", "price": 19.99}]
}

toon = stringify_advanced(data)
# Both arrays in one document
parsed = parse_advanced(toon)
```

### Streaming Parser & Serializer

Memory-efficient operations for large datasets:

```python
from toon_parser import stream_parse, StreamingSerializer

# Streaming parser (read large files)
for array_name, items in stream_parse(large_toon_data):
    print(f"Processing {array_name}: {len(items)} items")
    for item in items:
        process(item)  # Process one at a time

# Streaming serializer (write large files)
with StreamingSerializer("output.toon") as writer:
    writer.begin_array("users", ["id", "name", "email"])

    for user in database.query_users():  # Stream from DB
        writer.write_row([user.id, user.name, user.email])

    writer.end_array()
```

### Custom Configuration

```python
from toon_parser import ToonConfig, stringify_advanced

config = ToonConfig(
    separator="_",      # Use underscore instead of dot
    indent_size=4,      # 4-space indentation
    max_nesting_depth=5 # Maximum nesting levels
)

toon = stringify_advanced(data, config)
```

### Schema Validation

Define and validate data schemas:

```python
from toon_parser import Field, FieldType, Schema, infer_schema

# Define schema manually
schema = Schema("users", [
    Field("id", FieldType.INTEGER),
    Field("name", FieldType.STRING),
    Field("email", FieldType.STRING, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"),
    Field("age", FieldType.INTEGER, min_value=0, max_value=120)
])

# Validate data
schema.validate(data)

# Or infer schema from example data
schema = infer_schema(sample_data, "users")
```

### File I/O

Read and write TOON files with optional validation:

```python
from toon_parser import read_toon, write_toon, convert_json_to_toon

# Write TOON file with validation
write_toon(data, "output.toon", advanced=True, schema=schema)

# Read TOON file
data = read_toon("input.toon", advanced=True)

# Convert between formats
convert_json_to_toon("input.json", "output.toon")

# Batch convert directory
from toon_parser import batch_convert
batch_convert("json_files/", "toon_files/", from_format="json", to_format="toon")

# Get file statistics
from toon_parser import get_file_stats
stats = get_file_stats("data.toon")
print(f"Total items: {stats['total_items']}")
```

## What is TOON?

TOON is a token-efficient serialization format optimized for LLM input. It combines:
- YAML-style indentation for nested objects
- CSV-style tabular layout for uniform arrays
- Explicit schema declarations with `[N]{field1,field2}` headers

## Performance

- **30-60% fewer tokens** than JSON (up to 63% with nested objects)
- **Lossless, deterministic** round-trip conversion
- Optimized for uniform arrays (logs, user lists, analytics events)
- Streaming parser for memory-efficient processing of large files

### Benchmarks

| Dataset | JSON Size | TOON Size | Savings |
|---------|-----------|-----------|---------|
| Simple arrays (50 items) | 3,536 chars | 1,362 chars | **61.5%** |
| Nested objects (50 items) | 7,220 chars | 2,639 chars | **63.4%** |
| Event data (10 items) | 845 bytes | 235 bytes | **72.2%** |
| Multiple arrays | Varies | Varies | 30-60% |

## API Reference

### Functional API

**Basic Functions:**
- `parse(toon: str) -> Any` - Parse TOON to JSON
- `stringify(obj: Any) -> str` - Serialize JSON to TOON

**Advanced Functions:**
- `parse_advanced(toon: str, config: ToonConfig) -> Any` - Parse with nested object support
- `stringify_advanced(obj: Any, config: ToonConfig) -> str` - Serialize with nested objects
- `stream_parse(toon: str) -> Iterator` - Memory-efficient streaming parser

**Schema Validation:**
- `Schema(array_name, fields)` - Define validation schema
- `Field(name, field_type, **options)` - Define field with constraints
- `infer_schema(data, array_name)` - Auto-generate schema from data
- `MultiSchema(schemas)` - Validate multiple arrays

**File I/O:**
- `read_toon(path, advanced, schema)` - Read and validate TOON file
- `write_toon(data, path, advanced, schema)` - Write and validate TOON file
- `convert_json_to_toon(json_path, toon_path)` - Convert JSON → TOON
- `convert_toon_to_json(toon_path, json_path)` - Convert TOON → JSON
- `batch_convert(input_dir, output_dir)` - Batch convert files
- `get_file_stats(path)` - Analyze file statistics

**Streaming:**
- `StreamingSerializer(output)` - Stream write large TOON files
- `streaming_serializer(output)` - Context manager for streaming
- `stream_from_database(query_func, ...)` - Stream from database to TOON

### Object-Oriented API

**Classes:**
- `ToonParser(advanced, config, schema)` - Stateful parser
- `ToonSerializer(advanced, config, schema)` - Stateful serializer
- `ToonDocument(data)` - Document object model with query/manipulation methods
- `ToonConverter(advanced, config)` - Format converter with statistics

## Examples

See the example files for detailed usage:
- `example.py` - Basic parsing and serialization (functional API)
- `example_advanced.py` - Nested objects, multiple arrays, configuration
- `example_schema_io.py` - Schema validation and file I/O
- `example_oo_streaming.py` - Object-oriented API and streaming serializer

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=toon_parser

# Format code
black toon_parser/ tests/

# Lint
ruff check toon_parser/ tests/

# Type check
mypy toon_parser/
```

## License

MIT
