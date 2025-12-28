"""
Command-line interface for structure-viewer.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set

from structure_viewer import __version__
from structure_viewer.colors import ColorPrinter
from structure_viewer.core import count_entries, walk_directory
from structure_viewer.formatters import format_json, format_tree, format_yaml


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Optional list of arguments (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="structure",
        description="Visualize project directory structure with smart exclusions.",
        epilog="Examples:\n"
               "  structure                    # Current directory\n"
               "  structure ./src -d 2         # src folder, max 2 levels\n"
               "  structure -f json            # Output as JSON\n"
               "  structure -e '*.log' -e tmp  # Exclude additional patterns\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-d", "--depth",
        type=int,
        metavar="N",
        help="Maximum depth to display (default: unlimited)",
    )

    parser.add_argument(
        "-e", "--exclude",
        action="append",
        metavar="PATTERN",
        help="Additional patterns to exclude (can be repeated)",
    )

    parser.add_argument(
        "-I", "--include-ext",
        action="append",
        metavar="EXT",
        help="Only show files with these extensions (can be repeated)",
    )

    parser.add_argument(
        "-E", "--exclude-ext",
        action="append",
        metavar="EXT",
        help="Exclude files with these extensions (can be repeated)",
    )

    parser.add_argument(
        "-f", "--format",
        choices=["tree", "json", "yaml"],
        default="tree",
        help="Output format (default: tree)",
    )

    parser.add_argument(
        "-a", "--all",
        action="store_true",
        dest="show_hidden",
        help="Show hidden files and directories",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colorized output",
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only show directories (no files)",
    )

    parser.add_argument(
        "-s", "--stats",
        action="store_true",
        help="Show statistics (file/directory count)",
    )

    return parser.parse_args(args)


def _normalize_extensions(extensions: Optional[List[str]]) -> Optional[Set[str]]:
    """Normalize extension list by removing leading dots and converting to lowercase."""
    if extensions is None:
        return None
    return {ext.lstrip(".").lower() for ext in extensions}


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Optional list of arguments (for testing).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parsed = parse_args(args)
    printer = ColorPrinter(enabled=not parsed.no_color)

    # Resolve the target directory
    target = Path(parsed.directory).resolve()

    try:
        # Build the directory tree
        tree = walk_directory(
            root=target,
            max_depth=parsed.depth,
            exclusions=set(parsed.exclude) if parsed.exclude else None,
            include_hidden=parsed.show_hidden,
            include_extensions=_normalize_extensions(parsed.include_ext),
            exclude_extensions=_normalize_extensions(parsed.exclude_ext),
            dirs_only=parsed.quiet,
        )

        # Format and print the output
        if parsed.format == "tree":
            output = format_tree(tree, colorize=not parsed.no_color)
        elif parsed.format == "json":
            output = format_json(tree, pretty=True)
        elif parsed.format == "yaml":
            try:
                output = format_yaml(tree)
            except ImportError as e:
                print(printer.error(str(e)), file=sys.stderr)
                return 1
        else:
            output = format_tree(tree, colorize=not parsed.no_color)

        print(output)

        # Print statistics if requested
        if parsed.stats:
            dirs, files = count_entries(tree)
            stats_line = f"\n{dirs} directories, {files} files"
            if printer.enabled:
                stats_line = printer.colorize(stats_line, "dim")
            print(stats_line)

        return 0

    except FileNotFoundError as e:
        print(printer.error(f"Error: {e}"), file=sys.stderr)
        return 1
    except NotADirectoryError as e:
        print(printer.error(f"Error: {e}"), file=sys.stderr)
        return 1
    except PermissionError as e:
        print(printer.error(f"Error: Permission denied - {e}"), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
