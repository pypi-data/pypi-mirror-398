"""
Data models for cache items and file information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from cachekaro.platforms.base import Category, RiskLevel


@dataclass
class FileInfo:
    """Information about a single file."""
    path: Path
    name: str
    size_bytes: int
    extension: str
    last_accessed: datetime | None = None
    last_modified: datetime | None = None
    created_time: datetime | None = None

    @property
    def age_days(self) -> int:
        """Calculate days since last access."""
        if self.last_accessed is None:
            return 0
        delta = datetime.now() - self.last_accessed
        return delta.days

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "name": self.name,
            "size_bytes": self.size_bytes,
            "extension": self.extension,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "age_days": self.age_days,
        }


@dataclass
class FileTypeStats:
    """Statistics about file types in a cache location."""
    extension: str
    count: int
    total_size: int

    @property
    def average_size(self) -> float:
        """Calculate average file size."""
        if self.count == 0:
            return 0.0
        return self.total_size / self.count

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "extension": self.extension,
            "count": self.count,
            "total_size": self.total_size,
            "average_size": self.average_size,
        }


@dataclass
class CacheItem:
    """
    Comprehensive cache item with all metadata.

    Represents a scanned cache location with detailed statistics.
    """
    # Basic info
    path: Path
    name: str
    category: Category
    description: str

    # Size information
    size_bytes: int = 0
    file_count: int = 0
    dir_count: int = 0

    # Time information
    last_accessed: datetime | None = None
    last_modified: datetime | None = None
    oldest_file: datetime | None = None
    newest_file: datetime | None = None

    # Status
    exists: bool = True
    is_accessible: bool = True
    is_empty: bool = False
    error_message: str | None = None

    # Cleaning info
    risk_level: RiskLevel = RiskLevel.SAFE
    is_cleanable: bool = True
    clean_contents_only: bool = True
    requires_admin: bool = False

    # App info
    app_specific: bool = False
    app_name: str | None = None

    # Detailed breakdown
    file_types: dict[str, FileTypeStats] = field(default_factory=dict)
    largest_files: list[FileInfo] = field(default_factory=list)

    # Stale detection
    stale_threshold_days: int = 30

    @property
    def age_days(self) -> int:
        """Calculate days since last access."""
        if self.last_accessed is None:
            return 0
        delta = datetime.now() - self.last_accessed
        return delta.days

    @property
    def is_stale(self) -> bool:
        """Check if cache is stale (not accessed recently)."""
        return self.age_days > self.stale_threshold_days

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)

    @property
    def formatted_size(self) -> str:
        """Human-readable size string."""
        if self.size_bytes >= 1024 * 1024 * 1024:
            return f"{self.size_gb:.2f} GB"
        elif self.size_bytes >= 1024 * 1024:
            return f"{self.size_mb:.2f} MB"
        elif self.size_bytes >= 1024:
            return f"{self.size_bytes / 1024:.2f} KB"
        else:
            return f"{self.size_bytes} B"

    @property
    def top_file_types(self) -> list[FileTypeStats]:
        """Get top 5 file types by size."""
        sorted_types = sorted(
            self.file_types.values(),
            key=lambda x: x.total_size,
            reverse=True
        )
        return sorted_types[:5]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "size_bytes": self.size_bytes,
            "size_formatted": self.formatted_size,
            "file_count": self.file_count,
            "dir_count": self.dir_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "oldest_file": self.oldest_file.isoformat() if self.oldest_file else None,
            "newest_file": self.newest_file.isoformat() if self.newest_file else None,
            "age_days": self.age_days,
            "is_stale": self.is_stale,
            "exists": self.exists,
            "is_accessible": self.is_accessible,
            "is_empty": self.is_empty,
            "error_message": self.error_message,
            "risk_level": self.risk_level.value,
            "is_cleanable": self.is_cleanable,
            "clean_contents_only": self.clean_contents_only,
            "requires_admin": self.requires_admin,
            "app_specific": self.app_specific,
            "app_name": self.app_name,
            "file_types": {k: v.to_dict() for k, v in self.file_types.items()},
            "largest_files": [f.to_dict() for f in self.largest_files],
        }

    def to_csv_row(self) -> list:
        """Convert to CSV row."""
        return [
            str(self.path),
            self.name,
            self.category.value,
            self.size_bytes,
            self.formatted_size,
            self.file_count,
            self.age_days,
            self.is_stale,
            self.risk_level.value,
            self.app_name or "",
            self.description,
        ]

    @staticmethod
    def csv_headers() -> list[str]:
        """Get CSV column headers."""
        return [
            "Path",
            "Name",
            "Category",
            "Size (Bytes)",
            "Size (Formatted)",
            "File Count",
            "Age (Days)",
            "Is Stale",
            "Risk Level",
            "App Name",
            "Description",
        ]
