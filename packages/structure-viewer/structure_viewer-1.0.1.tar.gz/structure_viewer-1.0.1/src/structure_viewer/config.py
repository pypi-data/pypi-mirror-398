"""
Default configuration and exclusion patterns for structure-viewer.
"""

from typing import FrozenSet

# Default directories and files to exclude from the tree
DEFAULT_EXCLUSIONS: FrozenSet[str] = frozenset({
    # Version Control
    ".git",
    ".hg",
    ".svn",
    ".bzr",

    # Python
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".coverage",
    "htmlcov",
    ".eggs",
    "*.egg-info",
    ".python-version",

    # Virtual Environments
    "env",
    "venv",
    ".env",
    ".venv",
    "ENV",
    "virtualenv",

    # Node.js / JavaScript
    "node_modules",
    ".npm",
    ".yarn",
    ".pnpm-store",
    "bower_components",

    # Build Outputs
    "dist",
    "build",
    "out",
    "target",
    "_build",
    "site-packages",

    # Framework Specific
    ".next",
    ".nuxt",
    ".cache",
    ".parcel-cache",
    ".turbo",
    ".svelte-kit",

    # IDE / Editor
    ".idea",
    ".vscode",
    ".vs",
    "*.swp",
    "*.swo",
    "*~",

    # Java / Gradle / Maven
    ".gradle",
    ".m2",
    "*.class",

    # macOS
    ".DS_Store",
    ".AppleDouble",
    ".LSOverride",

    # Windows
    "Thumbs.db",
    "ehthumbs.db",
    "Desktop.ini",

    # iOS / Xcode
    "DerivedData",
    "*.xcworkspace",
    "Pods",

    # Flutter / Dart
    ".dart_tool",
    ".packages",
    ".pub-cache",
    ".pub",

    # Logs and Temp
    "logs",
    "log",
    "*.log",
    ".temp",
    "temp",
    "tmp",
    ".tmp",

    # Misc
    "coverage",
    ".nyc_output",
    ".hypothesis",
})

# File extensions that indicate binary files (optional for future use)
BINARY_EXTENSIONS: FrozenSet[str] = frozenset({
    ".exe", ".dll", ".so", ".dylib",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".webp",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".pyc", ".pyo", ".class", ".o", ".obj",
})

# Colors for different file types
FILE_TYPE_COLORS = {
    "directory": "blue",
    "python": "green",
    "javascript": "yellow",
    "typescript": "cyan",
    "config": "magenta",
    "markdown": "white",
    "default": "reset",
}

# Extension to type mapping for colorization
EXTENSION_TYPE_MAP = {
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".json": "config",
    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".ini": "config",
    ".cfg": "config",
    ".md": "markdown",
    ".rst": "markdown",
    ".txt": "markdown",
}
