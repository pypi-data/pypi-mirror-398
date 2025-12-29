"""
Tests for the cleaner.
"""

from pathlib import Path

from cachekaro.core.cleaner import Cleaner, CleanMode, CleanResult, CleanSummary
from cachekaro.core.scanner import Scanner
from cachekaro.platforms.base import Category, RiskLevel


class TestCleaner:
    """Tests for the Cleaner class."""

    def test_cleaner_creation(self):
        """Test cleaner can be created."""
        cleaner = Cleaner()
        assert cleaner is not None

    def test_dry_run_mode(self, sample_cache_path, temp_dir):
        """Test dry run doesn't delete files."""
        scanner = Scanner()
        item = scanner.scan_path(sample_cache_path)

        cleaner = Cleaner(mode=CleanMode.DRY_RUN)
        summary = cleaner.clean([item])

        assert summary.items_cleaned == 1
        assert summary.total_size_freed > 0
        # Files should still exist
        assert sample_cache_path.path.exists()
        assert len(list(sample_cache_path.path.iterdir())) > 0

    def test_auto_mode_deletes(self, sample_cache_path, temp_dir):
        """Test auto mode deletes files."""
        scanner = Scanner()
        item = scanner.scan_path(sample_cache_path)

        cleaner = Cleaner(mode=CleanMode.AUTO, max_risk=RiskLevel.SAFE)
        summary = cleaner.clean([item])

        assert summary.items_cleaned == 1
        # Directory should exist but be empty (clean_contents_only=True)
        assert sample_cache_path.path.exists()

    def test_interactive_skip_without_callback(self, sample_cache_path):
        """Test interactive mode skips without callback."""
        scanner = Scanner()
        item = scanner.scan_path(sample_cache_path)

        cleaner = Cleaner(mode=CleanMode.INTERACTIVE)
        summary = cleaner.clean([item])

        assert summary.items_skipped == 1
        assert summary.items_cleaned == 0

    def test_interactive_with_callback(self, sample_cache_path):
        """Test interactive mode with callback."""
        scanner = Scanner()
        item = scanner.scan_path(sample_cache_path)

        # Callback that always confirms
        def confirm(item):
            return True

        cleaner = Cleaner(mode=CleanMode.INTERACTIVE, confirm_callback=confirm)
        summary = cleaner.clean([item])

        assert summary.items_cleaned == 1

    def test_risk_level_filter(self, temp_dir):
        """Test risk level filtering."""
        # Create a cache item with CAUTION risk
        cache_dir = temp_dir / "caution_cache"
        cache_dir.mkdir()
        (cache_dir / "file.txt").write_text("test")

        from cachekaro.platforms.base import CachePath
        path = CachePath(
            path=cache_dir,
            name="Caution Cache",
            category=Category.USER_CACHE,
            description="High risk cache",
            risk_level=RiskLevel.CAUTION,
        )

        scanner = Scanner()
        item = scanner.scan_path(path)

        # Cleaner with SAFE max risk should not clean CAUTION items
        cleaner = Cleaner(mode=CleanMode.AUTO, max_risk=RiskLevel.SAFE)
        summary = cleaner.clean([item])

        assert summary.items_cleaned == 0
        assert cache_dir.exists()

    def test_estimate_savings(self, sample_cache_path):
        """Test savings estimation."""
        scanner = Scanner()
        item = scanner.scan_path(sample_cache_path)

        cleaner = Cleaner()
        estimate = cleaner.estimate_savings([item])

        assert estimate["total_items"] == 1
        assert estimate["total_size"] > 0
        assert estimate["total_files"] > 0

    def test_clean_summary_formatting(self):
        """Test clean summary formatting."""
        summary = CleanSummary(
            total_items=5,
            items_cleaned=3,
            items_skipped=1,
            items_failed=1,
            total_size_freed=1024 * 1024 * 100,  # 100 MB
        )

        assert "100" in summary.formatted_size_freed
        assert "MB" in summary.formatted_size_freed

    def test_clean_result_creation(self):
        """Test clean result creation."""
        result = CleanResult(
            path=Path("/test"),
            name="Test",
            success=True,
            size_freed=1024,
            files_deleted=5,
        )

        assert result.success
        assert result.size_freed == 1024
        assert result.files_deleted == 5
