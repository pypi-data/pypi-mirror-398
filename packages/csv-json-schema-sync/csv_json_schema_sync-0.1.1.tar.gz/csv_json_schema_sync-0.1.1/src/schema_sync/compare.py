import json

def compare_schemas(schema_old_file: str, schema_new_file: str) -> dict:
    """
    Compares two JSON schemas and detects new and missing columns.

    Args:
        schema_old_file (str): Path to the old/reference schema file.
        schema_new_file (str): Path to the new schema file or one generated from new data.

    Returns:
        dict: A dictionary containing 'new_columns' and 'missing_columns'.
    """
    try:
        with open(schema_old_file, 'r') as f:
            schema_old = json.load(f)
        with open(schema_new_file, 'r') as f:
            schema_new = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Schema file not found: {e.filename}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e.doc}")
        return {}

    old_props = set(schema_old.get("properties", {}).keys())
    new_props = set(schema_new.get("properties", {}).keys())

    new_columns = list(new_props - old_props)
    missing_columns = list(old_props - new_props)

    diff = {
        "new_columns": new_columns,
        "missing_columns": missing_columns
    }

    return diff
