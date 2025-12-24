"""Command-line entry point for Deflatable."""

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine

from deflatable import schema
from deflatable.app import Deflatable
from deflatable.config import DeflatableConfig
from deflatable.validate import validate_config


def cmd_init(args):
    """
    Create a minimal YAML config file for a database.

    Args:
        args: Parsed arguments with config path and database URL
    """
    yaml_path = Path(args.config)
    db_url = args.database

    if yaml_path.exists():
        print(f"Error: Config file already exists: {yaml_path}", file=sys.stderr)
        sys.exit(1)

    # Validate that a proper SQLAlchemy URL was provided
    if "://" not in db_url:
        print(
            "Error: Database must be a SQLAlchemy URL (e.g., sqlite:///path.db, postgresql://...)",
            file=sys.stderr,
        )
        print("\nExamples:", file=sys.stderr)
        print("  deflatable init config.yaml sqlite:///database.db", file=sys.stderr)
        print(
            "  deflatable init config.yaml postgresql://user:pass@localhost/dbname",
            file=sys.stderr,
        )
        print("  deflatable init config.yaml duckdb:///data.duckdb", file=sys.stderr)
        sys.exit(1)

    # Test database connection using SQLAlchemy
    try:
        engine = create_engine(db_url)
        tables = schema.get_tables(engine)
        engine.dispose()
    except Exception as e:
        print(f"Error: Cannot connect to database: {e}", file=sys.stderr)
        sys.exit(1)

    config_content = f"""database: {db_url}

# Views will be auto-created on first run with default settings.
# You can add custom views here, for example:
#
# views:
#   your_table_name:
#     active_view: All
#     views:
#       All:
#         visible_fields: [column1, column2, column3]
#         sort_config: []
#
#       "Custom View":
#         visible_fields: [column1, column2]
#         grouping: column3
#         sort_config: [[column1, asc]]
"""

    yaml_path.write_text(config_content)
    print(f"✓ Created config file: {yaml_path}")
    print(f"  Database: {db_url}")
    print(f"  Tables: {', '.join(tables)}")
    print(f"\nRun: deflatable {yaml_path}")


def cmd_validate(args):
    """
    Validate a config file.

    Args:
        args: Parsed arguments with config path, format, and quiet flag
    """
    result = validate_config(args.config)

    # Quiet mode: only exit codes, no output
    if args.quiet:
        sys.exit(0 if result.is_valid else 1)

    # JSON format
    if args.format == "json":
        print(result.to_json())
        sys.exit(0 if result.is_valid else 1)

    # Human-readable format (default)
    if result.is_valid and not result.has_warnings:
        print(f"✓ Config is valid: {args.config}")
        sys.exit(0)
    elif result.is_valid and result.has_warnings:
        print(f"✓ Config is valid: {args.config}")
        print()
        print(result.format())
        sys.exit(0)
    else:
        print(f"✗ Config validation failed: {args.config}")
        print()
        print(result.format())
        sys.exit(1)


def cmd_run(args):
    """
    Run the Deflatable TUI application.

    Args:
        args: Parsed arguments with config path
    """
    input_path = Path(args.config)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        print("\nTo create a config file:", file=sys.stderr)
        print(f"  deflatable init {input_path} <database>", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"Error: Not a file: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Check if it's a YAML file
    if input_path.suffix not in [".yaml", ".yml"]:
        print("Error: File must be a YAML config file (.yaml or .yml)", file=sys.stderr)
        print("\nTo create a config file:", file=sys.stderr)
        print("  deflatable init <config.yaml> <database-url>", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  deflatable init config.yaml sqlite:///database.db", file=sys.stderr)
        print(
            "  deflatable init config.yaml postgresql://user:pass@localhost/dbname",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        config = DeflatableConfig(str(input_path))
        app = Deflatable(config=config)
        app.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Entry point for deflatable command."""
    parser = argparse.ArgumentParser(
        prog="deflatable",
        description="A TUI for browsing databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new config file from a SQLite database
  deflatable init myconfig.yaml sqlite:///mydata.db

  # Create a new config file from a PostgreSQL database
  deflatable init myconfig.yaml postgresql://user:pass@localhost/db

  # Create a new config file from a DuckDB database
  deflatable init myconfig.yaml duckdb:///mydata.duckdb

  # Run the TUI
  deflatable myconfig.yaml

  # Validate a config file
  deflatable validate myconfig.yaml
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    parser_init = subparsers.add_parser(
        "init", help="Create a new config file for a database"
    )
    parser_init.add_argument("config", help="Path to config file to create (.yaml)")
    parser_init.add_argument(
        "database",
        help="SQLAlchemy database URL (e.g., sqlite:///db.db, postgresql://...)",
    )
    parser_init.set_defaults(func=cmd_init)

    # Validate command
    parser_validate = subparsers.add_parser("validate", help="Validate a config file")
    parser_validate.add_argument("config", help="Path to config file to validate")
    parser_validate.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    parser_validate.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode: only exit codes, no output",
    )
    parser_validate.set_defaults(func=cmd_validate)

    # If no subcommand given, check if first arg is a config file (backward compat)
    if len(sys.argv) > 1 and sys.argv[1] not in ["init", "validate", "-h", "--help"]:
        # Treat as direct config file path (backward compatibility)
        args = argparse.Namespace(config=sys.argv[1], command="run")
        cmd_run(args)
    else:
        # Parse normally
        args = parser.parse_args()

        if args.command is None:
            parser.print_help()
            sys.exit(1)

        # Call the appropriate command function
        args.func(args)


if __name__ == "__main__":
    main()
