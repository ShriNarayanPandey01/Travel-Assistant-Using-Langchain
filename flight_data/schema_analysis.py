import json
from typing import Any, Dict, List, Union
from collections import defaultdict

def analyze_json_schema(data: Any, path: str = "root") -> Dict:
    """Recursively analyze JSON structure and return schema"""
    
    if isinstance(data, dict):
        schema = {
            "type": "object",
            "properties": {}
        }
        for key, value in data.items():
            schema["properties"][key] = analyze_json_schema(value, f"{path}.{key}")
        return schema
    
    elif isinstance(data, list):
        if not data:
            return {"type": "array", "items": {"type": "unknown"}}
        
        # Analyze all items to find common schema
        item_schemas = []
        for i, item in enumerate(data[:10]):  # Sample first 10 items
            item_schemas.append(analyze_json_schema(item, f"{path}[{i}]"))
        
        # For simplicity, use the first item's schema
        return {
            "type": "array",
            "length": len(data),
            "items": item_schemas[0] if item_schemas else {"type": "unknown"}
        }
    
    elif isinstance(data, str):
        return {"type": "string", "example": data[:50] + "..." if len(data) > 50 else data}
    
    elif isinstance(data, (int, float)):
        return {"type": "number" if isinstance(data, float) else "integer", "example": data}
    
    elif isinstance(data, bool):
        return {"type": "boolean", "example": data}
    
    elif data is None:
        return {"type": "null"}
    
    else:
        return {"type": f"unknown ({type(data).__name__})"}

def print_schema(schema: Dict, indent: int = 0) -> None:
    """Pretty print the schema"""
    spaces = "  " * indent
    
    if schema.get("type") == "object":
        print(f"{spaces}type: object")
        if "properties" in schema:
            print(f"{spaces}properties:")
            for key, value in schema["properties"].items():
                print(f"{spaces}  {key}:")
                print_schema(value, indent + 2)
    
    elif schema.get("type") == "array":
        print(f"{spaces}type: array (length: {schema.get('length', 'unknown')})")
        print(f"{spaces}items:")
        print_schema(schema["items"], indent + 1)
    
    else:
        type_info = f"{spaces}type: {schema['type']}"
        if "example" in schema:
            type_info += f" (example: {schema['example']})"
        print(type_info)

def get_json_statistics(data: Any) -> Dict:
    """Get statistics about the JSON data"""
    stats = {
        "total_keys": 0,
        "total_values": 0,
        "data_types": defaultdict(int),
        "max_depth": 0,
        "array_lengths": []
    }
    
    def analyze(obj, depth=0):
        stats["max_depth"] = max(stats["max_depth"], depth)
        
        if isinstance(obj, dict):
            stats["data_types"]["object"] += 1
            stats["total_keys"] += len(obj)
            for value in obj.values():
                analyze(value, depth + 1)
        
        elif isinstance(obj, list):
            stats["data_types"]["array"] += 1
            stats["array_lengths"].append(len(obj))
            for item in obj:
                analyze(item, depth + 1)
        
        elif isinstance(obj, str):
            stats["data_types"]["string"] += 1
            stats["total_values"] += 1
        
        elif isinstance(obj, (int, float)):
            stats["data_types"]["number"] += 1
            stats["total_values"] += 1
        
        elif isinstance(obj, bool):
            stats["data_types"]["boolean"] += 1
            stats["total_values"] += 1
        
        elif obj is None:
            stats["data_types"]["null"] += 1
            stats["total_values"] += 1
    
    analyze(data)
    return dict(stats)

# Main function to analyze JSON file
def analyze_json_file(filename: str):
    """Load and analyze a JSON file"""
    
    try:
        # Load JSON file
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        print(f"=== JSON Schema Analysis for: {filename} ===\n")
        
        # Get and print schema
        schema = analyze_json_schema(data)
        print("Schema Structure:")
        print("-" * 40)
        print_schema(schema)
        
        # Get and print statistics
        stats = get_json_statistics(data)
        print("\n\nStatistics:")
        print("-" * 40)
        print(f"Max depth: {stats['max_depth']}")
        print(f"Total keys: {stats['total_keys']}")
        print(f"Total values: {stats['total_values']}")
        print("\nData type distribution:")
        for dtype, count in stats['data_types'].items():
            print(f"  {dtype}: {count}")
        
        if stats['array_lengths']:
            print(f"\nArray statistics:")
            print(f"  Min length: {min(stats['array_lengths'])}")
            print(f"  Max length: {max(stats['array_lengths'])}")
            print(f"  Avg length: {sum(stats['array_lengths']) / len(stats['array_lengths']):.2f}")
    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file - {e}")
    except Exception as e:
        print(f"Error: {e}")

# Alternative: Get schema in JSON Schema format
def get_json_schema_format(data: Any) -> Dict:
    """Generate schema in JSON Schema format (simplified)"""
    
    def build_schema(obj):
        if isinstance(obj, dict):
            properties = {}
            required = []
            
            for key, value in obj.items():
                properties[key] = build_schema(value)
                required.append(key)
            
            return {
                "type": "object",
                "properties": properties,
                "required": required
            }
        
        elif isinstance(obj, list):
            if obj:
                return {
                    "type": "array",
                    "items": build_schema(obj[0])
                }
            return {"type": "array"}
        
        elif isinstance(obj, str):
            return {"type": "string"}
        
        elif isinstance(obj, int):
            return {"type": "integer"}
        
        elif isinstance(obj, float):
            return {"type": "number"}
        
        elif isinstance(obj, bool):
            return {"type": "boolean"}
        
        elif obj is None:
            return {"type": "null"}
        
        return {"type": "unknown"}
    
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        **build_schema(data)
    }

# Usage examples:

# 1. Basic usage
analyze_json_file('AMD.json')

# 2. Save schema to file
def save_schema_to_file(input_file: str, output_file: str = None):
    if output_file is None:
        output_file = input_file.replace('.json', '_schema.json')
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    schema = get_json_schema_format(data)
    
    with open(output_file, 'w') as f:
        json.dump(schema, f, indent=2)
    
    print(f"Schema saved to: {output_file}")

# Example: save_schema_to_file('flight_data.json')