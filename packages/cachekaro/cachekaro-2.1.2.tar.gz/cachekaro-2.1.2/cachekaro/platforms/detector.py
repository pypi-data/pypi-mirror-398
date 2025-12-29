"""
Platform detection module for CacheKaro.

Automatically detects the current operating system and returns
the appropriate platform implementation.
"""

from __future__ import annotations

import platform
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cachekaro.platforms.base import PlatformBase


def get_platform_name() -> str:
    """
    Get the name of the current platform.

    Returns:
        'macos', 'linux', 'windows', or 'unknown'
    """
    system = platform.system().lower()

    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def get_platform() -> PlatformBase:
    """
    Get the platform implementation for the current OS.

    Returns:
        Platform-specific implementation of PlatformBase.

    Raises:
        NotImplementedError: If the current platform is not supported.
    """
    platform_name = get_platform_name()

    if platform_name == "macos":
        from cachekaro.platforms.macos import MacOSPlatform
        return MacOSPlatform()

    elif platform_name == "linux":
        from cachekaro.platforms.linux import LinuxPlatform
        return LinuxPlatform()

    elif platform_name == "windows":
        from cachekaro.platforms.windows import WindowsPlatform
        return WindowsPlatform()

    else:
        raise NotImplementedError(
            f"Platform '{platform.system()}' is not supported. "
            f"CacheKaro supports macOS, Linux, and Windows."
        )


def get_system_info() -> dict:
    """
    Get detailed system information.

    Returns:
        Dictionary with system details.
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "platform": get_platform_name(),
    }


def is_wsl() -> bool:
    """
    Check if running under Windows Subsystem for Linux.

    Returns:
        True if running in WSL, False otherwise.
    """
    if get_platform_name() != "linux":
        return False

    try:
        with open("/proc/version") as f:
            version = f.read().lower()
            return "microsoft" in version or "wsl" in version
    except (FileNotFoundError, PermissionError):
        return False


def is_docker() -> bool:
    """
    Check if running inside a Docker container.

    Returns:
        True if running in Docker, False otherwise.
    """
    try:
        with open("/proc/1/cgroup") as f:
            return "docker" in f.read()
    except (FileNotFoundError, PermissionError):
        pass

    # Check for .dockerenv file
    from pathlib import Path
    return Path("/.dockerenv").exists()
