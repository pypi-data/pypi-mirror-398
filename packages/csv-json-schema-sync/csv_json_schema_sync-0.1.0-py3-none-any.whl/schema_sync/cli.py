import argparse
import json
import sys
from schema_sync import infer_schema, validate_data, compare_schemas

def main():
    parser = argparse.ArgumentParser(description="Schema Sync: Manage continuously evolving schemas.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Infer command
    parser_infer = subparsers.add_parser("infer", help="Infer schema from data file")
    parser_infer.add_argument("data_file", help="Path to CSV/JSON data file")

    # Validate command
    parser_validate = subparsers.add_parser("validate", help="Validate data against schema")
    parser_validate.add_argument("data_file", help="Path to CSV/JSON data file")
    parser_validate.add_argument("schema_file", help="Path to JSON schema file")

    # Compare command
    parser_compare = subparsers.add_parser("compare", help="Compare two schemas")
    parser_compare.add_argument("old_schema", help="Path to old schema file")
    parser_compare.add_argument("new_schema", help="Path to new schema file")

    args = parser.parse_args()

    if args.command == "infer":
        try:
            schema = infer_schema(args.data_file)
            print(json.dumps(schema, indent=2))
        except Exception as e:
            print(f"Error inferring schema: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "validate":
        success = validate_data(args.data_file, args.schema_file)
        if not success:
            sys.exit(1)

    elif args.command == "compare":
        diff = compare_schemas(args.old_schema, args.new_schema)
        if diff:
            print(json.dumps(diff, indent=2))
        else:
             print("Error comparing schemas or no differences found.", file=sys.stderr)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
