"""
Structure Viewer - A powerful CLI tool to visualize project directory structure.

This package provides a command-line interface for displaying directory trees
with smart exclusions, multiple output formats, and colorized output.
"""

from structure_viewer.core import DirectoryEntry, walk_directory
from structure_viewer.formatters import format_json, format_tree

__version__ = "1.0.0"
__author__ = "Structure Viewer Contributors"

__all__ = [
    "__version__",
    "DirectoryEntry",
    "walk_directory",
    "format_tree",
    "format_json",
]
