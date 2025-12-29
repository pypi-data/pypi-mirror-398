"""
Tests for platform detection and implementations.
"""

import platform

from cachekaro.platforms.base import Category, RiskLevel
from cachekaro.platforms.detector import (
    get_platform,
    get_platform_name,
    get_system_info,
)


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_get_platform_name(self):
        """Test that platform name is detected correctly."""
        name = get_platform_name()
        assert name in ["macos", "linux", "windows", "unknown"]

    def test_get_platform_name_matches_system(self):
        """Test that detected name matches actual system."""
        system = platform.system().lower()
        name = get_platform_name()

        if system == "darwin":
            assert name == "macos"
        elif system == "linux":
            assert name == "linux"
        elif system == "windows":
            assert name == "windows"

    def test_get_platform(self):
        """Test that platform instance is returned."""
        plat = get_platform()
        assert plat is not None
        assert plat.name in ["macOS", "Linux", "Windows"]

    def test_get_system_info(self):
        """Test that system info is returned."""
        info = get_system_info()
        assert "system" in info
        assert "platform" in info
        assert "python_version" in info


class TestPlatformBase:
    """Tests for platform base functionality."""

    def test_platform_has_name(self):
        """Test that platform has a name."""
        plat = get_platform()
        assert plat.name is not None
        assert len(plat.name) > 0

    def test_platform_info(self):
        """Test platform info."""
        plat = get_platform()
        info = plat.get_platform_info()

        assert info.name is not None
        assert info.home_dir is not None
        assert info.home_dir.exists()

    def test_home_dir_exists(self):
        """Test that home directory exists."""
        plat = get_platform()
        home = plat.get_home_dir()
        assert home.exists()
        assert home.is_dir()

    def test_temp_dir_exists(self):
        """Test that temp directory exists."""
        plat = get_platform()
        temp = plat.get_temp_dir()
        assert temp.exists()
        assert temp.is_dir()

    def test_config_dir(self):
        """Test that config directory is created."""
        plat = get_platform()
        config = plat.get_config_dir()
        assert config.exists()
        assert config.is_dir()

    def test_disk_usage(self):
        """Test disk usage retrieval."""
        plat = get_platform()
        usage = plat.get_disk_usage()

        assert usage.total_bytes > 0
        assert usage.used_bytes >= 0
        assert usage.free_bytes >= 0
        # Note: total may not equal used + free due to reserved blocks on some systems
        assert usage.used_bytes + usage.free_bytes <= usage.total_bytes
        assert 0 <= usage.used_percent <= 100

    def test_cache_paths(self):
        """Test that cache paths are returned."""
        plat = get_platform()
        paths = plat.get_cache_paths()

        assert isinstance(paths, list)
        assert len(paths) > 0

        for path in paths:
            assert path.name is not None
            assert path.category in Category
            assert path.risk_level in RiskLevel

    def test_existing_paths_subset(self):
        """Test that existing paths is a subset of all paths."""
        plat = get_platform()
        all_paths = plat.get_cache_paths()
        existing = plat.get_existing_paths()

        assert len(existing) <= len(all_paths)
        for path in existing:
            assert path.exists()

    def test_filter_by_category(self):
        """Test filtering paths by category."""
        plat = get_platform()

        browser_paths = plat.get_paths_by_category(Category.BROWSER)
        for path in browser_paths:
            assert path.category == Category.BROWSER

    def test_filter_by_risk(self):
        """Test filtering paths by risk level."""
        plat = get_platform()

        safe_paths = plat.get_paths_by_risk(RiskLevel.SAFE)
        for path in safe_paths:
            assert path.risk_level == RiskLevel.SAFE
