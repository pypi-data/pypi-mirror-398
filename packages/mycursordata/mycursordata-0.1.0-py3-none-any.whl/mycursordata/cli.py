#!/usr/bin/env python3
"""
MyCursorData CLI

Command-line interface for extracting Cursor IDE conversation history.
"""

import argparse
import logging
import sys
import shutil
from pathlib import Path

from . import __version__
from .discovery import (
    discover_cursor_databases,
    get_primary_database,
    get_default_cursor_paths,
)
from .parser import CursorDataParser


def setup_logging(verbose: bool = False):
    """Configure logging with pretty formatting."""
    level = logging.DEBUG if verbose else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(message)s",
        datefmt="%H:%M:%S",
    )

    # Setup handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Also configure our package logger
    pkg_logger = logging.getLogger("mycursordata")
    pkg_logger.setLevel(level)


def print_banner():
    """Print the tool banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🔍 MyCursorData - Extract Your Cursor Conversation History      ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def cmd_export(args):
    """Export conversations to text files."""
    logger = logging.getLogger(__name__)

    output_dir = Path(args.output)

    # Find database
    if args.database:
        db_path = Path(args.database)
        if not db_path.exists():
            logger.error(f"❌ Database file not found: {db_path}")
            return 1
    else:
        logger.info("🔍 Searching for Cursor databases...")
        db_path = get_primary_database()
        if not db_path:
            logger.error("❌ No Cursor database found!")
            logger.error("   Try specifying a path with --database")
            return 1

    logger.info(f"📂 Using database: {db_path}")
    logger.info(f"📁 Output directory: {output_dir}")

    # Parse and export
    try:
        with CursorDataParser(db_path) as parser:
            if args.summary:
                parser.print_summary()

            total = parser.export_all(output_dir)

            if total > 0:
                logger.info(f"\n✅ Successfully exported {total} conversations!")
            else:
                logger.warning("\n⚠️  No conversations found to export.")

            return 0
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_discover(args):
    """Discover and list available databases."""
    logger = logging.getLogger(__name__)

    logger.info("🔍 Searching for Cursor databases...\n")

    # Show default paths being checked
    logger.info("Default search paths:")
    for path in get_default_cursor_paths():
        status = "✅" if path.exists() else "❌"
        logger.info(f"  {status} {path}")

    logger.info("")

    # Find all databases
    databases = discover_cursor_databases(include_workspace_dbs=args.include_workspace)

    if not databases:
        logger.warning("⚠️  No databases found!")
        return 1

    logger.info(f"\n📊 Found {len(databases)} database(s):\n")

    for i, db in enumerate(databases, 1):
        db_path = db["path"]
        db_type = db["type"]
        source = db["source"]

        # Get basic stats
        try:
            with CursorDataParser(db_path) as parser:
                stats = parser.get_bubble_stats()
                conversations = stats["conversations"]
                messages = stats["total_messages"]
        except Exception:
            conversations = "?"
            messages = "?"

        print(f"  {i}. [{db_type.upper()}] {source}")
        print(f"     Path: {db_path}")
        print(f"     Conversations: {conversations}, Messages: {messages}")
        print()

    return 0


def cmd_info(args):
    """Show database information and statistics."""
    logger = logging.getLogger(__name__)

    if args.database:
        db_path = Path(args.database)
    else:
        db_path = get_primary_database()
        if not db_path:
            logger.error("❌ No Cursor database found!")
            return 1

    logger.info(f"📂 Database: {db_path}")

    try:
        with CursorDataParser(db_path) as parser:
            parser.print_summary()
        return 0
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="mycursordata",
        description="Extract and export your Cursor IDE conversation history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mycursordata ~/cursor-export         Export to ~/cursor-export
  mycursordata . --summary             Export to current dir with stats
  mycursordata discover                List all found databases
  mycursordata info                    Show database statistics
  mycursordata export ./out -d /path/to/state.vscdb  Use specific DB
""",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose/debug output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        metavar="COMMAND",
    )

    # Export command (default when just path is given)
    export_parser = subparsers.add_parser(
        "export",
        help="Export conversations to text files",
        aliases=["e"],
    )
    export_parser.add_argument(
        "output",
        type=str,
        help="Output directory for exported files",
    )
    export_parser.add_argument(
        "-d",
        "--database",
        type=str,
        help="Path to state.vscdb file (auto-detected if not specified)",
    )
    export_parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="Print database summary before exporting",
    )
    export_parser.set_defaults(func=cmd_export)

    # Discover command
    discover_parser = subparsers.add_parser(
        "discover",
        help="Discover available Cursor databases",
        aliases=["d", "find"],
    )
    discover_parser.add_argument(
        "--include-workspace",
        action="store_true",
        help="Also search for per-workspace databases",
    )
    discover_parser.set_defaults(func=cmd_discover)

    # Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show database statistics",
        aliases=["i", "stats"],
    )
    info_parser.add_argument(
        "-d",
        "--database",
        type=str,
        help="Path to state.vscdb file (auto-detected if not specified)",
    )
    info_parser.set_defaults(func=cmd_info)

    # Handle default case: if first arg looks like a path, treat as export
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        known_commands = {
            "export",
            "e",
            "discover",
            "d",
            "find",
            "info",
            "i",
            "stats",
            "-h",
            "--help",
            "-v",
            "--verbose",
            "--version",
        }

        if first_arg not in known_commands and not first_arg.startswith("-"):
            # Looks like a path, insert "export" command
            sys.argv.insert(1, "export")

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    setup_logging(getattr(args, "verbose", False))

    # Print banner
    print_banner()

    # Handle case where no command was given
    if args.command is None:
        parser.print_help()
        return 0

    # Run the command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
