#!/usr/bin/env python3
"""Examples for schema validation and file I/O features."""

import tempfile
from pathlib import Path
from toon_parser import (
    # Schema validation
    Field,
    FieldType,
    Schema,
    MultiSchema,
    ValidationError,
    infer_schema,
    # File I/O
    read_toon,
    write_toon,
    read_json,
    write_json,
    convert_json_to_toon,
    convert_toon_to_json,
    batch_convert,
    get_file_stats,
    ToonFileError,
)

print("=" * 70)
print("SCHEMA VALIDATION & FILE I/O EXAMPLES")
print("=" * 70)

# Example 1: Basic Schema Validation
print("\n" + "=" * 70)
print("Example 1: Basic Schema Validation")
print("=" * 70)

# Define a schema
user_schema = Schema(
    "users",
    [
        Field("id", FieldType.INTEGER),
        Field("name", FieldType.STRING),
        Field("email", FieldType.STRING, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"),
        Field("age", FieldType.INTEGER, min_value=0, max_value=120),
        Field("active", FieldType.BOOLEAN),
    ],
)

# Valid data
valid_data = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30, "active": True},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25, "active": False},
    ]
}

print("\nValidating valid data...")
try:
    user_schema.validate(valid_data)
    print("✓ Validation passed!")
except ValidationError as e:
    print(f"✗ Validation failed: {e}")

# Invalid data
invalid_data = {
    "users": [
        {"id": 1, "name": "Charlie", "email": "invalid-email", "age": 30, "active": True},
    ]
}

print("\nValidating invalid data...")
try:
    user_schema.validate(invalid_data)
    print("✓ Validation passed!")
except ValidationError as e:
    print(f"✗ Validation failed: {e}")

# Example 2: Schema Inference
print("\n" + "=" * 70)
print("Example 2: Automatic Schema Inference")
print("=" * 70)

sample_data = {
    "products": [
        {"sku": "A001", "name": "Widget", "price": 19.99, "in_stock": True},
        {"sku": "A002", "name": "Gadget", "price": 29.99, "in_stock": False},
        {"sku": "A003", "name": "Doohickey", "price": 9.99, "in_stock": True},
    ]
}

print("\nInferring schema from sample data...")
inferred = infer_schema(sample_data, "products")

print(f"\nInferred {len(inferred.fields)} fields:")
for field_name, field in inferred.fields.items():
    print(f"  - {field_name}: {field.field_type.value} (required={field.required}, nullable={field.nullable})")

# Use inferred schema to validate
print("\nUsing inferred schema to validate data...")
try:
    inferred.validate(sample_data)
    print("✓ Validation passed with inferred schema!")
except ValidationError as e:
    print(f"✗ Validation failed: {e}")

# Example 3: File I/O with Validation
print("\n" + "=" * 70)
print("Example 3: File I/O with Schema Validation")
print("=" * 70)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)

    # Write TOON file with validation
    toon_file = tmp_path / "validated_users.toon"

    print(f"\nWriting data to {toon_file.name} with schema validation...")
    try:
        write_toon(valid_data, toon_file, advanced=True, schema=user_schema)
        print("✓ File written successfully!")
    except ValidationError as e:
        print(f"✗ Write failed: {e}")

    # Read TOON file with validation
    print(f"\nReading {toon_file.name} with schema validation...")
    try:
        data = read_toon(toon_file, advanced=True, schema=user_schema)
        print(f"✓ File read successfully! Got {len(data['users'])} users")
    except ValidationError as e:
        print(f"✗ Read failed: {e}")

