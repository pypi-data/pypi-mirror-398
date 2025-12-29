#!/usr/bin/env python3
"""Examples for Object-Oriented API and Streaming Serializer."""

import tempfile
from pathlib import Path
from toon_parser import (
    # OO API
    ToonParser,
    ToonSerializer,
    ToonDocument,
    ToonConverter,
    # Streaming
    StreamingSerializer,
    streaming_serializer,
    stream_from_database,
    # Config
    ToonConfig,
    # Schema
    Schema,
    Field,
    FieldType,
)

print("=" * 70)
print("OBJECT-ORIENTED API & STREAMING SERIALIZER EXAMPLES")
print("=" * 70)

# ============================================================================
# PART 1: OBJECT-ORIENTED API
# ============================================================================

print("\n" + "=" * 70)
print("PART 1: Object-Oriented API")
print("=" * 70)

# Example 1: ToonParser class
print("\n" + "-" * 70)
print("Example 1: ToonParser Class (Stateful parsing)")
print("-" * 70)

# Create parser with configuration
parser = ToonParser(
    advanced=True,
    config=ToonConfig(separator="_")
)

toon_data = """users[2]{id,profile_name,profile_age}:
  1,Alice,30
  2,Bob,25"""

print("\nParsing with configured parser...")
data = parser.parse(toon_data)
print(f"Parsed {len(data['users'])} users")
print(f"First user: {data['users'][0]}")

# Example 2: ToonSerializer class
print("\n" + "-" * 70)
print("Example 2: ToonSerializer Class (Stateful serialization)")
print("-" * 70)

serializer = ToonSerializer(
    advanced=True,
    config=ToonConfig(separator=".", indent_size=2)
)

nested_data = {
    "employees": [
        {"id": 1, "info": {"name": "Alice", "dept": "Engineering"}},
        {"id": 2, "info": {"name": "Bob", "dept": "Sales"}},
    ]
}

print("\nSerializing with configured serializer...")
toon_output = serializer.stringify(nested_data)
print("TOON output:")
print(toon_output)

# Example 3: ToonDocument class
print("\n" + "-" * 70)
print("Example 3: ToonDocument Class (Document object model)")
print("-" * 70)

# Create a document
doc = ToonDocument({
    "users": [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False},
        {"id": 3, "name": "Charlie", "active": True},
    ]
})

print(f"\nDocument: {doc}")
print(f"Total items: {doc.total_items()}")

# Query the document
active_users = doc.query("users", lambda u: u["active"])
print(f"Active users: {len(active_users)}")

# Add new item
doc.add_item("users", {"id": 4, "name": "Diana", "active": True})
print(f"After adding: {doc.count('users')} users")

# Add new array
doc.add_array("products", [{"sku": "A001", "price": 19.99}])
print(f"Arrays: {doc.get_array_names()}")

# Save to file
with tempfile.TemporaryDirectory() as tmpdir:
    output_file = Path(tmpdir) / "document.toon"
    doc.save(output_file)
    print(f"Saved to {output_file.name}: {output_file.stat().st_size} bytes")

# Example 4: ToonConverter class
print("\n" + "-" * 70)
print("Example 4: ToonConverter Class (Format conversion)")
print("-" * 70)

converter = ToonConverter(advanced=True)

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)

    # Create JSON file
    import json
    json_file = tmpdir / "data.json"
    test_data = {"events": [{"id": i, "type": "click"} for i in range(50)]}
    json_file.write_text(json.dumps(test_data))

    # Convert JSON -> TOON
    toon_file = tmpdir / "data.toon"
    converter.json_to_toon(json_file, toon_file)

    # Get savings
    stats = converter.get_savings(json_file, toon_file)
    print(f"\nConversion Stats:")
    print(f"  JSON size: {stats['json_size_bytes']} bytes")
    print(f"  TOON size: {stats['toon_size_bytes']} bytes")
    print(f"  Savings: {stats['savings_percent']}%")

# ============================================================================
# PART 2: STREAMING SERIALIZER
# ============================================================================

print("\n" + "=" * 70)
print("PART 2: Streaming Serializer (Memory Efficient)")
print("=" * 70)

# Example 5: Basic streaming write
print("\n" + "-" * 70)
print("Example 5: Basic Streaming Write")
print("-" * 70)

with tempfile.TemporaryDirectory() as tmpdir:
    output_file = Path(tmpdir) / "streaming.toon"

    print(f"\nStreaming 1,000 users to {output_file.name}...")

    with StreamingSerializer(output_file) as writer:
        # Begin array
        writer.begin_array("users", ["id", "name", "email", "active"])

        # Write items one at a time (generator - no memory buildup)
        for i in range(1000):
            writer.write_row([
                i,
                f"User{i}",
                f"user{i}@example.com",
                i % 2 == 0
            ])

        # End array
        count = writer.end_array()

    print(f"✓ Wrote {count} items")
    print(f"  File size: {output_file.stat().st_size:,} bytes")

