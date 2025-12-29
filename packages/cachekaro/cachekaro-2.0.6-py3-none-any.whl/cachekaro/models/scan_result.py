"""
Data models for scan results and summaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from cachekaro.models.cache_item import CacheItem
from cachekaro.platforms.base import Category, RiskLevel


@dataclass
class CategorySummary:
    """Summary statistics for a category."""
    category: Category
    total_size: int = 0
    item_count: int = 0
    file_count: int = 0
    stale_size: int = 0
    stale_count: int = 0

    @property
    def formatted_size(self) -> str:
        """Human-readable size string."""
        if self.total_size >= 1024 * 1024 * 1024:
            return f"{self.total_size / (1024 * 1024 * 1024):.2f} GB"
        elif self.total_size >= 1024 * 1024:
            return f"{self.total_size / (1024 * 1024):.2f} MB"
        elif self.total_size >= 1024:
            return f"{self.total_size / 1024:.2f} KB"
        else:
            return f"{self.total_size} B"

    @property
    def stale_formatted_size(self) -> str:
        """Human-readable stale size string."""
        if self.stale_size >= 1024 * 1024 * 1024:
            return f"{self.stale_size / (1024 * 1024 * 1024):.2f} GB"
        elif self.stale_size >= 1024 * 1024:
            return f"{self.stale_size / (1024 * 1024):.2f} MB"
        elif self.stale_size >= 1024:
            return f"{self.stale_size / 1024:.2f} KB"
        else:
            return f"{self.stale_size} B"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category.value,
            "total_size": self.total_size,
            "formatted_size": self.formatted_size,
            "item_count": self.item_count,
            "file_count": self.file_count,
            "stale_size": self.stale_size,
            "stale_formatted_size": self.stale_formatted_size,
            "stale_count": self.stale_count,
        }


@dataclass
class ScanMetadata:
    """Metadata about the scan."""
    scan_time: datetime
    duration_seconds: float
    platform: str
    platform_version: str
    hostname: str
    username: str
    scan_paths_total: int
    scan_paths_found: int
    scan_paths_accessible: int
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "scan_time": self.scan_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "platform": self.platform,
            "platform_version": self.platform_version,
            "hostname": self.hostname,
            "username": self.username,
            "scan_paths_total": self.scan_paths_total,
            "scan_paths_found": self.scan_paths_found,
            "scan_paths_accessible": self.scan_paths_accessible,
            "errors": self.errors,
        }


@dataclass
class ScanResult:
    """
    Complete scan result containing all analyzed cache items.

    Provides comprehensive statistics and filtering capabilities.
    """
    items: list[CacheItem] = field(default_factory=list)
    metadata: ScanMetadata | None = None
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0

    @property
    def total_size(self) -> int:
        """Total size of all cache items."""
        return sum(item.size_bytes for item in self.items)

    @property
    def total_files(self) -> int:
        """Total number of files across all items."""
        return sum(item.file_count for item in self.items)

    @property
    def cleanable_size(self) -> int:
        """Total size of cleanable items (safe risk level)."""
        return sum(
            item.size_bytes for item in self.items
            if item.is_cleanable and item.risk_level == RiskLevel.SAFE
        )

    @property
    def stale_size(self) -> int:
        """Total size of stale cache items."""
        return sum(item.size_bytes for item in self.items if item.is_stale)

    @property
    def stale_count(self) -> int:
        """Number of stale cache items."""
        return sum(1 for item in self.items if item.is_stale)

    @property
    def formatted_total_size(self) -> str:
        """Human-readable total size."""
        size = self.total_size
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
        elif size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        elif size >= 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size} B"

    @property
    def formatted_cleanable_size(self) -> str:
        """Human-readable cleanable size."""
        size = self.cleanable_size
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
        elif size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        elif size >= 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size} B"

    @property
    def formatted_disk_total(self) -> str:
        """Human-readable disk total."""
        size = self.disk_total
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"

    @property
    def formatted_disk_used(self) -> str:
        """Human-readable disk used."""
        size = self.disk_used
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"

    @property
    def formatted_disk_free(self) -> str:
        """Human-readable disk free."""
        size = self.disk_free
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"

    @property
    def disk_usage_percent(self) -> float:
        """Disk usage percentage."""
        if self.disk_total == 0:
            return 0.0
        return (self.disk_used / self.disk_total) * 100

    def get_category_summaries(self) -> dict[Category, CategorySummary]:
        """Get summary statistics grouped by category."""
        summaries: dict[Category, CategorySummary] = {}

        for item in self.items:
            if item.category not in summaries:
                summaries[item.category] = CategorySummary(category=item.category)

            summary = summaries[item.category]
            summary.total_size += item.size_bytes
            summary.item_count += 1
            summary.file_count += item.file_count

            if item.is_stale:
                summary.stale_size += item.size_bytes
                summary.stale_count += 1

        return summaries

    def get_top_items(self, limit: int = 10) -> list[CacheItem]:
        """Get top N items by size."""
        sorted_items = sorted(self.items, key=lambda x: x.size_bytes, reverse=True)
        return sorted_items[:limit]

    def get_items_by_category(self, category: Category) -> list[CacheItem]:
        """Get items filtered by category."""
        return [item for item in self.items if item.category == category]

    def get_items_by_risk(self, max_risk: RiskLevel) -> list[CacheItem]:
        """Get items filtered by maximum risk level."""
        risk_order = [RiskLevel.SAFE, RiskLevel.MODERATE, RiskLevel.CAUTION]
        max_index = risk_order.index(max_risk)
        return [
            item for item in self.items
            if risk_order.index(item.risk_level) <= max_index
        ]

    def get_stale_items(self) -> list[CacheItem]:
        """Get only stale items."""
        return [item for item in self.items if item.is_stale]

    def get_items_over_size(self, min_bytes: int) -> list[CacheItem]:
        """Get items over a minimum size."""
        return [item for item in self.items if item.size_bytes >= min_bytes]

    def get_app_items(self, app_name: str) -> list[CacheItem]:
        """Get items for a specific app."""
        return [
            item for item in self.items
            if item.app_specific and item.app_name and item.app_name.lower() == app_name.lower()
        ]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        category_summaries = self.get_category_summaries()
        return {
            "summary": {
                "total_size": self.total_size,
                "formatted_total_size": self.formatted_total_size,
                "total_files": self.total_files,
                "item_count": len(self.items),
                "cleanable_size": self.cleanable_size,
                "formatted_cleanable_size": self.formatted_cleanable_size,
                "stale_size": self.stale_size,
                "stale_count": self.stale_count,
            },
            "disk": {
                "total": self.disk_total,
                "formatted_total": self.formatted_disk_total,
                "used": self.disk_used,
                "formatted_used": self.formatted_disk_used,
                "free": self.disk_free,
                "formatted_free": self.formatted_disk_free,
                "usage_percent": self.disk_usage_percent,
            },
            "categories": {
                cat.value: summary.to_dict()
                for cat, summary in category_summaries.items()
            },
            "items": [item.to_dict() for item in self.items],
            "metadata": self.metadata.to_dict() if self.metadata else None,
        }