# Example 4: Format Conversion
print("\n" + "=" * 70)
print("Example 4: JSON <-> TOON Conversion")
print("=" * 70)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)

    # Create a JSON file
    json_file = tmp_path / "data.json"
    toon_file = tmp_path / "data.toon"

    data = {
        "events": [
            {"id": i, "type": "click" if i % 2 == 0 else "view", "timestamp": f"2025-01-{(i % 28) + 1:02d}"}
            for i in range(10)
        ]
    }

    print(f"\nCreating {json_file.name}...")
    write_json(data, json_file)
    print(f"✓ JSON file created: {json_file.stat().st_size} bytes")

    print(f"\nConverting to TOON format...")
    convert_json_to_toon(json_file, toon_file, advanced=True)
    print(f"✓ TOON file created: {toon_file.stat().st_size} bytes")

    # Calculate savings
    json_size = json_file.stat().st_size
    toon_size = toon_file.stat().st_size
    savings_pct = 100 * (1 - toon_size / json_size)
    print(f"  Savings: {json_size - toon_size} bytes ({savings_pct:.1f}%)")

    print(f"\nConverting back to JSON...")
    json_file2 = tmp_path / "data_restored.json"
    convert_toon_to_json(toon_file, json_file2, advanced=True)

    restored = read_json(json_file2)
    print(f"✓ Round-trip successful: {data == restored}")

# Example 5: Batch Conversion
print("\n" + "=" * 70)
print("Example 5: Batch File Conversion")
print("=" * 70)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)
    input_dir = tmp_path / "json_files"
    output_dir = tmp_path / "toon_files"
    input_dir.mkdir()

    # Create multiple JSON files
    print("\nCreating 5 JSON files...")
    for i in range(5):
        data = {"items": [{"id": j, "value": f"item_{i}_{j}"} for j in range(10)]}
        write_json(data, input_dir / f"dataset_{i}.json")

    print(f"✓ Created {len(list(input_dir.glob('*.json')))} JSON files")

    # Batch convert
    print(f"\nBatch converting JSON -> TOON...")
    results = batch_convert(input_dir, output_dir, from_format="json", to_format="toon")

    print(f"✓ Converted {len(results)} files:")
    for json_file, toon_file in list(results.items())[:3]:
        print(f"  {Path(json_file).name} -> {Path(toon_file).name}")
    if len(results) > 3:
        print(f"  ... and {len(results) - 3} more")

# Example 6: File Statistics
print("\n" + "=" * 70)
print("Example 6: File Statistics Analysis")
print("=" * 70)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)

    # Create a complex dataset
    complex_data = {
        "users": [{"id": i, "name": f"User{i}"} for i in range(100)],
        "transactions": [
            {"tx_id": i, "amount": round(100 + i * 1.5, 2), "status": "completed"}
            for i in range(500)
        ],
        "logs": [{"level": "info", "message": f"Log entry {i}"} for i in range(1000)],
    }

    toon_file = tmp_path / "complex.toon"
    write_toon(complex_data, toon_file, advanced=True)

    print(f"\nAnalyzing {toon_file.name}...")
    stats = get_file_stats(toon_file)

    print(f"\nFile Statistics:")
    print(f"  Format: {stats['format']}")
    print(f"  Size: {stats['file_size_bytes']:,} bytes")
    print(f"  Total arrays: {stats['total_arrays']}")
    print(f"  Total items: {stats['total_items']:,}")
    print(f"\nArrays:")
    for array_name, array_info in stats['arrays'].items():
        print(f"  - {array_name}: {array_info['count']:,} items")
        if array_info['fields']:
            print(f"    Fields: {', '.join(array_info['fields'][:5])}")

# Example 7: Multi-Schema Validation
print("\n" + "=" * 70)
print("Example 7: Multiple Array Schema Validation")
print("=" * 70)

multi_data = {
    "users": [{"id": 1, "name": "Alice"}],
    "orders": [{"order_id": 1001, "user_id": 1, "total": 99.99}],
}

multi_schema = MultiSchema(
    [
        Schema("users", [Field("id", FieldType.INTEGER), Field("name", FieldType.STRING)]),
        Schema(
            "orders",
            [
                Field("order_id", FieldType.INTEGER),
                Field("user_id", FieldType.INTEGER),
                Field("total", FieldType.FLOAT),
            ],
        ),
    ]
)

print("\nValidating multiple arrays with MultiSchema...")
try:
    multi_schema.validate(multi_data)
    print("✓ All arrays validated successfully!")
except ValidationError as e:
    print(f"✗ Validation failed: {e}")

print("\n" + "=" * 70)
print("✓ All examples completed successfully!")
print("=" * 70)
