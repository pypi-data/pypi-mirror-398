"""
Data models for CacheKaro.

Provides structured data classes for cache items, scan results, and configuration.
"""

from cachekaro.models.cache_item import CacheItem, FileInfo, FileTypeStats
from cachekaro.models.scan_result import CategorySummary, ScanMetadata, ScanResult

__all__ = [
    "CacheItem",
    "FileInfo",
    "FileTypeStats",
    "ScanResult",
    "CategorySummary",
    "ScanMetadata",
]
