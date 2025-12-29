"""
CacheKaro - Cross-platform Storage & Cache Manager

A production-ready tool to analyze and clean cache/storage on macOS, Linux, and Windows.
Cache Karo! (Hindi-English: "Clean It Up!")
"""

__version__ = "2.1.1"
__author__ = "MOHIT BAGRI"
__license__ = "MIT"

from cachekaro.platforms.detector import get_platform, get_platform_name

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "get_platform",
    "get_platform_name",
]
