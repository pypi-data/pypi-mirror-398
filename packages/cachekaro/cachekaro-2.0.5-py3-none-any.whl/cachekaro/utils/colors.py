"""
Cross-platform terminal color utilities for CacheKaro.
"""

import os
import re
import sys


class Colors:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = "\033[0m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Regular colors
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[0;37m"

    # Bright colors
    BRIGHT_BLACK = "\033[0;90m"
    BRIGHT_RED = "\033[0;91m"
    BRIGHT_GREEN = "\033[0;92m"
    BRIGHT_YELLOW = "\033[0;93m"
    BRIGHT_BLUE = "\033[0;94m"
    BRIGHT_MAGENTA = "\033[0;95m"
    BRIGHT_CYAN = "\033[0;96m"
    BRIGHT_WHITE = "\033[0;97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def supports_color() -> bool:
    """
    Check if the terminal supports color output.

    Returns:
        True if colors are supported
    """
    # Check for NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return False

    # Check for FORCE_COLOR
    if os.environ.get("FORCE_COLOR"):
        return True

    # Check if stdout is a tty
    if not hasattr(sys.stdout, "isatty"):
        return False

    if not sys.stdout.isatty():
        return False

    # Windows handling
    if sys.platform == "win32":
        # Windows 10 supports ANSI colors
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Enable ANSI support on Windows 10+
            kernel32.SetConsoleMode(
                kernel32.GetStdHandle(-11),
                7
            )
            return True
        except Exception:
            return False

    # Unix-like systems with TERM
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False

    return True


def colorize(text: str, color: str, bold: bool = False) -> str:
    """
    Apply color to text if colors are supported.

    Args:
        text: Text to colorize
        color: Color code from Colors class
        bold: Whether to make text bold

    Returns:
        Colorized text or plain text if colors not supported
    """
    if not supports_color():
        return text

    if bold:
        return f"{Colors.BOLD}{color}{text}{Colors.RESET}"
    return f"{color}{text}{Colors.RESET}"


def strip_colors(text: str) -> str:
    """
    Remove ANSI color codes from text.

    Args:
        text: Text with potential color codes

    Returns:
        Plain text without color codes
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


# Convenience functions
def red(text: str, bold: bool = False) -> str:
    """Color text red."""
    return colorize(text, Colors.RED, bold)


def green(text: str, bold: bool = False) -> str:
    """Color text green."""
    return colorize(text, Colors.GREEN, bold)


def yellow(text: str, bold: bool = False) -> str:
    """Color text yellow."""
    return colorize(text, Colors.YELLOW, bold)


def blue(text: str, bold: bool = False) -> str:
    """Color text blue."""
    return colorize(text, Colors.BLUE, bold)


def cyan(text: str, bold: bool = False) -> str:
    """Color text cyan."""
    return colorize(text, Colors.CYAN, bold)


def magenta(text: str, bold: bool = False) -> str:
    """Color text magenta."""
    return colorize(text, Colors.MAGENTA, bold)


def bold(text: str) -> str:
    """Make text bold."""
    if not supports_color():
        return text
    return f"{Colors.BOLD}{text}{Colors.RESET}"


def dim(text: str) -> str:
    """Make text dim."""
    if not supports_color():
        return text
    return f"{Colors.DIM}{text}{Colors.RESET}"
