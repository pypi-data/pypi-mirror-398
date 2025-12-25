import pandas as pd
import json

def infer_schema(data_file: str) -> dict:
    """
    Infers a JSON schema from a CSV or JSON data file.

    Args:
        data_file (str): Path to the CSV or JSON file.

    Returns:
        dict: A dictionary representing the JSON schema.
    """
    if data_file.endswith('.csv'):
        df = pd.read_csv(data_file)
    elif data_file.endswith('.json'):
        df = pd.read_json(data_file)
    else:
        raise ValueError("Unsupported file format. Only CSV and JSON are supported.")

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }

    # Map pandas dtypes to JSON schema types
    for column, dtype in df.dtypes.items():
        schema_type = 'string' # Default
        dtype_str = str(dtype)
        
        if 'int' in dtype_str:
            schema_type = 'integer'
        elif 'float' in dtype_str:
            schema_type = 'number'
        elif 'bool' in dtype_str:
            schema_type = 'boolean'
            
        schema["properties"][column] = {"type": schema_type}

        # Date detection
        if schema_type == 'string':
            # Check if column looks like a date/datetime
            try:
                if pd.to_datetime(df[column], errors='coerce').notna().all():
                     schema["properties"][column]["format"] = "date-time"
            except:
                pass
            
            # Email detection (simple heuristic)
            try:
                 if df[column].astype(str).str.contains(r'^[\w\.-]+@[\w\.-]+\.\w+$').all():
                     schema["properties"][column]["format"] = "email"
            except:
                pass


        # Nullability check
        if not df[column].isnull().any():
            schema["required"].append(column)

    return schema
