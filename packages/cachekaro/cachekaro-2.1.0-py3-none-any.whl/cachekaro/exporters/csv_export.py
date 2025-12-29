"""
CSV exporter for CacheKaro.

Produces CSV output for spreadsheet analysis.
"""

from __future__ import annotations

import csv
import io

from cachekaro.exporters.base import Exporter, ExportFormat
from cachekaro.models.cache_item import CacheItem
from cachekaro.models.scan_result import ScanResult


class CsvExporter(Exporter):
    """
    Exports scan results to CSV format.

    Produces flat CSV data suitable for spreadsheet analysis.
    """

    def __init__(self, delimiter: str = ",", include_headers: bool = True):
        """
        Initialize the CSV exporter.

        Args:
            delimiter: Field delimiter character
            include_headers: Include header row
        """
        self.delimiter = delimiter
        self.include_headers = include_headers

    @property
    def format(self) -> ExportFormat:
        return ExportFormat.CSV

    @property
    def file_extension(self) -> str:
        return "csv"

    def export(self, result: ScanResult) -> str:
        """Export scan result to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        # Write headers
        if self.include_headers:
            writer.writerow(CacheItem.csv_headers())

        # Write data rows
        for item in result.items:
            writer.writerow(item.to_csv_row())

        return output.getvalue()

    def export_summary(self, result: ScanResult) -> str:
        """Export category summary to CSV."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        # Headers
        if self.include_headers:
            writer.writerow([
                "Category",
                "Total Size (Bytes)",
                "Formatted Size",
                "Item Count",
                "File Count",
                "Stale Size (Bytes)",
                "Stale Count",
            ])

        # Data
        summaries = result.get_category_summaries()
        for cat, summary in sorted(summaries.items(), key=lambda x: x[1].total_size, reverse=True):
            writer.writerow([
                cat.value,
                summary.total_size,
                summary.formatted_size,
                summary.item_count,
                summary.file_count,
                summary.stale_size,
                summary.stale_count,
            ])

        return output.getvalue()

    def export_detailed(self, result: ScanResult) -> str:
        """Export with additional file type details."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        # Extended headers
        if self.include_headers:
            writer.writerow([
                "Path",
                "Name",
                "Category",
                "Size (Bytes)",
                "Size (Formatted)",
                "File Count",
                "Directory Count",
                "Age (Days)",
                "Is Stale",
                "Risk Level",
                "App Name",
                "Description",
                "Last Accessed",
                "Last Modified",
                "Is Accessible",
                "Requires Admin",
            ])

        # Data rows with extended info
        for item in result.items:
            writer.writerow([
                str(item.path),
                item.name,
                item.category.value,
                item.size_bytes,
                item.formatted_size,
                item.file_count,
                item.dir_count,
                item.age_days,
                item.is_stale,
                item.risk_level.value,
                item.app_name or "",
                item.description,
                item.last_accessed.isoformat() if item.last_accessed else "",
                item.last_modified.isoformat() if item.last_modified else "",
                item.is_accessible,
                item.requires_admin,
            ])

        return output.getvalue()
