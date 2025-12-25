"""Command-line interface for sonnerrise-core."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sonnerrise_core import __version__
from sonnerrise_core.config import Config, load_config


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sonnerrise-core",
        description="Sonnerrise Core - Configuration and database utilities",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init-config command
    init_parser = subparsers.add_parser(
        "init-config",
        help="Create a default configuration file",
    )
    init_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("sonnerrise.yaml"),
        help="Output path for configuration file (default: sonnerrise.yaml)",
    )
    init_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing file",
    )

    # test-db command
    subparsers.add_parser(
        "test-db",
        help="Test database connection",
    )

    # init-db command
    subparsers.add_parser(
        "init-db",
        help="Initialize database tables",
    )

    # show-config command
    subparsers.add_parser(
        "show-config",
        help="Show current configuration",
    )

    return parser


def cmd_init_config(args: argparse.Namespace) -> int:
    """Create a default configuration file."""
    output_path: Path = args.output

    if output_path.exists() and not args.force:
        print(f"Error: File already exists: {output_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        return 1

    config = Config()
    config.to_yaml(output_path)
    print(f"Created configuration file: {output_path}")
    return 0


def cmd_test_db(args: argparse.Namespace) -> int:
    """Test database connection."""
    from sonnerrise_core.database import get_database

    config = load_config(args.config)
    print(f"Testing connection to {config.database.plugin} database...")
    print(f"  Host: {config.database.host}:{config.database.port}")
    print(f"  Database: {config.database.database}")
    print(f"  User: {config.database.user}")

    try:
        db = get_database(config)
        if db.test_connection():
            print("Connection successful!")
            return 0
        else:
            print("Connection failed!", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        return 1


def cmd_init_db(args: argparse.Namespace) -> int:
    """Initialize database tables."""
    from sonnerrise_core.database import get_database

    config = load_config(args.config)
    print(f"Initializing database tables in {config.database.database}...")

    try:
        db = get_database(config)
        db.create_tables()
        print("Database tables created successfully!")
        return 0
    except Exception as e:
        print(f"Error creating tables: {e}", file=sys.stderr)
        return 1


def cmd_show_config(args: argparse.Namespace) -> int:
    """Show current configuration."""
    import yaml

    config = load_config(args.config)
    print(yaml.safe_dump(config.model_dump(), default_flow_style=False))
    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "init-config": cmd_init_config,
        "test-db": cmd_test_db,
        "init-db": cmd_init_db,
        "show-config": cmd_show_config,
    }

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
