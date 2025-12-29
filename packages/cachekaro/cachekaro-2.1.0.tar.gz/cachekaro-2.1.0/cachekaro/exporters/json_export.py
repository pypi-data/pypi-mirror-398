"""
JSON exporter for CacheKaro.

Produces structured JSON output for programmatic use.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from cachekaro.exporters.base import Exporter, ExportFormat
from cachekaro.models.scan_result import ScanResult


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class JsonExporter(Exporter):
    """
    Exports scan results to JSON format.

    Produces structured JSON with complete metadata for API/automation use.
    """

    def __init__(self, indent: int | None = 2, include_file_details: bool = True):
        """
        Initialize the JSON exporter.

        Args:
            indent: JSON indentation level (None for compact)
            include_file_details: Include detailed file info
        """
        self.indent: int | None = indent
        self.include_file_details = include_file_details

    @property
    def format(self) -> ExportFormat:
        return ExportFormat.JSON

    @property
    def file_extension(self) -> str:
        return "json"

    def export(self, result: ScanResult) -> str:
        """Export scan result to JSON format."""
        data = result.to_dict()

        # Optionally remove detailed file info to reduce size
        if not self.include_file_details:
            for item in data.get("items", []):
                item.pop("largest_files", None)
                item.pop("file_types", None)

        return json.dumps(data, cls=DateTimeEncoder, indent=self.indent)

    def export_compact(self, result: ScanResult) -> str:
        """Export to compact JSON (no indentation)."""
        original = self.indent
        self.indent = None
        output = self.export(result)
        self.indent = original
        return output

    def export_summary_only(self, result: ScanResult) -> str:
        """Export only summary statistics."""
        data = result.to_dict()

        # Keep only summary data
        summary = {
            "summary": data.get("summary", {}),
            "disk": data.get("disk", {}),
            "categories": data.get("categories", {}),
            "metadata": data.get("metadata", {}),
        }

        return json.dumps(summary, cls=DateTimeEncoder, indent=self.indent)
