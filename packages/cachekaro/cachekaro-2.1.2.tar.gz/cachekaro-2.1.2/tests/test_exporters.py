"""
Tests for exporters.
"""

import json

import pytest

from cachekaro.exporters import CsvExporter, HtmlExporter, JsonExporter, TextExporter, get_exporter


class TestTextExporter:
    """Tests for TextExporter."""

    def test_export_text(self, sample_scan_result):
        """Test text export."""
        exporter = TextExporter(use_colors=False)
        output = exporter.export(sample_scan_result)

        assert "CACHEKARO" in output
        assert "DISK OVERVIEW" in output
        assert "CACHE SUMMARY" in output

    def test_export_with_colors(self, sample_scan_result):
        """Test text export with colors."""
        exporter = TextExporter(use_colors=True)
        output = exporter.export(sample_scan_result)

        # Should contain ANSI codes
        assert "\033[" in output

    def test_export_without_colors(self, sample_scan_result):
        """Test text export without colors."""
        exporter = TextExporter(use_colors=False)
        output = exporter.export_without_colors(sample_scan_result)

        # Should not contain ANSI codes
        assert "\033[" not in output


class TestJsonExporter:
    """Tests for JsonExporter."""

    def test_export_json(self, sample_scan_result):
        """Test JSON export."""
        exporter = JsonExporter()
        output = exporter.export(sample_scan_result)

        # Should be valid JSON
        data = json.loads(output)
        assert "summary" in data
        assert "items" in data
        assert "disk" in data

    def test_export_compact(self, sample_scan_result):
        """Test compact JSON export."""
        exporter = JsonExporter()
        output = exporter.export_compact(sample_scan_result)

        # Should be valid JSON without newlines
        data = json.loads(output)
        assert data is not None

    def test_export_summary_only(self, sample_scan_result):
        """Test summary-only export."""
        exporter = JsonExporter()
        output = exporter.export_summary_only(sample_scan_result)

        data = json.loads(output)
        assert "summary" in data
        assert "items" not in data


class TestCsvExporter:
    """Tests for CsvExporter."""

    def test_export_csv(self, sample_scan_result):
        """Test CSV export."""
        exporter = CsvExporter()
        output = exporter.export(sample_scan_result)

        lines = output.strip().split("\n")
        assert len(lines) > 1  # Header + data rows

        # Check headers
        headers = lines[0].split(",")
        assert "Path" in headers
        assert "Name" in headers
        assert "Category" in headers

    def test_export_without_headers(self, sample_scan_result):
        """Test CSV export without headers."""
        exporter = CsvExporter(include_headers=False)
        output = exporter.export(sample_scan_result)

        lines = output.strip().split("\n")
        # First line should be data, not header
        assert "Path" not in lines[0]

    def test_export_summary(self, sample_scan_result):
        """Test CSV summary export."""
        exporter = CsvExporter()
        output = exporter.export_summary(sample_scan_result)

        lines = output.strip().split("\n")
        assert len(lines) > 1

        headers = lines[0].split(",")
        assert "Category" in headers


class TestHtmlExporter:
    """Tests for HtmlExporter."""

    def test_export_html(self, sample_scan_result):
        """Test HTML export."""
        exporter = HtmlExporter()
        output = exporter.export(sample_scan_result)

        assert "<!DOCTYPE html>" in output
        assert "CacheKaro" in output
        assert "<table" in output
        assert "chart.js" in output  # Chart.js library reference

    def test_dark_mode(self, sample_scan_result):
        """Test HTML minimalist purple dark theme."""
        exporter = HtmlExporter(dark_mode=True)
        output = exporter.export(sample_scan_result)

        # Check for minimalist purple theme elements
        assert "--purple-primary" in output
        assert "--bg-primary: #0f0f1a" in output
        assert "Inter" in output  # Clean modern font


class TestExporterFactory:
    """Tests for exporter factory."""

    def test_get_text_exporter(self):
        """Test getting text exporter."""
        exporter = get_exporter("text")
        assert isinstance(exporter, TextExporter)

    def test_get_json_exporter(self):
        """Test getting JSON exporter."""
        exporter = get_exporter("json")
        assert isinstance(exporter, JsonExporter)

    def test_get_csv_exporter(self):
        """Test getting CSV exporter."""
        exporter = get_exporter("csv")
        assert isinstance(exporter, CsvExporter)

    def test_get_html_exporter(self):
        """Test getting HTML exporter."""
        exporter = get_exporter("html")
        assert isinstance(exporter, HtmlExporter)

    def test_invalid_format(self):
        """Test invalid format raises error."""
        with pytest.raises(ValueError):
            get_exporter("invalid")

    def test_case_insensitive(self):
        """Test format names are case insensitive."""
        exporter = get_exporter("JSON")
        assert isinstance(exporter, JsonExporter)
