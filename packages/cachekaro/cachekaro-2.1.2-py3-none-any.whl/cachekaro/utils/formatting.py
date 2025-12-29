"""
Formatting utilities for CacheKaro.
"""

from __future__ import annotations


def format_size(size_bytes: int | float, precision: int = 2) -> str:
    """
    Format size in bytes to human-readable string.

    Args:
        size_bytes: Size in bytes
        precision: Decimal precision

    Returns:
        Human-readable size string (e.g., "1.5 GB")
    """
    if size_bytes < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024.0:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.{precision}f} {unit}"
        size /= 1024.0

    return f"{size:.{precision}f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_number(num: int | float) -> str:
    """
    Format number with thousand separators.

    Args:
        num: Number to format

    Returns:
        Formatted string with commas
    """
    return f"{num:,}"


def format_percent(value: float, total: float, precision: int = 1) -> str:
    """
    Format value as percentage of total.

    Args:
        value: Numerator
        total: Denominator
        precision: Decimal precision

    Returns:
        Percentage string (e.g., "75.5%")
    """
    if total == 0:
        return "0%"
    percent = (value / total) * 100
    return f"{percent:.{precision}f}%"


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def create_progress_bar(
    current: int,
    total: int,
    width: int = 30,
    fill_char: str = "█",
    empty_char: str = "░",
) -> str:
    """
    Create a text progress bar.

    Args:
        current: Current progress value
        total: Total value
        width: Width of the bar in characters
        fill_char: Character for filled portion
        empty_char: Character for empty portion

    Returns:
        Progress bar string
    """
    if total == 0:
        percent = 0.0
    else:
        percent = current / total

    filled = int(width * percent)
    bar = fill_char * filled + empty_char * (width - filled)
    return f"[{bar}] {percent * 100:.1f}%"


def create_table(
    headers: list[str],
    rows: list[list[str]],
    min_widths: list[int] | None = None,
) -> str:
    """
    Create a formatted text table.

    Args:
        headers: Column headers
        rows: Table rows
        min_widths: Minimum column widths

    Returns:
        Formatted table string
    """
    if not rows:
        return ""

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    # Apply minimum widths
    if min_widths:
        for i, min_w in enumerate(min_widths):
            if i < len(widths):
                widths[i] = max(widths[i], min_w)

    # Build table
    lines = []

    # Header
    header_row = " | ".join(
        headers[i].ljust(widths[i]) for i in range(len(headers))
    )
    lines.append(header_row)

    # Separator
    separator = "-+-".join("-" * w for w in widths)
    lines.append(separator)

    # Data rows
    for row in rows:
        data_row = " | ".join(
            str(row[i]).ljust(widths[i]) if i < len(row) else " " * widths[i]
            for i in range(len(headers))
        )
        lines.append(data_row)

    return "\n".join(lines)
