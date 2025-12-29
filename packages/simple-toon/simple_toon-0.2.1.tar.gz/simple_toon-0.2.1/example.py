#!/usr/bin/env python3
"""Example usage of toon_parser library."""

from toon_parser import parse, stringify

# Example 1: JSON to TOON conversion
print("=" * 60)
print("Example 1: JSON to TOON Conversion")
print("=" * 60)

json_data = {
    "users": [
        {"id": 1, "name": "Alice", "active": True, "score": 95.5},
        {"id": 2, "name": "Bob", "active": False, "score": 87.3},
        {"id": 3, "name": "Charlie", "active": True, "score": 92.0},
    ]
}

print("\nOriginal JSON:")
import json
print(json.dumps(json_data, indent=2))

toon_output = stringify(json_data)
print("\nTOON format:")
print(toon_output)

# Example 2: TOON to JSON conversion
print("\n" + "=" * 60)
print("Example 2: TOON to JSON Conversion")
print("=" * 60)

toon_input = """logs[3]{id,timestamp,level,message}:
  2001,"2025-11-18T08:14:23Z",error,"Connection failed"
  2002,"2025-11-18T08:15:00Z",info,"Server started"
  2003,"2025-11-18T08:16:30Z",warning,"High memory usage"
"""

print("\nTOON input:")
print(toon_input)

parsed_json = parse(toon_input)
print("\nParsed JSON:")
print(json.dumps(parsed_json, indent=2))

# Example 3: Round-trip conversion
print("\n" + "=" * 60)
print("Example 3: Round-trip Conversion (JSON → TOON → JSON)")
print("=" * 60)

original = {
    "products": [
        {"sku": "A001", "name": "Widget", "price": 19.99, "in_stock": True},
        {"sku": "B002", "name": "Gadget", "price": 29.99, "in_stock": False},
    ]
}

print("\nOriginal JSON:")
print(json.dumps(original, indent=2))

# Convert to TOON
toon = stringify(original)
print("\nConverted to TOON:")
print(toon)

# Convert back to JSON
result = parse(toon)
print("\nConverted back to JSON:")
print(json.dumps(result, indent=2))

# Verify round-trip
print("\nRound-trip successful:", original == result)

# Example 4: Token savings demonstration
print("\n" + "=" * 60)
print("Example 4: Token Savings Estimation")
print("=" * 60)

large_dataset = {
    "transactions": [
        {
            "id": i,
            "amount": round(100.50 + i * 0.33, 2),
            "status": "completed" if i % 2 == 0 else "pending",
            "verified": i % 3 == 0,
        }
        for i in range(50)
    ]
}

json_str = json.dumps(large_dataset)
toon_str = stringify(large_dataset)

print(f"\nJSON size: {len(json_str)} characters")
print(f"TOON size: {len(toon_str)} characters")
print(f"Savings: {len(json_str) - len(toon_str)} characters ({100 * (1 - len(toon_str) / len(json_str)):.1f}%)")
print(f"\nEstimated token savings: ~{100 * (1 - len(toon_str) / len(json_str)):.0f}%")
print(f"(Note: Actual token savings may vary based on tokenizer)")
