"""
Storage analyzer for CacheKaro.

Orchestrates scanning and generates comprehensive analysis results.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from cachekaro.core.scanner import Scanner
from cachekaro.models.cache_item import CacheItem
from cachekaro.models.scan_result import ScanMetadata, ScanResult
from cachekaro.platforms.base import Category, PlatformBase, RiskLevel


class Analyzer:
    """
    Analyzes storage and cache usage.

    Orchestrates the scanning process and generates comprehensive reports.
    """

    def __init__(
        self,
        platform: PlatformBase,
        stale_threshold_days: int = 30,
        min_size_bytes: int = 0,
        include_empty: bool = False,
        max_workers: int = 4,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ):
        """
        Initialize the analyzer.

        Args:
            platform: Platform implementation to use
            stale_threshold_days: Days after which cache is considered stale
            min_size_bytes: Minimum size to include in results
            include_empty: Whether to include empty cache locations
            max_workers: Number of parallel scanning workers
            progress_callback: Callback for progress updates (name, current, total)
        """
        self.platform = platform
        self.stale_threshold_days = stale_threshold_days
        self.min_size_bytes = min_size_bytes
        self.include_empty = include_empty
        self.max_workers = max_workers
        self.progress_callback = progress_callback

        self.scanner = Scanner(
            max_workers=max_workers,
            stale_threshold_days=stale_threshold_days,
            progress_callback=progress_callback,
        )

    def analyze(
        self,
        categories: list[Category] | None = None,
        max_risk: RiskLevel = RiskLevel.CAUTION,
        include_non_existent: bool = False,
    ) -> ScanResult:
        """
        Perform a full storage analysis.

        Args:
            categories: Optional list of categories to analyze (None = all)
            max_risk: Maximum risk level to include
            include_non_existent: Include paths that don't exist

        Returns:
            ScanResult with all analyzed cache items
        """
        start_time = time.time()

        # Get cache paths from platform
        cache_paths = self.platform.get_cache_paths()

        # Filter by category if specified
        if categories:
            cache_paths = [p for p in cache_paths if p.category in categories]

        # Filter by risk level
        risk_order = [RiskLevel.SAFE, RiskLevel.MODERATE, RiskLevel.CAUTION]
        max_index = risk_order.index(max_risk)
        cache_paths = [
            p for p in cache_paths if risk_order.index(p.risk_level) <= max_index
        ]

        # Filter to existing paths if requested
        if not include_non_existent:
            cache_paths = [p for p in cache_paths if p.exists()]

        # Scan all paths
        items = self.scanner.scan_paths(cache_paths)

        # Filter results
        filtered_items = self._filter_items(items)

        # Sort by size (largest first)
        filtered_items.sort(key=lambda x: x.size_bytes, reverse=True)

        # Get disk usage
        disk_usage = self.platform.get_disk_usage()

        # Get platform info
        platform_info = self.platform.get_platform_info()

        # Calculate duration
        duration = time.time() - start_time

        # Collect errors
        errors = [
            f"{item.name}: {item.error_message}"
            for item in items
            if item.error_message
        ]

        # Create metadata
        metadata = ScanMetadata(
            scan_time=datetime.now(),
            duration_seconds=duration,
            platform=platform_info.name,
            platform_version=platform_info.version,
            hostname=platform_info.hostname,
            username=platform_info.username,
            scan_paths_total=len(cache_paths),
            scan_paths_found=sum(1 for item in items if item.exists),
            scan_paths_accessible=sum(1 for item in items if item.is_accessible),
            errors=errors,
        )

        # Create result
        result = ScanResult(
            items=filtered_items,
            metadata=metadata,
            disk_total=disk_usage.total_bytes,
            disk_used=disk_usage.used_bytes,
            disk_free=disk_usage.free_bytes,
        )

        return result

    def _filter_items(self, items: list[CacheItem]) -> list[CacheItem]:
        """
        Filter items based on analyzer settings.

        Args:
            items: List of scanned items

        Returns:
            Filtered list of items
        """
        filtered = []
        for item in items:
            # Skip items that don't exist
            if not item.exists:
                continue

            # Skip empty items if not requested
            if not self.include_empty and item.is_empty:
                continue

            # Skip items below minimum size
            if item.size_bytes < self.min_size_bytes:
                continue

            filtered.append(item)

        return filtered

    def analyze_category(self, category: Category) -> ScanResult:
        """
        Analyze a specific category.

        Args:
            category: The category to analyze

        Returns:
            ScanResult for the category
        """
        return self.analyze(categories=[category])

    def analyze_stale(self) -> ScanResult:
        """
        Analyze only stale cache items.

        Returns:
            ScanResult containing only stale items
        """
        result = self.analyze()
        result.items = [item for item in result.items if item.is_stale]
        return result

    def analyze_app(self, app_name: str) -> ScanResult:
        """
        Analyze cache for a specific app.

        Args:
            app_name: Name of the application

        Returns:
            ScanResult for the app
        """
        result = self.analyze()
        result.items = [
            item
            for item in result.items
            if item.app_specific
            and item.app_name
            and item.app_name.lower() == app_name.lower()
        ]
        return result

    def get_quick_summary(self) -> dict:
        """
        Get a quick summary without detailed file scanning.

        Returns:
            Dictionary with summary statistics
        """
        cache_paths = self.platform.get_existing_paths()
        disk_usage = self.platform.get_disk_usage()

        total_size = 0
        category_sizes: dict[Category, int] = {}

        for path in cache_paths:
            size = self.scanner.get_directory_size(path.path)
            total_size += size

            if path.category not in category_sizes:
                category_sizes[path.category] = 0
            category_sizes[path.category] += size

        return {
            "total_cache_size": total_size,
            "disk_total": disk_usage.total_bytes,
            "disk_used": disk_usage.used_bytes,
            "disk_free": disk_usage.free_bytes,
            "disk_usage_percent": disk_usage.used_percent,
            "cache_paths_count": len(cache_paths),
            "category_sizes": {
                cat.value: size for cat, size in category_sizes.items()
            },
        }

    def find_large_items(self, min_size_mb: float = 100) -> list[CacheItem]:
        """
        Find cache items larger than specified size.

        Args:
            min_size_mb: Minimum size in megabytes

        Returns:
            List of large cache items
        """
        min_bytes = int(min_size_mb * 1024 * 1024)
        result = self.analyze()
        return [item for item in result.items if item.size_bytes >= min_bytes]

    def get_recommendations(self, result: ScanResult) -> list[dict]:
        """
        Generate cleaning recommendations based on scan results.

        Args:
            result: Scan result to analyze

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Recommend cleaning stale caches
        stale_items = result.get_stale_items()
        if stale_items:
            stale_size = sum(item.size_bytes for item in stale_items)
            recommendations.append({
                "type": "stale",
                "priority": "high",
                "message": f"Clean {len(stale_items)} stale cache items",
                "potential_savings": stale_size,
                "items": [item.name for item in stale_items[:5]],
            })

        # Recommend cleaning large safe items
        large_safe = [
            item
            for item in result.items
            if item.size_bytes > 100 * 1024 * 1024  # > 100MB
            and item.risk_level == RiskLevel.SAFE
        ]
        if large_safe:
            large_size = sum(item.size_bytes for item in large_safe)
            recommendations.append({
                "type": "large_safe",
                "priority": "medium",
                "message": f"Clean {len(large_safe)} large safe cache items",
                "potential_savings": large_size,
                "items": [item.name for item in large_safe[:5]],
            })

        # Recommend cleaning development caches
        dev_items = result.get_items_by_category(Category.DEVELOPMENT)
        dev_size = sum(item.size_bytes for item in dev_items)
        if dev_size > 500 * 1024 * 1024:  # > 500MB
            recommendations.append({
                "type": "development",
                "priority": "medium",
                "message": "Clean development tool caches",
                "potential_savings": dev_size,
                "items": [item.name for item in dev_items[:5]],
            })

        # Recommend emptying trash
        trash_items = result.get_items_by_category(Category.TRASH)
        trash_size = sum(item.size_bytes for item in trash_items)
        if trash_size > 100 * 1024 * 1024:  # > 100MB
            recommendations.append({
                "type": "trash",
                "priority": "high",
                "message": "Empty Trash",
                "potential_savings": trash_size,
                "items": ["Trash"],
            })

        # Sort by priority
        priority_order: dict[str, int] = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(str(x["priority"]), 2))

        return recommendations
