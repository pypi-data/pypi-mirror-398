"""
Pytest fixtures for structure-viewer tests.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_project() -> Generator[Path, None, None]:
    """
    Create a temporary project directory with a sample structure.

    Structure:
        temp_project/
        ├── src/
        │   ├── main.py
        │   └── utils.py
        ├── tests/
        │   └── test_main.py
        ├── README.md
        └── .git/
            └── config
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create directories
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / ".git").mkdir()
        (root / "node_modules").mkdir()  # Should be excluded

        # Create files
        (root / "src" / "main.py").write_text("# Main module\n")
        (root / "src" / "utils.py").write_text("# Utils module\n")
        (root / "tests" / "test_main.py").write_text("# Tests\n")
        (root / "README.md").write_text("# Project\n")
        (root / ".git" / "config").write_text("[core]\n")
        (root / "node_modules" / "package.json").write_text("{}\n")

        yield root


@pytest.fixture
def temp_empty_dir() -> Generator[Path, None, None]:
    """Create an empty temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_nested_dir() -> Generator[Path, None, None]:
    """
    Create a deeply nested temporary directory.

    Structure:
        temp_nested/
        └── level1/
            └── level2/
                └── level3/
                    └── deep.txt
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        deep_path = root / "level1" / "level2" / "level3"
        deep_path.mkdir(parents=True)
        (deep_path / "deep.txt").write_text("Deep content\n")

        yield root


@pytest.fixture
def temp_mixed_extensions() -> Generator[Path, None, None]:
    """
    Create a directory with various file extensions.

    Structure:
        temp_mixed/
        ├── script.py
        ├── style.css
        ├── app.js
        ├── data.json
        └── notes.txt
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "script.py").write_text("# Python\n")
        (root / "style.css").write_text("/* CSS */\n")
        (root / "app.js").write_text("// JavaScript\n")
        (root / "data.json").write_text("{}\n")
        (root / "notes.txt").write_text("Notes\n")

        yield root
