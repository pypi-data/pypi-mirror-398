#!/usr/bin/env python3
"""Advanced examples for toon_parser library."""

import json
from toon_parser import (
    stringify_advanced,
    parse_advanced,
    stream_parse,
    ToonConfig,
    flatten_object,
    unflatten_object,
)

print("=" * 70)
print("ADVANCED TOON PARSER EXAMPLES")
print("=" * 70)

# Example 1: Nested Objects
print("\n" + "=" * 70)
print("Example 1: Nested Objects with Auto-Flattening")
print("=" * 70)

users_with_addresses = {
    "users": [
        {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "address": {"street": "123 Main St", "city": "NYC", "zip": "10001"},
        },
        {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "address": {"street": "456 Oak Ave", "city": "LA", "zip": "90001"},
        },
    ]
}

print("\nOriginal JSON with nested objects:")
print(json.dumps(users_with_addresses, indent=2))

toon_nested = stringify_advanced(users_with_addresses)
print("\nTOON format (auto-flattened with dot notation):")
print(toon_nested)

parsed_back = parse_advanced(toon_nested)
print("\nParsed back to JSON (nested structure restored):")
print(json.dumps(parsed_back, indent=2))

print(f"\nRound-trip successful: {parsed_back == users_with_addresses}")

# Example 2: Multiple Root-Level Arrays
print("\n" + "=" * 70)
print("Example 2: Multiple Arrays in One Document")
print("=" * 70)

multi_array_data = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"},
    ],
    "products": [
        {"sku": "A001", "name": "Widget", "price": 19.99},
        {"sku": "B002", "name": "Gadget", "price": 29.99},
    ],
    "orders": [
        {"order_id": 1001, "user_id": 1, "product_sku": "A001", "quantity": 2},
        {"order_id": 1002, "user_id": 2, "product_sku": "B002", "quantity": 1},
    ],
}

print("\nOriginal JSON with multiple arrays:")
print(json.dumps(multi_array_data, indent=2))

toon_multi = stringify_advanced(multi_array_data)
print("\nTOON format with multiple root arrays:")
print(toon_multi)

parsed_multi = parse_advanced(toon_multi)
print("\nParsed back - all arrays restored:")
for key, value in parsed_multi.items():
    print(f"  {key}: {len(value)} items")

# Example 3: Streaming Parser for Large Datasets
print("\n" + "=" * 70)
print("Example 3: Streaming Parser (Memory Efficient)")
print("=" * 70)

large_dataset = {
    "transactions": [
        {
            "id": i,
            "timestamp": f"2025-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z",
            "amount": round(100 + i * 1.5, 2),
            "status": "completed" if i % 2 == 0 else "pending",
        }
        for i in range(100)
    ]
}

toon_large = stringify_advanced(large_dataset)
print(f"\nGenerated TOON with {len(large_dataset['transactions'])} transactions")
print(f"TOON size: {len(toon_large)} characters")

print("\nStreaming parse (processes one array at a time):")
total_processed = 0
for array_name, items in stream_parse(toon_large):
    print(f"  Processing '{array_name}': {len(items)} items")
    # Process items one at a time (memory efficient)
    completed = sum(1 for item in items if item.get("status") == "completed")
    pending = len(items) - completed
    print(f"    - Completed: {completed}, Pending: {pending}")
    total_processed += len(items)

print(f"Total items processed: {total_processed}")

# Example 4: Custom Configuration
print("\n" + "=" * 70)
print("Example 4: Custom Configuration Options")
print("=" * 70)

data_with_deep_nesting = {
    "employees": [
        {
            "id": 1,
            "personal": {
                "name": "Alice",
                "contact": {"email": "alice@company.com", "phone": "555-0001"},
            },
            "position": {"title": "Engineer", "department": "R&D", "level": 3},
        },
        {
            "id": 2,
            "personal": {
                "name": "Bob",
                "contact": {"email": "bob@company.com", "phone": "555-0002"},
            },
            "position": {"title": "Manager", "department": "Sales", "level": 4},
        },
    ]
}

print("\nUsing default config (dot separator):")
config_default = ToonConfig()
toon_default = stringify_advanced(data_with_deep_nesting, config_default)
print(toon_default)

print("\nUsing custom config (underscore separator, 4-space indent):")
config_custom = ToonConfig(separator="_", indent_size=4)
toon_custom = stringify_advanced(data_with_deep_nesting, config_custom)
print(toon_custom)

# Example 5: Object Flattening Utilities
print("\n" + "=" * 70)
print("Example 5: Manual Flatten/Unflatten Operations")
print("=" * 70)

nested_obj = {
    "user": {
        "profile": {"name": "Alice", "age": 30},
        "settings": {"theme": "dark", "notifications": {"email": True, "sms": False}},
    }
}

print("\nOriginal nested object:")
print(json.dumps(nested_obj, indent=2))

flattened = flatten_object(nested_obj)
print("\nFlattened with dot notation:")
print(json.dumps(flattened, indent=2))

unflattened = unflatten_object(flattened)
print("\nUnflattened (restored):")
print(json.dumps(unflattened, indent=2))

print(f"\nRound-trip successful: {unflattened == nested_obj}")

# Example 6: Token Savings with Nested Data
print("\n" + "=" * 70)
print("Example 6: Token Savings Comparison (Nested Data)")
print("=" * 70)

complex_data = {
    "events": [
        {
            "id": i,
            "type": "page_view" if i % 3 == 0 else "click",
            "user": {"id": i % 10, "session": f"session_{i // 10}"},
            "metadata": {
                "timestamp": f"2025-01-01T{(i % 24):02d}:00:00Z",
                "duration_ms": 100 + i * 5,
            },
        }
        for i in range(50)
    ]
}

json_str = json.dumps(complex_data)
toon_str = stringify_advanced(complex_data)

print(f"\nDataset: 50 events with nested objects")
print(f"JSON size: {len(json_str)} characters")
print(f"TOON size: {len(toon_str)} characters")
print(f"Savings: {len(json_str) - len(toon_str)} characters ({100 * (1 - len(toon_str) / len(json_str)):.1f}%)")

print("\nFirst 5 lines of TOON output:")
for i, line in enumerate(toon_str.split("\n")[:5]):
    print(f"  {line}")

print("\n" + "=" * 70)
print("✓ All advanced features demonstrated successfully!")
print("=" * 70)
