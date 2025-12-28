"""
Output formatters for structure-viewer.

Supports multiple output formats:
- Tree: ASCII art tree representation
- JSON: Machine-readable JSON format
- YAML: Human-readable YAML format (requires PyYAML)
"""

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from structure_viewer.colors import ColorPrinter, default_printer

if TYPE_CHECKING:
    from structure_viewer.core import DirectoryEntry


# Tree drawing characters
TREE_CHARS = {
    "branch": "├── ",
    "last_branch": "└── ",
    "vertical": "│   ",
    "space": "    ",
}


def _build_tree_lines(
    entry: "DirectoryEntry",
    prefix: str = "",
    is_root: bool = True,
    color_printer: Optional[ColorPrinter] = None,
) -> List[str]:
    """
    Build tree lines recursively.

    Args:
        entry: The directory entry to format.
        prefix: The prefix string for indentation.
        is_root: Whether this is the root entry.
        color_printer: Optional color printer for colorized output.

    Returns:
        A list of formatted lines.
    """
    lines: List[str] = []
    printer = color_printer or default_printer

    if is_root:
        # Root directory with trailing slash
        name = printer.directory(f"{entry.name}/") if printer.enabled else f"{entry.name}/"
        lines.append(name)

    children = entry.children
    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        connector = TREE_CHARS["last_branch"] if is_last else TREE_CHARS["branch"]

        # Format the connector
        if printer.enabled:
            connector_str = printer.connector(connector)
        else:
            connector_str = connector

        # Format the name
        if child.is_dir:
            name = printer.directory(f"{child.name}/") if printer.enabled else f"{child.name}/"
        else:
            name = (
                printer.file(child.name, child.extension)
                if printer.enabled
                else child.name
            )

        lines.append(f"{prefix}{connector_str}{name}")

        # Recurse into directories
        if child.is_dir and child.children:
            extension = TREE_CHARS["space"] if is_last else TREE_CHARS["vertical"]
            if printer.enabled:
                extension_str = printer.connector(extension)
            else:
                extension_str = extension

            child_lines = _build_tree_lines(
                child,
                prefix=prefix + extension_str,
                is_root=False,
                color_printer=printer,
            )
            lines.extend(child_lines)

    return lines


def format_tree(
    entry: "DirectoryEntry",
    colorize: bool = True,
) -> str:
    """
    Format a directory tree as ASCII art.

    Args:
        entry: The root directory entry to format.
        colorize: Whether to include ANSI color codes.

    Returns:
        A string containing the formatted tree.

    Example output:
        my-project/
        ├── src/
        │   ├── main.py
        │   └── utils.py
        ├── tests/
        │   └── test_main.py
        └── README.md
    """
    printer = ColorPrinter(enabled=colorize)
    lines = _build_tree_lines(entry, color_printer=printer)
    return "\n".join(lines)


def _entry_to_dict(entry: "DirectoryEntry") -> Dict[str, Any]:
    """Convert a DirectoryEntry to a dictionary for JSON/YAML output."""
    result: Dict[str, Any] = {
        "name": entry.name,
        "type": "directory" if entry.is_dir else "file",
        "path": str(entry.path),
    }

    if entry.is_dir and entry.children:
        result["children"] = [_entry_to_dict(child) for child in entry.children]

    if not entry.is_dir:
        result["extension"] = entry.extension or None

    return result


def format_json(
    entry: "DirectoryEntry",
    pretty: bool = True,
) -> str:
    """
    Format a directory tree as JSON.

    Args:
        entry: The root directory entry to format.
        pretty: Whether to format with indentation.

    Returns:
        A JSON string representation of the tree.
    """
    data = _entry_to_dict(entry)
    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    return json.dumps(data, ensure_ascii=False)


def format_yaml(entry: "DirectoryEntry") -> str:
    """
    Format a directory tree as YAML.

    Args:
        entry: The root directory entry to format.

    Returns:
        A YAML string representation of the tree.

    Raises:
        ImportError: If PyYAML is not installed.
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as e:
        raise ImportError(
            "PyYAML is required for YAML output. "
            "Install it with: pip install structure-viewer[yaml]"
        ) from e

    data = _entry_to_dict(entry)
    return str(yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False))


def get_formatter(format_name: str) -> Any:
    """
    Get a formatter function by name.

    Args:
        format_name: One of 'tree', 'json', 'yaml'.

    Returns:
        The formatter function.

    Raises:
        ValueError: If the format name is unknown.
    """
    formatters = {
        "tree": format_tree,
        "json": format_json,
        "yaml": format_yaml,
    }

    if format_name not in formatters:
        valid = ", ".join(formatters.keys())
        raise ValueError(f"Unknown format '{format_name}'. Valid formats: {valid}")

    return formatters[format_name]
