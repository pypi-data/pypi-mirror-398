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
    dtype_map = {
        'int64': 'integer',
        'float64': 'number',
        'bool': 'boolean',
        'object': 'string',
        'datetime64[ns]': 'string',  # Could be refined to format: date-time
    }

    for column, dtype in df.dtypes.items():
        schema_type = dtype_map.get(str(dtype), 'string')
        schema["properties"][column] = {"type": schema_type}
        
        # Simple heuristic: if no nulls, mark as required
        if not df[column].isnull().any():
            schema["required"].append(column)

    return schema
