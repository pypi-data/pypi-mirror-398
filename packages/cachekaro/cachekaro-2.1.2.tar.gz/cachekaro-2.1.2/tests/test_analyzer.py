"""
Tests for the analyzer and scanner.
"""


from cachekaro.core.analyzer import Analyzer
from cachekaro.core.scanner import Scanner
from cachekaro.platforms import get_platform
from cachekaro.platforms.base import Category, RiskLevel


class TestScanner:
    """Tests for the Scanner class."""

    def test_scanner_creation(self):
        """Test scanner can be created."""
        scanner = Scanner()
        assert scanner is not None

    def test_scan_path(self, sample_cache_path):
        """Test scanning a single path."""
        scanner = Scanner()
        item = scanner.scan_path(sample_cache_path)

        assert item is not None
        assert item.name == "Test Cache"
        assert item.exists
        assert item.is_accessible
        assert item.size_bytes > 0
        assert item.file_count > 0

    def test_scan_nonexistent_path(self, temp_dir):
        """Test scanning a non-existent path."""
        from cachekaro.platforms.base import CachePath

        path = CachePath(
            path=temp_dir / "nonexistent",
            name="Missing",
            category=Category.USER_CACHE,
            description="Does not exist",
        )

        scanner = Scanner()
        item = scanner.scan_path(path)

        assert not item.exists
        assert not item.is_accessible

    def test_scan_collects_file_types(self, sample_cache_path):
        """Test that file types are collected."""
        scanner = Scanner(collect_file_details=True)
        item = scanner.scan_path(sample_cache_path)

        assert len(item.file_types) > 0
        assert ".txt" in item.file_types or ".log" in item.file_types

    def test_scan_finds_largest_files(self, sample_cache_path):
        """Test that largest files are tracked."""
        scanner = Scanner(collect_file_details=True, max_largest_files=5)
        item = scanner.scan_path(sample_cache_path)

        assert len(item.largest_files) > 0
        # Should be sorted by size descending
        if len(item.largest_files) > 1:
            assert item.largest_files[0].size_bytes >= item.largest_files[1].size_bytes

    def test_get_directory_size(self, sample_cache_path):
        """Test getting directory size."""
        scanner = Scanner()
        size = scanner.get_directory_size(sample_cache_path.path)
        assert size > 0

    def test_count_files(self, sample_cache_path):
        """Test counting files and directories."""
        scanner = Scanner()
        file_count, dir_count = scanner.count_files(sample_cache_path.path)
        assert file_count > 0
        assert dir_count >= 0


class TestAnalyzer:
    """Tests for the Analyzer class."""

    def test_analyzer_creation(self):
        """Test analyzer can be created."""
        platform = get_platform()
        analyzer = Analyzer(platform=platform)
        assert analyzer is not None

    def test_analyze_returns_result(self):
        """Test that analyze returns a result."""
        platform = get_platform()
        analyzer = Analyzer(platform=platform, min_size_bytes=0)
        result = analyzer.analyze()

        assert result is not None
        assert result.metadata is not None

    def test_analyze_with_category_filter(self):
        """Test analyzing specific category."""
        platform = get_platform()
        analyzer = Analyzer(platform=platform)
        result = analyzer.analyze(categories=[Category.BROWSER])

        for item in result.items:
            assert item.category == Category.BROWSER

    def test_analyze_with_risk_filter(self):
        """Test analyzing with risk filter."""
        platform = get_platform()
        analyzer = Analyzer(platform=platform)
        result = analyzer.analyze(max_risk=RiskLevel.SAFE)

        for item in result.items:
            assert item.risk_level == RiskLevel.SAFE

    def test_quick_summary(self):
        """Test quick summary generation."""
        platform = get_platform()
        analyzer = Analyzer(platform=platform)
        summary = analyzer.get_quick_summary()

        assert "total_cache_size" in summary
        assert "disk_total" in summary
        assert "cache_paths_count" in summary

    def test_recommendations(self, sample_scan_result):
        """Test recommendation generation."""
        platform = get_platform()
        analyzer = Analyzer(platform=platform)
        recommendations = analyzer.get_recommendations(sample_scan_result)

        assert isinstance(recommendations, list)
