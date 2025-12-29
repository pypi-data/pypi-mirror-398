"""
Base exporter class for CacheKaro.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from cachekaro.models.scan_result import ScanResult


class ExportFormat(Enum):
    """Supported export formats."""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    HTML = "html"


class Exporter(ABC):
    """
    Abstract base class for exporters.

    Each exporter must implement methods to convert scan results
    to its specific format.
    """

    @property
    @abstractmethod
    def format(self) -> ExportFormat:
        """Return the export format."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format."""
        pass

    @abstractmethod
    def export(self, result: ScanResult) -> str:
        """
        Export scan result to string.

        Args:
            result: ScanResult to export

        Returns:
            Formatted string representation
        """
        pass

    def export_to_file(
        self,
        result: ScanResult,
        output_path: str | Path,
    ) -> Path:
        """
        Export scan result to a file.

        Args:
            result: ScanResult to export
            output_path: Path to output file

        Returns:
            Path to the created file
        """
        output_path = Path(output_path)

        # Add extension if not present
        if not output_path.suffix:
            output_path = output_path.with_suffix(f".{self.file_extension}")

        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export content
        content = self.export(result)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def format_size(self, size_bytes: int) -> str:
        """
        Format size in bytes to human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human-readable size string
        """
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        elif size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} B"
