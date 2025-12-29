"""
Platform-specific implementations for CacheKaro.

Provides abstraction layer for different operating systems.
"""

from cachekaro.platforms.base import CachePath, DiskUsage, PlatformBase
from cachekaro.platforms.detector import get_platform, get_platform_name

__all__ = [
    "get_platform",
    "get_platform_name",
    "PlatformBase",
    "CachePath",
    "DiskUsage",
]
