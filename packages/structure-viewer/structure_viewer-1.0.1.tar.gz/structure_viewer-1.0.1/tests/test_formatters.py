"""
Unit tests for the formatters module.
"""

import json
from pathlib import Path

import pytest

from structure_viewer.core import walk_directory
from structure_viewer.formatters import format_json, format_tree, format_yaml


class TestTreeFormatter:
    """Tests for the tree formatter."""

    def test_basic_format(self, temp_project: Path) -> None:
        """Test basic tree formatting."""
        tree = walk_directory(temp_project)
        output = format_tree(tree, colorize=False)

        # Should contain the root directory
        assert temp_project.name in output

        # Should contain tree characters
        assert "├── " in output or "└── " in output

    def test_contains_files(self, temp_project: Path) -> None:
        """Test that files are included in output."""
        tree = walk_directory(temp_project)
        output = format_tree(tree, colorize=False)

        assert "README.md" in output
        assert "main.py" in output

    def test_contains_directories(self, temp_project: Path) -> None:
        """Test that directories are included with trailing slash."""
        tree = walk_directory(temp_project)
        output = format_tree(tree, colorize=False)

        assert "src/" in output
        assert "tests/" in output

    def test_no_color_output(self, temp_project: Path) -> None:
        """Test that no ANSI codes are present when colorize=False."""
        tree = walk_directory(temp_project)
        output = format_tree(tree, colorize=False)

        # ANSI escape codes start with \x1b[ or \033[
        assert "\x1b[" not in output
        assert "\033[" not in output

    def test_empty_directory(self, temp_empty_dir: Path) -> None:
        """Test formatting an empty directory."""
        tree = walk_directory(temp_empty_dir)
        output = format_tree(tree, colorize=False)

        # Should just show the root
        lines = output.strip().split("\n")
        assert len(lines) == 1


class TestJsonFormatter:
    """Tests for the JSON formatter."""

    def test_valid_json(self, temp_project: Path) -> None:
        """Test that output is valid JSON."""
        tree = walk_directory(temp_project)
        output = format_json(tree)

        # Should parse without error
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_json_structure(self, temp_project: Path) -> None:
        """Test JSON structure."""
        tree = walk_directory(temp_project)
        output = format_json(tree)
        data = json.loads(output)

        assert "name" in data
        assert "type" in data
        assert data["type"] == "directory"
        assert "children" in data

    def test_json_children(self, temp_project: Path) -> None:
        """Test that children are properly nested."""
        tree = walk_directory(temp_project)
        output = format_json(tree)
        data = json.loads(output)

        child_names = [c["name"] for c in data["children"]]
        assert "src" in child_names
        assert "README.md" in child_names

    def test_json_compact(self, temp_project: Path) -> None:
        """Test compact JSON output."""
        tree = walk_directory(temp_project)
        output = format_json(tree, pretty=False)

        # Compact JSON should be a single line
        assert "\n" not in output.strip()

    def test_json_file_extension(self, temp_project: Path) -> None:
        """Test that file extensions are included."""
        tree = walk_directory(temp_project)
        output = format_json(tree)
        data = json.loads(output)

        # Find a Python file
        src = next(c for c in data["children"] if c["name"] == "src")
        main_py = next(c for c in src["children"] if c["name"] == "main.py")

        assert main_py["extension"] == ".py"
        assert main_py["type"] == "file"


class TestYamlFormatter:
    """Tests for the YAML formatter."""

    def test_yaml_import_error(self, temp_project: Path) -> None:
        """Test that ImportError is raised when PyYAML is not available."""
        tree = walk_directory(temp_project)

        # This test assumes PyYAML might not be installed
        # If it is installed, the test will pass anyway
        try:
            output = format_yaml(tree)
            # If PyYAML is installed, verify it's valid YAML
            import yaml
            data = yaml.safe_load(output)
            assert isinstance(data, dict)
        except ImportError as e:
            assert "PyYAML" in str(e)

    @pytest.mark.skipif(
        not pytest.importorskip("yaml", reason="PyYAML not installed"),
        reason="PyYAML not installed"
    )
    def test_yaml_structure(self, temp_project: Path) -> None:
        """Test YAML structure when PyYAML is available."""
        import yaml

        tree = walk_directory(temp_project)
        output = format_yaml(tree)
        data = yaml.safe_load(output)

        assert "name" in data
        assert "type" in data
        assert "children" in data
