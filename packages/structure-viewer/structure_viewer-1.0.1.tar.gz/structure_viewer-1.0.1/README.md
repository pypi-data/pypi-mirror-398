# Structure Viewer

[![CI](https://github.com/crrrowz/structure-viewer/actions/workflows/ci.yml/badge.svg)](https://github.com/crrrowz/structure-viewer/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/structure-viewer.svg)](https://pypi.org/project/structure-viewer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful CLI tool to visualize project directory structure with smart exclusions, multiple output formats, and colorized output.

![Structure Viewer Demo](assets/demo.png)

## ✨ Features

- 🌳 **Beautiful Tree Output** - ASCII art tree representation with colorized output
- 🚫 **Smart Exclusions** - Automatically excludes common development artifacts (`.git`, `node_modules`, `__pycache__`, etc.)
- 📊 **Multiple Formats** - Output as tree, JSON, or YAML
- 🎨 **Colorized Output** - File type-aware syntax highlighting in terminal
- 🔧 **Highly Configurable** - Custom exclusions, depth limiting, extension filtering
- 🖥️ **Cross-Platform** - Works on Windows, macOS, and Linux

## 📦 Installation

### Using pip

```bash
pip install structure-viewer
```

### Using pipx (recommended for CLI tools)

```bash
pipx install structure-viewer
```

### From source

```bash
git clone https://github.com/crrrowz/structure-viewer.git
cd structure-viewer
pip install -e .
```

## 🚀 Usage

### Basic Usage

```bash
# Show structure of current directory
structure

# Show structure of a specific directory
structure ./my-project

# Show structure with limited depth
structure -d 2
```

### Output Formats

```bash
# Default tree format
structure

# JSON output
structure -f json

# YAML output (requires PyYAML)
structure -f yaml
```

### Filtering

```bash
# Only show Python files
structure -I py

# Exclude log and tmp files
structure -E log -E tmp

# Add custom exclusion patterns
structure -e "*.bak" -e "*.tmp"

# Show hidden files
structure -a
```

### Other Options

```bash
# Show only directories
structure -q

# Show file/directory statistics
structure -s

# Disable colors
structure --no-color
```

## 📋 Example Output

```
my-project/
├── src/
│   ├── __init__.py
│   ├── cli.py
│   ├── core.py
│   └── utils.py
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   └── test_core.py
├── LICENSE
├── README.md
└── pyproject.toml

2 directories, 10 files
```

## ⚙️ CLI Reference

```
usage: structure [OPTIONS] [DIRECTORY]

Visualize project directory structure.

positional arguments:
  directory              Directory to scan (default: current directory)

options:
  -h, --help             Show this help message
  -V, --version          Show version number
  -d, --depth N          Maximum depth to display (default: unlimited)
  -e, --exclude PATTERN  Additional patterns to exclude (can be repeated)
  -I, --include-ext EXT  Only show files with these extensions
  -E, --exclude-ext EXT  Exclude files with these extensions
  -f, --format FORMAT    Output format: tree, json, yaml (default: tree)
  -a, --all              Show hidden files
  --no-color             Disable colorized output
  -q, --quiet            Only show directories
  -s, --stats            Show statistics
```

## 🔒 Default Exclusions

Structure Viewer automatically excludes common development artifacts:

| Category | Patterns |
|----------|----------|
| Version Control | `.git`, `.hg`, `.svn` |
| Python | `__pycache__`, `.pytest_cache`, `.mypy_cache`, `*.egg-info` |
| Node.js | `node_modules`, `.npm`, `.yarn` |
| Build | `dist`, `build`, `out`, `target` |
| IDEs | `.idea`, `.vscode`, `.vs` |
| OS | `.DS_Store`, `Thumbs.db` |

## 🐍 Python API

You can also use structure-viewer as a library:

```python
from structure_viewer import walk_directory, format_tree

# Get the directory tree
tree = walk_directory("./my-project", max_depth=3)

# Format as ASCII tree
output = format_tree(tree, colorize=False)
print(output)

# Or as JSON
from structure_viewer import format_json
json_output = format_json(tree)
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/crrrowz/structure-viewer/blob/main/CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/crrrowz/structure-viewer/blob/main/LICENSE) file for details.

## 🙏 Acknowledgments

Inspired by the classic `tree` command and modern directory visualization tools.
