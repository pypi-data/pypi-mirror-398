import pytest
from schema_sync import infer_schema, validate_data, compare_schemas
import json
import os

@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name,age\n1,Alice,30\n2,Bob,25")
    return str(csv_file)

@pytest.fixture
def sample_schema(tmp_path):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["id", "name", "age"],
        "additionalProperties": False
    }
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(schema))
    return str(schema_file)

def test_infer_schema(sample_csv):
    schema = infer_schema(sample_csv)
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "id" in schema["properties"]
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]

def test_validate_data_success(sample_csv, sample_schema):
    assert validate_data(sample_csv, sample_schema) is True

def test_validate_data_failure(sample_csv, tmp_path):
    # Create a schema that expects specific types/fields
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"} # Expecting string, but csv has integer
        }
    }
    schema_file = tmp_path / "invalid_schema.json"
    schema_file.write_text(json.dumps(schema))
    assert validate_data(sample_csv, str(schema_file)) is False

def test_compare_schemas(sample_schema, tmp_path):
    # Same schema
    diff = compare_schemas(sample_schema, sample_schema)
    assert diff["new_columns"] == []
    assert diff["missing_columns"] == []

    # New schema with extra column
    schema_new_data = {
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string"}
        }
    }
    schema_new_file = tmp_path / "schema_new.json"
    schema_new_file.write_text(json.dumps(schema_new_data))
    
    diff = compare_schemas(sample_schema, str(schema_new_file))
    assert "email" in diff["new_columns"]
