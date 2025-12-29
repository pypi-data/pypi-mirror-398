"""
File and directory scanner for CacheKaro.

Provides efficient scanning with metadata collection.
"""

from __future__ import annotations

import os
import stat
from collections import defaultdict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable

from cachekaro.models.cache_item import CacheItem, FileInfo, FileTypeStats
from cachekaro.platforms.base import CachePath


class Scanner:
    """
    Scans directories and collects comprehensive metadata.

    Features:
    - Parallel scanning for performance
    - Detailed file statistics
    - File type breakdown
    - Largest file identification
    - Stale cache detection
    """

    def __init__(
        self,
        max_workers: int = 4,
        collect_file_details: bool = True,
        max_largest_files: int = 10,
        stale_threshold_days: int = 30,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ):
        """
        Initialize the scanner.

        Args:
            max_workers: Number of parallel workers for scanning
            collect_file_details: Whether to collect detailed file info
            max_largest_files: Number of largest files to track
            stale_threshold_days: Days after which a file is considered stale
            progress_callback: Callback function for progress updates
                               (name, current, total)
        """
        self.max_workers = max_workers
        self.collect_file_details = collect_file_details
        self.max_largest_files = max_largest_files
        self.stale_threshold_days = stale_threshold_days
        self.progress_callback = progress_callback

    def scan_path(self, cache_path: CachePath) -> CacheItem:
        """
        Scan a single cache path and collect metadata.

        Args:
            cache_path: The cache path to scan

        Returns:
            CacheItem with complete metadata
        """
        item = CacheItem(
            path=cache_path.path,
            name=cache_path.name,
            category=cache_path.category,
            description=cache_path.description,
            risk_level=cache_path.risk_level,
            is_cleanable=True,
            clean_contents_only=cache_path.clean_contents_only,
            requires_admin=cache_path.requires_admin,
            app_specific=cache_path.app_specific,
            app_name=cache_path.app_name,
            stale_threshold_days=self.stale_threshold_days,
        )

        # Check if path exists
        if not cache_path.path.exists():
            item.exists = False
            item.is_accessible = False
            item.is_cleanable = False
            return item

        # Check accessibility
        if not cache_path.is_accessible():
            item.is_accessible = False
            item.is_cleanable = False
            item.error_message = "Permission denied"
            return item

        try:
            self._scan_directory(cache_path.path, item)
        except PermissionError as e:
            item.is_accessible = False
            item.error_message = f"Permission denied: {e}"
        except OSError as e:
            item.error_message = f"OS error: {e}"

        # Check if empty
        item.is_empty = item.size_bytes == 0 and item.file_count == 0

        return item

    def _scan_directory(self, path: Path, item: CacheItem) -> None:
        """
        Recursively scan a directory and update the cache item.

        Args:
            path: Directory path to scan
            item: CacheItem to update with statistics
        """
        file_types: dict[str, FileTypeStats] = defaultdict(
            lambda: FileTypeStats(extension="", count=0, total_size=0)
        )
        largest_files: list[FileInfo] = []
        oldest_time: datetime | None = None
        newest_time: datetime | None = None
        last_accessed: datetime | None = None

        try:
            for entry in self._walk_directory(path):
                try:
                    stat_info = entry.stat(follow_symlinks=False)

                    if stat.S_ISREG(stat_info.st_mode):
                        # Regular file
                        item.file_count += 1
                        item.size_bytes += stat_info.st_size

                        # File extension stats
                        ext = Path(entry.name).suffix.lower() or "(no extension)"
                        if ext not in file_types:
                            file_types[ext] = FileTypeStats(
                                extension=ext, count=0, total_size=0
                            )
                        file_types[ext].count += 1
                        file_types[ext].total_size += stat_info.st_size

                        # Time tracking
                        try:
                            mtime = datetime.fromtimestamp(stat_info.st_mtime)
                            atime = datetime.fromtimestamp(stat_info.st_atime)

                            if oldest_time is None or mtime < oldest_time:
                                oldest_time = mtime
                            if newest_time is None or mtime > newest_time:
                                newest_time = mtime
                            if last_accessed is None or atime > last_accessed:
                                last_accessed = atime
                        except (ValueError, OSError):
                            pass

                        # Track largest files
                        if self.collect_file_details:
                            file_info = FileInfo(
                                path=Path(entry.path),
                                name=entry.name,
                                size_bytes=stat_info.st_size,
                                extension=ext,
                            )
                            try:
                                file_info.last_modified = datetime.fromtimestamp(
                                    stat_info.st_mtime
                                )
                                file_info.last_accessed = datetime.fromtimestamp(
                                    stat_info.st_atime
                                )
                                file_info.created_time = datetime.fromtimestamp(
                                    stat_info.st_ctime
                                )
                            except (ValueError, OSError):
                                pass

                            # Keep track of largest files
                            largest_files.append(file_info)
                            if len(largest_files) > self.max_largest_files * 2:
                                # Periodically trim to avoid memory bloat
                                largest_files.sort(
                                    key=lambda x: x.size_bytes, reverse=True
                                )
                                largest_files = largest_files[: self.max_largest_files]

                    elif stat.S_ISDIR(stat_info.st_mode):
                        # Directory
                        item.dir_count += 1

                except (PermissionError, OSError):
                    # Skip files we can't access
                    continue

        except PermissionError:
            item.is_accessible = False
            item.error_message = "Permission denied during scan"
            return

        # Finalize results
        item.file_types = dict(file_types)
        item.oldest_file = oldest_time
        item.newest_file = newest_time
        item.last_accessed = last_accessed
        item.last_modified = newest_time

        # Get final largest files
        largest_files.sort(key=lambda x: x.size_bytes, reverse=True)
        item.largest_files = largest_files[: self.max_largest_files]

    def _walk_directory(self, path: Path) -> Iterator[os.DirEntry[str]]:
        """
        Walk directory tree yielding DirEntry objects.

        Uses os.scandir for better performance than os.walk.
        """
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    yield entry
                    if entry.is_dir(follow_symlinks=False):
                        try:
                            yield from self._walk_directory(Path(entry.path))
                        except (PermissionError, OSError):
                            continue
        except (PermissionError, OSError):
            return

    def scan_paths(self, cache_paths: list[CachePath]) -> list[CacheItem]:
        """
        Scan multiple cache paths in parallel.

        Args:
            cache_paths: List of cache paths to scan

        Returns:
            List of CacheItem objects with metadata
        """
        items: list[CacheItem] = []
        total = len(cache_paths)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self.scan_path, cp): cp for cp in cache_paths
            }

            for i, future in enumerate(as_completed(future_to_path)):
                cache_path = future_to_path[future]
                try:
                    item = future.result()
                    items.append(item)

                    if self.progress_callback:
                        self.progress_callback(cache_path.name, i + 1, total)
                except Exception as e:
                    # Create error item
                    error_item = CacheItem(
                        path=cache_path.path,
                        name=cache_path.name,
                        category=cache_path.category,
                        description=cache_path.description,
                        exists=False,
                        is_accessible=False,
                        error_message=str(e),
                    )
                    items.append(error_item)

        return items

    def get_directory_size(self, path: Path) -> int:
        """
        Get the total size of a directory.

        Args:
            path: Directory path

        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for entry in self._walk_directory(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total_size += entry.stat(follow_symlinks=False).st_size
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass
        return total_size

    def count_files(self, path: Path) -> tuple[int, int]:
        """
        Count files and directories in a path.

        Args:
            path: Directory path

        Returns:
            Tuple of (file_count, dir_count)
        """
        file_count = 0
        dir_count = 0
        try:
            for entry in self._walk_directory(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        file_count += 1
                    elif entry.is_dir(follow_symlinks=False):
                        dir_count += 1
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass
        return file_count, dir_count
