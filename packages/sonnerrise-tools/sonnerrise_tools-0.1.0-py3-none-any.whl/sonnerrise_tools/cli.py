"""CLI for Sonnerrise Tools."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def export_command(args: argparse.Namespace) -> int:
    """Handle export command."""
    from sonnerrise_core import get_database, load_config

    from sonnerrise_tools import ExportService
    from sonnerrise_tools.schemas import ExportOptions

    config = load_config()
    db = get_database(config)

    with db.session() as session:
        exporter = ExportService(session, config)

        # Build export options
        options = ExportOptions(pretty_print=not args.compact)

        # Handle --only flag
        if args.only:
            entities = [e.strip().lower() for e in args.only.split(",")]
            options.include_personas = "personas" in entities
            options.include_definitions = "definitions" in entities
            options.include_tracks = "tracks" in entities
            options.include_promos = "promos" in entities

        backup = exporter.export_all(args.output, format=args.format, options=options)

        print(f"Exported {backup.counts.total} records to {args.output}")
        print(f"  Personas: {backup.counts.personas}")
        print(f"  Definitions: {backup.counts.definitions}")
        print(f"  Definition Links: {backup.counts.definition_links}")
        print(f"  Tracks: {backup.counts.tracks}")
        print(f"  Track Links: {backup.counts.track_links}")
        print(f"  Track Events: {backup.counts.track_events}")
        print(f"  Promos: {backup.counts.promos}")
        print(f"  Promo Links: {backup.counts.promo_links}")

    return 0


def import_command(args: argparse.Namespace) -> int:
    """Handle import command."""
    from sonnerrise_core import get_database, load_config

    from sonnerrise_tools import ImportService
    from sonnerrise_tools.schemas import ImportOptions

    config = load_config()
    db = get_database(config)

    with db.session() as session:
        importer = ImportService(session, config)

        options = ImportOptions(
            skip_existing=args.skip_existing,
            create_tables=args.create_tables,
            clear_existing=args.clear_existing,
        )

        result = importer.import_all(args.input, options=options)

        if result.success:
            print(f"Successfully imported {result.imported.total} records")
            print(f"  Personas: {result.imported.personas}")
            print(f"  Definitions: {result.imported.definitions}")
            print(f"  Definition Links: {result.imported.definition_links}")
            print(f"  Tracks: {result.imported.tracks}")
            print(f"  Track Links: {result.imported.track_links}")
            print(f"  Track Events: {result.imported.track_events}")
            print(f"  Promos: {result.imported.promos}")
            print(f"  Promo Links: {result.imported.promo_links}")

            if result.skipped.total > 0:
                print(f"\nSkipped {result.skipped.total} existing records")

            if result.has_warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")

            return 0
        else:
            print("Import failed with errors:")
            for error in result.errors:
                print(f"  - {error}")
            return 1


def info_command(args: argparse.Namespace) -> int:
    """Handle info command."""
    from sonnerrise_core import get_database, load_config

    from sonnerrise_tools import ImportService

    config = load_config()
    db = get_database(config)

    with db.session() as session:
        importer = ImportService(session, config)
        info = importer.get_backup_info(args.input)

        print(f"Backup Information: {args.input}")
        print(f"  Version: {info.version}")
        print(f"  Created: {info.created_at}")
        print(f"  File Size: {info.file_size:,} bytes")
        print(f"  Compatible: {'Yes' if info.is_compatible else 'No'}")
        print(f"\nRecord Counts:")
        print(f"  Personas: {info.counts.personas}")
        print(f"  Definitions: {info.counts.definitions}")
        print(f"  Definition Links: {info.counts.definition_links}")
        print(f"  Tracks: {info.counts.tracks}")
        print(f"  Track Links: {info.counts.track_links}")
        print(f"  Track Events: {info.counts.track_events}")
        print(f"  Promos: {info.counts.promos}")
        print(f"  Promo Links: {info.counts.promo_links}")
        print(f"  Total: {info.counts.total}")

    return 0


def validate_command(args: argparse.Namespace) -> int:
    """Handle validate command."""
    from sonnerrise_core import get_database, load_config

    from sonnerrise_tools import ImportService

    config = load_config()
    db = get_database(config)

    with db.session() as session:
        importer = ImportService(session, config)
        result = importer.validate(args.input)

        if result.success:
            print(f"Backup is valid: {args.input}")
            print(f"  Total records: {result.total_records}")
            return 0
        else:
            print(f"Backup validation failed: {args.input}")
            for error in result.errors:
                print(f"  - {error}")
            return 1


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="sonnerrise-tools",
        description="Database export/import tools for Sonnerrise",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export database to file")
    export_parser.add_argument("output", help="Output file path")
    export_parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )
    export_parser.add_argument(
        "--only",
        help="Export only specific entities (comma-separated: personas,definitions,tracks,promos)",
    )
    export_parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact output (no pretty printing)",
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import data from file")
    import_parser.add_argument("input", help="Input file path")
    import_parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip records that already exist",
    )
    import_parser.add_argument(
        "--create-tables",
        action="store_true",
        default=True,
        help="Create missing tables (default: true)",
    )
    import_parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing data before import",
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show backup file information")
    info_parser.add_argument("input", help="Backup file path")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate backup file")
    validate_parser.add_argument("input", help="Backup file path")

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "export": export_command,
        "import": import_command,
        "info": info_command,
        "validate": validate_command,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
