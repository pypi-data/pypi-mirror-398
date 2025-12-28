"""
Unit tests for the core module.
"""

from pathlib import Path

import pytest

from structure_viewer.core import (
    DirectoryEntry,
    count_entries,
    iter_entries,
    walk_directory,
)


class TestDirectoryEntry:
    """Tests for the DirectoryEntry dataclass."""

    def test_file_entry(self, temp_project: Path) -> None:
        """Test creating a file entry."""
        entry = DirectoryEntry(
            name="main.py",
            path=temp_project / "src" / "main.py",
            is_dir=False,
            depth=2,
        )

        assert entry.name == "main.py"
        assert entry.is_dir is False
        assert entry.depth == 2
        assert entry.extension == ".py"
        assert entry.children == []

    def test_directory_entry(self, temp_project: Path) -> None:
        """Test creating a directory entry."""
        entry = DirectoryEntry(
            name="src",
            path=temp_project / "src",
            is_dir=True,
            depth=1,
        )

        assert entry.name == "src"
        assert entry.is_dir is True
        assert entry.extension == ""

    def test_repr(self, temp_project: Path) -> None:
        """Test string representation."""
        entry = DirectoryEntry(
            name="test.py",
            path=temp_project / "test.py",
            is_dir=False,
            depth=0,
        )

        assert "test.py" in repr(entry)
        assert "file" in repr(entry)


class TestWalkDirectory:
    """Tests for the walk_directory function."""

    def test_basic_walk(self, temp_project: Path) -> None:
        """Test basic directory walking."""
        result = walk_directory(temp_project)

        assert result.is_dir is True
        assert result.depth == 0
        assert len(result.children) > 0

    def test_excludes_git(self, temp_project: Path) -> None:
        """Test that .git is excluded by default."""
        result = walk_directory(temp_project)

        child_names = [c.name for c in result.children]
        assert ".git" not in child_names

    def test_excludes_node_modules(self, temp_project: Path) -> None:
        """Test that node_modules is excluded by default."""
        result = walk_directory(temp_project)

        child_names = [c.name for c in result.children]
        assert "node_modules" not in child_names

    def test_includes_src(self, temp_project: Path) -> None:
        """Test that src directory is included."""
        result = walk_directory(temp_project)

        child_names = [c.name for c in result.children]
        assert "src" in child_names

    def test_depth_limit(self, temp_nested_dir: Path) -> None:
        """Test depth limiting."""
        result = walk_directory(temp_nested_dir, max_depth=1)

        # Should include level1 but not deeper
        level1 = next((c for c in result.children if c.name == "level1"), None)
        assert level1 is not None
        assert level1.children == []  # No deeper scanning

    def test_depth_unlimited(self, temp_nested_dir: Path) -> None:
        """Test unlimited depth."""
        result = walk_directory(temp_nested_dir)

        # Should find the deep file
        all_entries = list(iter_entries(result))
        names = [e.name for e in all_entries]
        assert "deep.txt" in names

    def test_include_hidden(self, temp_project: Path) -> None:
        """Test including hidden files."""
        result = walk_directory(temp_project, include_hidden=True)

        child_names = [c.name for c in result.children]
        # .git should now be included
        assert ".git" in child_names

    def test_custom_exclusions(self, temp_project: Path) -> None:
        """Test custom exclusion patterns."""
        result = walk_directory(temp_project, exclusions={"src"})

        child_names = [c.name for c in result.children]
        assert "src" not in child_names

    def test_include_extensions(self, temp_mixed_extensions: Path) -> None:
        """Test filtering by included extensions."""
        result = walk_directory(temp_mixed_extensions, include_extensions={"py", "js"})

        file_names = [c.name for c in result.children if not c.is_dir]
        assert "script.py" in file_names
        assert "app.js" in file_names
        assert "style.css" not in file_names

    def test_exclude_extensions(self, temp_mixed_extensions: Path) -> None:
        """Test filtering by excluded extensions."""
        result = walk_directory(temp_mixed_extensions, exclude_extensions={"txt", "json"})

        file_names = [c.name for c in result.children if not c.is_dir]
        assert "script.py" in file_names
        assert "notes.txt" not in file_names
        assert "data.json" not in file_names

    def test_dirs_only(self, temp_project: Path) -> None:
        """Test showing only directories."""
        result = walk_directory(temp_project, dirs_only=True)

        all_entries = list(iter_entries(result))
        for entry in all_entries:
            if entry != result:  # Skip root
                assert entry.is_dir is True

    def test_nonexistent_directory(self) -> None:
        """Test error handling for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            walk_directory(Path("/nonexistent/path/123456"))

    def test_file_instead_of_directory(self, temp_project: Path) -> None:
        """Test error handling when given a file instead of directory."""
        file_path = temp_project / "README.md"
        with pytest.raises(NotADirectoryError):
            walk_directory(file_path)

    def test_empty_directory(self, temp_empty_dir: Path) -> None:
        """Test walking an empty directory."""
        result = walk_directory(temp_empty_dir)

        assert result.is_dir is True
        assert result.children == []


class TestIterEntries:
    """Tests for the iter_entries function."""

    def test_iteration(self, temp_project: Path) -> None:
        """Test iterating over all entries."""
        tree = walk_directory(temp_project)
        entries = list(iter_entries(tree))

        # Should have multiple entries
        assert len(entries) > 1

        # First entry should be the root
        assert entries[0] == tree


class TestCountEntries:
    """Tests for the count_entries function."""

    def test_count(self, temp_project: Path) -> None:
        """Test counting files and directories."""
        tree = walk_directory(temp_project)
        dirs, files = count_entries(tree)

        # At minimum we have src, tests directories and README.md, etc.
        assert dirs >= 2
        assert files >= 3

    def test_empty_count(self, temp_empty_dir: Path) -> None:
        """Test counting in empty directory."""
        tree = walk_directory(temp_empty_dir)
        dirs, files = count_entries(tree)

        assert dirs == 0  # Root is subtracted
        assert files == 0
