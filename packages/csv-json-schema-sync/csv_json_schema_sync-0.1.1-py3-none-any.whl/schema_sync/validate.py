import pandas as pd
import json
from jsonschema import validate, ValidationError

def validate_data(data_file: str, schema_file: str) -> bool:
    """
    Validates a CSV or JSON data file against a JSON schema.

    Args:
        data_file (str): Path to the CSV or JSON file.
        schema_file (str): Path to the JSON schema file.

    Returns:
        bool: True if valid, False otherwise. Prints validation errors.
    """
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found at {schema_file}")
        return False
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in schema file {schema_file}")
        return False

    if data_file.endswith('.csv'):
        df = pd.read_csv(data_file)
    elif data_file.endswith('.json'):
        df = pd.read_json(data_file)
    else:
        print("Error: Unsupported file format. Only CSV and JSON are supported.")
        return False

    # Convert DataFrame to list of dicts for validation
    data = df.to_dict(orient='records')

    try:
        for i, row in enumerate(data):
            validate(instance=row, schema=schema)
        print("Validation successful!")
        return True
    except ValidationError as e:
        print(f"Validation failed at row {i + 1}: {e.message}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during validation: {e}")
        return False
