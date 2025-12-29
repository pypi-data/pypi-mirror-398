"""
Cache cleaner for CacheKaro.

Provides safe cleaning with multiple modes and backup capabilities.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable

from cachekaro.models.cache_item import CacheItem
from cachekaro.models.scan_result import ScanResult
from cachekaro.platforms.base import RiskLevel


class CleanMode(Enum):
    """Cleaning mode options."""
    INTERACTIVE = "interactive"  # Ask for each item
    AUTO = "auto"                # Clean all without asking
    DRY_RUN = "dry_run"          # Show what would be cleaned


@dataclass
class CleanResult:
    """Result of a cleaning operation."""
    path: Path
    name: str
    success: bool
    size_freed: int
    files_deleted: int
    error_message: str | None = None
    was_skipped: bool = False
    was_backed_up: bool = False
    backup_path: Path | None = None


@dataclass
class CleanSummary:
    """Summary of all cleaning operations."""
    total_items: int = 0
    items_cleaned: int = 0
    items_skipped: int = 0
    items_failed: int = 0
    total_size_freed: int = 0
    total_files_deleted: int = 0
    results: list[CleanResult] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_seconds: float = 0.0

    @property
    def formatted_size_freed(self) -> str:
        """Human-readable size freed."""
        size = self.total_size_freed
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
        elif size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        elif size >= 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size} B"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "total_items": self.total_items,
            "items_cleaned": self.items_cleaned,
            "items_skipped": self.items_skipped,
            "items_failed": self.items_failed,
            "total_size_freed": self.total_size_freed,
            "formatted_size_freed": self.formatted_size_freed,
            "total_files_deleted": self.total_files_deleted,
            "duration_seconds": self.duration_seconds,
            "results": [
                {
                    "path": str(r.path),
                    "name": r.name,
                    "success": r.success,
                    "size_freed": r.size_freed,
                    "files_deleted": r.files_deleted,
                    "error_message": r.error_message,
                    "was_skipped": r.was_skipped,
                }
                for r in self.results
            ],
        }


class Cleaner:
    """
    Safely cleans cache items.

    Features:
    - Multiple cleaning modes (interactive, auto, dry-run)
    - Optional backup before deletion
    - Progress callbacks
    - Detailed results tracking
    """

    def __init__(
        self,
        mode: CleanMode = CleanMode.INTERACTIVE,
        backup_enabled: bool = False,
        backup_dir: Path | None = None,
        max_risk: RiskLevel = RiskLevel.SAFE,
        confirm_callback: Callable[[CacheItem], bool] | None = None,
        progress_callback: Callable[[str, int, int, int], None] | None = None,
    ):
        """
        Initialize the cleaner.

        Args:
            mode: Cleaning mode (interactive, auto, dry_run)
            backup_enabled: Whether to backup before deleting
            backup_dir: Directory for backups (default: temp dir)
            max_risk: Maximum risk level to clean
            confirm_callback: Callback for confirmation (interactive mode)
                              Returns True to proceed, False to skip
            progress_callback: Callback for progress updates
                               (name, current, total, size_freed)
        """
        self.mode = mode
        self.backup_enabled = backup_enabled
        self.backup_dir = backup_dir or Path(tempfile.gettempdir()) / "cachekaro_backup"
        self.max_risk = max_risk
        self.confirm_callback = confirm_callback
        self.progress_callback = progress_callback

    def clean(self, items: list[CacheItem]) -> CleanSummary:
        """
        Clean multiple cache items.

        Args:
            items: List of CacheItem objects to clean

        Returns:
            CleanSummary with results
        """
        summary = CleanSummary(
            total_items=len(items),
            start_time=datetime.now(),
        )

        # Filter by risk level
        risk_order = [RiskLevel.SAFE, RiskLevel.MODERATE, RiskLevel.CAUTION]
        max_index = risk_order.index(self.max_risk)

        filtered_items = [
            item
            for item in items
            if item.is_cleanable
            and item.exists
            and item.is_accessible
            and risk_order.index(item.risk_level) <= max_index
        ]

        for i, item in enumerate(filtered_items):
            result = self._clean_item(item)
            summary.results.append(result)

            if result.success and not result.was_skipped:
                summary.items_cleaned += 1
                summary.total_size_freed += result.size_freed
                summary.total_files_deleted += result.files_deleted
            elif result.was_skipped:
                summary.items_skipped += 1
            else:
                summary.items_failed += 1

            if self.progress_callback:
                self.progress_callback(
                    item.name,
                    i + 1,
                    len(filtered_items),
                    summary.total_size_freed,
                )

        summary.end_time = datetime.now()
        if summary.start_time is not None:
            summary.duration_seconds = (
                summary.end_time - summary.start_time
            ).total_seconds()

        return summary

    def _clean_item(self, item: CacheItem) -> CleanResult:
        """
        Clean a single cache item.

        Args:
            item: CacheItem to clean

        Returns:
            CleanResult with operation details
        """
        result = CleanResult(
            path=item.path,
            name=item.name,
            success=False,
            size_freed=0,
            files_deleted=0,
        )

        # Dry run mode - don't actually delete
        if self.mode == CleanMode.DRY_RUN:
            result.success = True
            result.size_freed = item.size_bytes
            result.files_deleted = item.file_count
            return result

        # Interactive mode - ask for confirmation
        if self.mode == CleanMode.INTERACTIVE:
            if self.confirm_callback:
                if not self.confirm_callback(item):
                    result.was_skipped = True
                    result.success = True
                    return result
            else:
                # No callback provided, skip
                result.was_skipped = True
                result.success = True
                return result

        # Backup if enabled
        if self.backup_enabled:
            try:
                backup_path = self._backup_item(item)
                result.was_backed_up = True
                result.backup_path = backup_path
            except Exception as e:
                result.error_message = f"Backup failed: {e}"
                return result

        # Perform deletion
        try:
            size_before = item.size_bytes
            files_before = item.file_count

            if item.clean_contents_only:
                self._delete_contents(item.path)
            else:
                self._delete_path(item.path)

            result.success = True
            result.size_freed = size_before
            result.files_deleted = files_before

        except PermissionError as e:
            result.error_message = f"Permission denied: {e}"
        except OSError as e:
            result.error_message = f"OS error: {e}"
        except Exception as e:
            result.error_message = f"Unexpected error: {e}"

        return result

    def _delete_contents(self, path: Path) -> None:
        """
        Delete contents of a directory but keep the directory itself.

        Args:
            path: Directory path
        """
        if not path.is_dir():
            return

        for entry in path.iterdir():
            try:
                if entry.is_dir():
                    shutil.rmtree(entry, ignore_errors=True)
                else:
                    entry.unlink(missing_ok=True)
            except (PermissionError, OSError):
                # Skip files we can't delete
                continue

    def _delete_path(self, path: Path) -> None:
        """
        Delete a path (file or directory) completely.

        Args:
            path: Path to delete
        """
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            path.unlink(missing_ok=True)

    def _backup_item(self, item: CacheItem) -> Path:
        """
        Create a backup of a cache item.

        Args:
            item: CacheItem to backup

        Returns:
            Path to the backup
        """
        # Create backup directory if needed
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = item.name.replace("/", "_").replace("\\", "_")
        backup_name = f"{safe_name}_{timestamp}"
        backup_path = self.backup_dir / backup_name

        # Copy to backup
        if item.path.is_dir():
            shutil.copytree(item.path, backup_path, dirs_exist_ok=True)
        else:
            shutil.copy2(item.path, backup_path)

        return backup_path

    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restore a backup to its original location.

        Args:
            backup_path: Path to the backup
            target_path: Original path to restore to

        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_path.is_dir():
                shutil.copytree(backup_path, target_path, dirs_exist_ok=True)
            else:
                shutil.copy2(backup_path, target_path)
            return True
        except Exception:
            return False

    def clean_from_result(
        self,
        result: ScanResult,
        categories: list | None = None,
        min_size_bytes: int = 0,
        stale_only: bool = False,
    ) -> CleanSummary:
        """
        Clean items from a scan result with filters.

        Args:
            result: ScanResult to clean from
            categories: Optional list of categories to clean
            min_size_bytes: Minimum size to clean
            stale_only: Only clean stale items

        Returns:
            CleanSummary with results
        """
        items = result.items

        # Apply filters
        if categories:
            items = [item for item in items if item.category in categories]

        if min_size_bytes > 0:
            items = [item for item in items if item.size_bytes >= min_size_bytes]

        if stale_only:
            items = [item for item in items if item.is_stale]

        return self.clean(items)

    def estimate_savings(self, items: list[CacheItem]) -> dict:
        """
        Estimate potential space savings.

        Args:
            items: List of items to estimate

        Returns:
            Dictionary with savings estimates
        """
        risk_order = [RiskLevel.SAFE, RiskLevel.MODERATE, RiskLevel.CAUTION]
        max_index = risk_order.index(self.max_risk)

        cleanable = [
            item
            for item in items
            if item.is_cleanable
            and item.exists
            and risk_order.index(item.risk_level) <= max_index
        ]

        total_size = sum(item.size_bytes for item in cleanable)
        total_files = sum(item.file_count for item in cleanable)

        # Breakdown by risk
        safe_size = sum(
            item.size_bytes
            for item in cleanable
            if item.risk_level == RiskLevel.SAFE
        )
        moderate_size = sum(
            item.size_bytes
            for item in cleanable
            if item.risk_level == RiskLevel.MODERATE
        )

        return {
            "total_items": len(cleanable),
            "total_size": total_size,
            "total_files": total_files,
            "safe_size": safe_size,
            "moderate_size": moderate_size,
        }
