"""
Cross-platform terminal color support for structure-viewer.
"""

import os
import sys
from typing import Dict

# ANSI color codes
COLORS: Dict[str, str] = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",

    # Regular colors
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",

    # Bright colors
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
}


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    # Check for explicit disable
    if os.environ.get("NO_COLOR"):
        return False

    # Check for explicit enable
    if os.environ.get("FORCE_COLOR"):
        return True

    # Check if output is a TTY
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    # Windows-specific handling
    if sys.platform == "win32":
        # Windows 10+ supports ANSI codes natively
        # Try to enable virtual terminal processing
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Enable ANSI escape sequences on Windows 10+
            kernel32.SetConsoleMode(
                kernel32.GetStdHandle(-11),  # STD_OUTPUT_HANDLE
                7  # ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            )
            return True
        except Exception:
            # Check for Windows Terminal or other modern terminals
            return (
                os.environ.get("WT_SESSION") is not None  # Windows Terminal
                or os.environ.get("TERM_PROGRAM") == "vscode"
                or os.environ.get("ANSICON") is not None
            )

    # Unix-like systems generally support colors
    return True


# Cache the color support check
_COLOR_SUPPORTED: bool = _supports_color()


class ColorPrinter:
    """A utility class for printing colored text to the terminal."""

    def __init__(self, enabled: bool = True) -> None:
        """
        Initialize the color printer.

        Args:
            enabled: Whether to enable color output. If False, no color codes
                    will be added even if the terminal supports them.
        """
        self._enabled = enabled and _COLOR_SUPPORTED

    @property
    def enabled(self) -> bool:
        """Check if colors are enabled."""
        return self._enabled

    def colorize(self, text: str, color: str, bold: bool = False) -> str:
        """
        Apply color to text.

        Args:
            text: The text to colorize.
            color: The color name from COLORS dict.
            bold: Whether to make the text bold.

        Returns:
            The colorized text string, or plain text if colors are disabled.
        """
        if not self._enabled:
            return text

        color_code = COLORS.get(color, "")
        bold_code = COLORS["bold"] if bold else ""
        reset_code = COLORS["reset"]

        return f"{bold_code}{color_code}{text}{reset_code}"

    def directory(self, name: str) -> str:
        """Format a directory name with appropriate color."""
        return self.colorize(name, "bright_blue", bold=True)

    def file(self, name: str, extension: str = "") -> str:
        """
        Format a file name with appropriate color based on extension.

        Args:
            name: The file name.
            extension: The file extension (including the dot).

        Returns:
            The colorized file name.
        """
        from structure_viewer.config import EXTENSION_TYPE_MAP, FILE_TYPE_COLORS

        file_type = EXTENSION_TYPE_MAP.get(extension.lower(), "default")
        color = FILE_TYPE_COLORS.get(file_type, "reset")

        return self.colorize(name, color)

    def connector(self, text: str) -> str:
        """Format tree connector characters."""
        return self.colorize(text, "dim")

    def error(self, text: str) -> str:
        """Format error messages."""
        return self.colorize(text, "red", bold=True)

    def warning(self, text: str) -> str:
        """Format warning messages."""
        return self.colorize(text, "yellow")

    def success(self, text: str) -> str:
        """Format success messages."""
        return self.colorize(text, "green")


# Default color printer instance
default_printer = ColorPrinter()
