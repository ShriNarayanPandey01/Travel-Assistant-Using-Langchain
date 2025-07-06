import requests
import json
from datetime import datetime

# Make the API request
response = requests.get("apiurl")

try:
    # Get the JSON data
    data = response.json()
    
    # Create a filename with timestamp
    filename = f"TIR.json"
    
    # Save to a JSON file with pretty formatting
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
    
    print(f"Data saved successfully to '{filename}'")
    
    # Also print a preview
    print(f"\nTotal records: {len(data) if isinstance(data, list) else 'N/A'}")
    
except requests.exceptions.JSONDecodeError:
    print("Error: Invalid JSON response")
except Exception as e:
    print(f"Error saving file: {e}")