# Example 6: Streaming from iterator
print("\n" + "-" * 70)
print("Example 6: Streaming from Iterator/Generator")
print("-" * 70)

def generate_products(count):
    """Simulate streaming from database or API."""
    for i in range(count):
        yield {
            "sku": f"SKU-{i:05d}",
            "name": f"Product {i}",
            "price": round(10 + i * 0.99, 2),
            "in_stock": i % 3 != 0,
        }

with tempfile.TemporaryDirectory() as tmpdir:
    output_file = Path(tmpdir) / "products.toon"

    print(f"\nStreaming from generator...")

    with streaming_serializer(output_file) as writer:
        # Write entire iterator at once
        count = writer.write_array("products", generate_products(5000))

    print(f"✓ Wrote {count} products from generator")
    print(f"  File size: {output_file.stat().st_size:,} bytes")
    print("  Memory: Only processed one item at a time!")

# Example 7: Streaming from "database"
print("\n" + "-" * 70)
print("Example 7: Streaming from Database Query")
print("-" * 70)

def mock_database_query():
    """Simulate database cursor that yields rows."""
    # In real code, this would be:
    # cursor.execute("SELECT id, email, created FROM users")
    # for row in cursor:
    #     yield {"id": row[0], "email": row[1], "created": row[2]}

    for i in range(10000):
        yield {
            "user_id": i,
            "email": f"user{i}@example.com",
            "created": f"2025-01-{(i % 28) + 1:02d}",
            "verified": i % 5 == 0,
        }

with tempfile.TemporaryDirectory() as tmpdir:
    output_file = Path(tmpdir) / "database_export.toon"

    print(f"\nStreaming 10,000 rows from 'database'...")

    count = stream_from_database(
        query_func=mock_database_query,
        array_name="users",
        fields=["user_id", "email", "created", "verified"],
        output=output_file,
        batch_size=1000,  # Flush every 1000 rows
    )

    print(f"✓ Exported {count:,} database rows")
    print(f"  File size: {output_file.stat().st_size:,} bytes")
    print("  Memory: Constant (streamed from cursor)!")

# Example 8: Multiple arrays in one stream
print("\n" + "-" * 70)
print("Example 8: Multiple Arrays in Streaming Output")
print("-" * 70)

with tempfile.TemporaryDirectory() as tmpdir:
    output_file = Path(tmpdir) / "multi_array.toon"

    print(f"\nWriting multiple arrays to single file...")

    with StreamingSerializer(output_file) as writer:
        # First array
        writer.begin_array("users", ["id", "name"])
        for i in range(100):
            writer.write_item({"id": i, "name": f"User{i}"})
        count1 = writer.end_array()

        # Second array
        writer.begin_array("orders", ["order_id", "user_id", "total"])
        for i in range(500):
            writer.write_item({"order_id": i, "user_id": i % 100, "total": round(50 + i * 1.5, 2)})
        count2 = writer.end_array()

        # Third array
        writer.begin_array("products", ["sku", "price"])
        for i in range(200):
            writer.write_item({"sku": f"P{i}", "price": 19.99 + i})
        count3 = writer.end_array()

    print(f"✓ Wrote 3 arrays:")
    print(f"  - users: {count1} items")
    print(f"  - orders: {count2} items")
    print(f"  - products: {count3} items")
    print(f"  Total file size: {output_file.stat().st_size:,} bytes")

# ============================================================================
# COMPARISON: Functional vs OO API
# ============================================================================

print("\n" + "=" * 70)
print("API Style Comparison")
print("=" * 70)

sample_data = {"items": [{"id": 1, "value": "test"}]}

print("\nFunctional API (stateless):")
print("-" * 40)
print("from toon_parser import parse, stringify")
print("")
print("toon = stringify(data)")
print("data = parse(toon)")

print("\nObject-Oriented API (stateful):")
print("-" * 40)
print("from toon_parser import ToonSerializer, ToonParser")
print("")
print("serializer = ToonSerializer(advanced=True)")
print("toon = serializer.stringify(data)")
print("")
print("parser = ToonParser(advanced=True)")
print("data = parser.parse(toon)")

print("\nBoth APIs produce identical results!")
print("Choose based on your preference:")
print("  - Functional: Quick one-off conversions")
print("  - OO: Repeated operations with configuration")

print("\n" + "=" * 70)
print("✓ All examples completed successfully!")
print("=" * 70)
