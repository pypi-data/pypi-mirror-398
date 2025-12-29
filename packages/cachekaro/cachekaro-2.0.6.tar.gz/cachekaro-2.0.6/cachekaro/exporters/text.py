"""
Plain text exporter for CacheKaro.

Produces formatted text output suitable for terminal display.
"""

from __future__ import annotations

from cachekaro.exporters.base import Exporter, ExportFormat
from cachekaro.models.scan_result import ScanResult
from cachekaro.platforms.base import Category


class TextExporter(Exporter):
    """
    Exports scan results to plain text format.

    Produces a formatted report suitable for terminal or file output.
    """

    def __init__(self, use_colors: bool = True, width: int = 70):
        """
        Initialize the text exporter.

        Args:
            use_colors: Whether to include ANSI color codes
            width: Width of the output in characters
        """
        self.use_colors = use_colors
        self.width = width

        # ANSI color codes
        self.colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "red": "\033[0;31m",
            "green": "\033[0;32m",
            "yellow": "\033[1;33m",
            "blue": "\033[0;34m",
            "cyan": "\033[0;36m",
            "magenta": "\033[0;35m",
        }

    @property
    def format(self) -> ExportFormat:
        return ExportFormat.TEXT

    @property
    def file_extension(self) -> str:
        return "txt"

    def _color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.use_colors:
            return text
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    def _header(self, text: str) -> str:
        """Create a section header."""
        line = "=" * self.width
        return f"\n{self._color(line, 'cyan')}\n{self._color(text.center(self.width), 'bold')}\n{self._color(line, 'cyan')}\n"

    def _subheader(self, text: str) -> str:
        """Create a subsection header."""
        line = "-" * self.width
        return f"\n{self._color(text, 'yellow')}\n{line}\n"

    def export(self, result: ScanResult) -> str:
        """Export scan result to text format."""
        lines = []

        # Title
        lines.append(self._header("CACHEKARO - STORAGE & CACHE ANALYSIS REPORT"))

        # Scan info
        if result.metadata:
            lines.append(f"Platform: {result.metadata.platform}")
            lines.append(f"Scan Time: {result.metadata.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Duration: {result.metadata.duration_seconds:.2f} seconds")
            lines.append("")

        # Disk Overview
        lines.append(self._subheader("DISK OVERVIEW"))
        lines.append(f"Total Disk Space: {result.formatted_disk_total}")
        lines.append(f"Used Space: {result.formatted_disk_used} ({result.disk_usage_percent:.1f}%)")
        lines.append(f"Free Space: {result.formatted_disk_free}")
        lines.append("")

        # Cache Summary
        lines.append(self._subheader("CACHE SUMMARY"))
        lines.append(f"Total Cache Size: {self._color(result.formatted_total_size, 'red')}")
        lines.append(f"Cleanable (Safe): {self._color(result.formatted_cleanable_size, 'green')}")
        lines.append(f"Total Files: {result.total_files:,}")
        lines.append(f"Cache Locations: {len(result.items)}")
        if result.stale_count > 0:
            lines.append(f"Stale Caches: {result.stale_count} ({self.format_size(result.stale_size)})")
        lines.append("")

        # Category Breakdown
        lines.append(self._subheader("BREAKDOWN BY CATEGORY"))
        summaries = result.get_category_summaries()
        sorted_summaries = sorted(
            summaries.values(),
            key=lambda x: x.total_size,
            reverse=True
        )

        category_icons = {
            Category.USER_CACHE: "📁",
            Category.SYSTEM_CACHE: "⚙️",
            Category.BROWSER: "🌐",
            Category.DEVELOPMENT: "💻",
            Category.LOGS: "📝",
            Category.TRASH: "🗑️",
            Category.DOWNLOADS: "📥",
            Category.APPLICATION: "📦",
            Category.CONTAINER: "📦",
            Category.CUSTOM: "📂",
        }

        for summary in sorted_summaries:
            icon = category_icons.get(summary.category, "📁")
            name = summary.category.value.replace("_", " ").title()
            size = summary.formatted_size
            count = summary.item_count
            lines.append(f"  {icon} {name:20s} {size:>12s} ({count} items)")
        lines.append("")

        # Top Consumers
        lines.append(self._subheader("TOP 15 CACHE CONSUMERS"))
        top_items = result.get_top_items(15)
        for i, item in enumerate(top_items, 1):
            size_color = "red" if item.size_bytes > 100 * 1024 * 1024 else "yellow"
            risk_indicator = {
                "safe": self._color("[SAFE]", "green"),
                "moderate": self._color("[MOD]", "yellow"),
                "caution": self._color("[WARN]", "red"),
            }.get(item.risk_level.value, "")

            lines.append(
                f"  {i:2d}. {item.name:35s} "
                f"{self._color(item.formatted_size, size_color):>12s} "
                f"{risk_indicator}"
            )
        lines.append("")

        # Stale Caches (if any)
        stale_items = result.get_stale_items()
        if stale_items:
            lines.append(self._subheader("STALE CACHES (Not accessed recently)"))
            for item in sorted(stale_items, key=lambda x: x.age_days, reverse=True)[:10]:
                lines.append(
                    f"  {item.name:35s} "
                    f"{item.formatted_size:>12s} "
                    f"({item.age_days} days old)"
                )
            lines.append("")

        # Recommendations
        lines.append(self._subheader("CLEANABLE SPACE ESTIMATE"))
        lines.append(f"  Safe to clean: {self._color(result.formatted_cleanable_size, 'green')}")
        lines.append("")

        # Footer
        lines.append(self._color("=" * self.width, "cyan"))
        lines.append(self._color("Run 'cachekaro clean' to start cleaning".center(self.width), "cyan"))
        lines.append(self._color("=" * self.width, "cyan"))
        lines.append("")

        return "\n".join(lines)

    def export_without_colors(self, result: ScanResult) -> str:
        """Export without ANSI color codes (for file output)."""
        original = self.use_colors
        self.use_colors = False
        output = self.export(result)
        self.use_colors = original
        return output
