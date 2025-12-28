"""
Core directory traversal logic for structure-viewer.
"""

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List, Optional, Set

from structure_viewer.config import DEFAULT_EXCLUSIONS


@dataclass
class DirectoryEntry:
    """
    Represents a single entry (file or directory) in the directory tree.

    Attributes:
        name: The name of the file or directory.
        path: The full path to the entry.
        is_dir: Whether this entry is a directory.
        depth: The depth level in the tree (0 for root).
        children: Child entries if this is a directory.
        is_last: Whether this is the last item at its level.
    """
    name: str
    path: Path
    is_dir: bool
    depth: int
    children: List["DirectoryEntry"] = field(default_factory=list)
    is_last: bool = False

    @property
    def extension(self) -> str:
        """Get the file extension (including the dot)."""
        if self.is_dir:
            return ""
        return Path(self.name).suffix

    def __repr__(self) -> str:
        entry_type = "dir" if self.is_dir else "file"
        return f"DirectoryEntry({self.name!r}, {entry_type}, depth={self.depth})"


def _should_exclude(
    name: str,
    exclusions: Set[str],
    include_hidden: bool = False,
) -> bool:
    """
    Check if a file or directory should be excluded.

    Args:
        name: The name of the file or directory.
        exclusions: Set of patterns to exclude.
        include_hidden: Whether to include hidden files (starting with .).

    Returns:
        True if the entry should be excluded, False otherwise.
    """
    is_hidden = name.startswith(".")

    # Handle hidden files
    if is_hidden:
        if include_hidden:
            # When include_hidden is True, don't exclude hidden files at all
            # (they explicitly want to see hidden files)
            return False
        else:
            # When include_hidden is False, exclude hidden files
            # except for some important dotfiles
            if name not in {".github", ".gitignore", ".env.example"}:
                return True

    # For non-hidden files, check exclusion patterns
    # Check exact matches
    if name in exclusions:
        return True

    # Check glob patterns
    for pattern in exclusions:
        if "*" in pattern and fnmatch.fnmatch(name, pattern):
            return True

    return False


def _filter_extensions(
    name: str,
    is_dir: bool,
    include_extensions: Optional[Set[str]] = None,
    exclude_extensions: Optional[Set[str]] = None,
) -> bool:
    """
    Check if a file should be filtered based on extensions.

    Args:
        name: The file name.
        is_dir: Whether this is a directory.
        include_extensions: If set, only include files with these extensions.
        exclude_extensions: Exclude files with these extensions.

    Returns:
        True if the entry should be included, False if filtered out.
    """
    # Directories are always included (unless excluded by other rules)
    if is_dir:
        return True

    ext = Path(name).suffix.lower().lstrip(".")

    # Check include filter (whitelist)
    if include_extensions is not None:
        if ext not in include_extensions:
            return False

    # Check exclude filter (blacklist)
    if exclude_extensions is not None:
        if ext in exclude_extensions:
            return False

    return True


def walk_directory(
    root: Path,
    max_depth: Optional[int] = None,
    exclusions: Optional[Set[str]] = None,
    include_hidden: bool = False,
    include_extensions: Optional[Set[str]] = None,
    exclude_extensions: Optional[Set[str]] = None,
    dirs_only: bool = False,
) -> DirectoryEntry:
    """
    Walk a directory tree and build a structured representation.

    Args:
        root: The root directory to walk.
        max_depth: Maximum depth to traverse (None for unlimited).
        exclusions: Patterns to exclude (defaults to DEFAULT_EXCLUSIONS).
        include_hidden: Whether to include hidden files.
        include_extensions: Only include files with these extensions.
        exclude_extensions: Exclude files with these extensions.
        dirs_only: Only include directories.

    Returns:
        A DirectoryEntry representing the root with nested children.

    Raises:
        FileNotFoundError: If the root directory doesn't exist.
        NotADirectoryError: If root is not a directory.
        PermissionError: If access to the directory is denied.
    """
    root = Path(root).resolve()

    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    if exclusions is None:
        exclusions = set(DEFAULT_EXCLUSIONS)
    else:
        exclusions = set(exclusions) | set(DEFAULT_EXCLUSIONS)

    def _walk(
        path: Path,
        depth: int,
    ) -> Optional[DirectoryEntry]:
        """Recursive helper to walk the directory tree."""
        # Check depth limit
        if max_depth is not None and depth > max_depth:
            return None

        try:
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            # Return empty entry for inaccessible directories
            return DirectoryEntry(
                name=path.name,
                path=path,
                is_dir=True,
                depth=depth,
                children=[],
            )

        children: List[DirectoryEntry] = []

        for item in items:
            name = item.name
            is_dir = item.is_dir()

            # Apply exclusion rules
            if _should_exclude(name, exclusions, include_hidden):
                continue

            # Apply extension filters
            if not _filter_extensions(
                name, is_dir, include_extensions, exclude_extensions
            ):
                continue

            # Skip files if dirs_only
            if dirs_only and not is_dir:
                continue

            if is_dir:
                # Recursively process subdirectory
                child = _walk(item, depth + 1)
                if child is not None:
                    children.append(child)
            else:
                children.append(DirectoryEntry(
                    name=name,
                    path=item,
                    is_dir=False,
                    depth=depth + 1,
                ))

        # Mark the last child
        if children:
            children[-1].is_last = True

        return DirectoryEntry(
            name=path.name,
            path=path,
            is_dir=True,
            depth=depth,
            children=children,
        )

    result = _walk(root, 0)
    if result is None:
        # This shouldn't happen for depth 0, but handle it anyway
        result = DirectoryEntry(
            name=root.name,
            path=root,
            is_dir=True,
            depth=0,
            children=[],
        )

    result.is_last = True
    return result


def iter_entries(entry: DirectoryEntry) -> Generator[DirectoryEntry, None, None]:
    """
    Iterate over all entries in a directory tree (depth-first).

    Args:
        entry: The root DirectoryEntry to iterate from.

    Yields:
        Each DirectoryEntry in depth-first order.
    """
    yield entry
    for child in entry.children:
        yield from iter_entries(child)


def count_entries(entry: DirectoryEntry) -> tuple:
    """
    Count the number of files and directories in a tree.

    Args:
        entry: The root DirectoryEntry to count from.

    Returns:
        A tuple of (directories, files).
    """
    dirs = 0
    files = 0

    for e in iter_entries(entry):
        if e.is_dir:
            dirs += 1
        else:
            files += 1

    # Subtract 1 from dirs because we count the root
    return (dirs - 1, files)
