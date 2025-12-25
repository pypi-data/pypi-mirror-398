import argparse
import json
import sys
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.status import Status
from schema_sync import infer_schema, validate_data, compare_schemas

console = Console()

def main():
    parser = argparse.ArgumentParser(description="CSV/JSON Schema Sync: Manage evolving schemas.")
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
        with console.status(f"[bold green]Inferring schema from {args.data_file}...") as status:
            try:
                schema = infer_schema(args.data_file)
                output = json.dumps(schema, indent=2)
                syntax = Syntax(output, "json", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Inferred Schema", border_style="green"))
            except Exception as e:
                console.print(f"[bold red]Error inferring schema: {e}[/bold red]")
                sys.exit(1)

    elif args.command == "validate":
        with console.status(f"[bold blue]Validating {args.data_file} against {args.schema_file}...") as status:
            # Note: validata_data prints standard output, we might want to capture it or just let it print
            # for now let's just run it. Ideally validate_data should return result and we print.
            # But the current implementation prints errors inside.
            success = validate_data(args.data_file, args.schema_file)
            
            if success:
                console.print(Panel(f"[bold green]Validation Successful![/bold green]\nData in [bold]{args.data_file}[/bold] matches schema [bold]{args.schema_file}[/bold]", title="Success", border_style="green"))
            else:
                 console.print(Panel(f"[bold red]Validation Failed![/bold red]\nCheck output above for errors.", title="Failure", border_style="red"))
                 sys.exit(1)

    elif args.command == "compare":
        with console.status(f"[bold yellow]Comparing schemas...") as status:
            diff = compare_schemas(args.old_schema, args.new_schema)
            
            if not diff:
                 console.print("[bold red]Error comparing schemas or no differences found.[/bold red]")
                 return

            table = Table(title="Schema Comparison Result")
            table.add_column("Change Type", justify="center", style="cyan", no_wrap=True)
            table.add_column("Column Name", style="magenta")

            for col in diff.get("new_columns", []):
                table.add_row("[green]New Column[/green]", col)
            
            for col in diff.get("missing_columns", []):
                 table.add_row("[red]Missing Column[/red]", col)
            
            if not diff["new_columns"] and not diff["missing_columns"]:
                 console.print(Panel("[bold green]Schemas are identical![/bold green]", title="Comparison", border_style="green"))
            else:
                console.print(table)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
