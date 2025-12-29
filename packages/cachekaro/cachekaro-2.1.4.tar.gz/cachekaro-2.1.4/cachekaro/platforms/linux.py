"""
Linux platform implementation for CacheKaro.

Provides Linux-specific cache paths, system operations, and utilities.
Follows XDG Base Directory Specification.
"""

from __future__ import annotations

import getpass
import os
import platform
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

from cachekaro.platforms.base import (
    CachePath,
    Category,
    DiskUsage,
    PlatformBase,
    PlatformInfo,
    RiskLevel,
    identify_app_from_path,
)


class LinuxPlatform(PlatformBase):
    """Linux-specific platform implementation."""

    @property
    def name(self) -> str:
        return "Linux"

    def get_platform_info(self) -> PlatformInfo:
        """Get detailed Linux platform information."""
        if self._platform_info is not None:
            return self._platform_info

        # Try to get distribution info
        try:
            with open("/etc/os-release") as f:
                lines = f.readlines()
                distro = "Linux"
                version = ""
                for line in lines:
                    if line.startswith("PRETTY_NAME="):
                        distro = line.split("=")[1].strip().strip('"')
                    elif line.startswith("VERSION_ID="):
                        version = line.split("=")[1].strip().strip('"')
        except (FileNotFoundError, PermissionError):
            distro = "Linux"
            version = platform.release()

        self._platform_info = PlatformInfo(
            name=distro,
            version=version,
            architecture=platform.machine(),
            hostname=socket.gethostname(),
            username=getpass.getuser(),
            home_dir=self.get_home_dir(),
            temp_dir=self.get_temp_dir(),
        )
        return self._platform_info

    def get_home_dir(self) -> Path:
        """Get user home directory."""
        return Path.home()

    def get_temp_dir(self) -> Path:
        """Get system temp directory."""
        return Path(tempfile.gettempdir())

    def get_trash_path(self) -> Path | None:
        """Get Linux Trash path (FreeDesktop.org spec)."""
        # Check XDG_DATA_HOME first
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            trash = Path(xdg_data) / "Trash"
        else:
            trash = self.get_home_dir() / ".local" / "share" / "Trash"

        if trash.exists():
            return trash

        # Fallback to ~/.Trash
        fallback = self.get_home_dir() / ".Trash"
        return fallback if fallback.exists() else None

    def get_config_dir(self) -> Path:
        """Get configuration directory (XDG spec)."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / "cachekaro"
        else:
            config_dir = self.get_home_dir() / ".config" / "cachekaro"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _get_xdg_cache_home(self) -> Path:
        """Get XDG cache home directory."""
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache)
        return self.get_home_dir() / ".cache"

    def _get_xdg_config_home(self) -> Path:
        """Get XDG config home directory."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config)
        return self.get_home_dir() / ".config"

    def _get_xdg_data_home(self) -> Path:
        """Get XDG data home directory."""
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data)
        return self.get_home_dir() / ".local" / "share"

    def get_disk_usage(self, path: str = "/") -> DiskUsage:
        """Get disk usage for the specified path."""
        usage = shutil.disk_usage(path)
        return DiskUsage(
            total_bytes=usage.total,
            used_bytes=usage.used,
            free_bytes=usage.free,
            mount_point=path,
        )

    def flush_dns_cache(self) -> tuple[bool, str]:
        """
        Flush Linux DNS cache.

        Linux DNS caching varies by distribution and configuration.
        """
        commands_to_try = [
            # systemd-resolved (Ubuntu, Fedora, etc.)
            ["sudo", "systemd-resolve", "--flush-caches"],
            ["sudo", "resolvectl", "flush-caches"],
            # nscd
            ["sudo", "systemctl", "restart", "nscd"],
            # dnsmasq
            ["sudo", "systemctl", "restart", "dnsmasq"],
        ]

        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return True, f"DNS cache flushed using {cmd[1]}"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return False, "No DNS cache service found or flush failed"

    def is_admin(self) -> bool:
        """Check if running as root."""
        # os.geteuid() is Unix-only, use getattr for type safety
        geteuid = getattr(os, "geteuid", None)
        if geteuid is not None:
            return bool(geteuid() == 0)
        return False

    def get_cache_paths(self) -> list[CachePath]:
        """
        Get all Linux cache paths using automatic discovery.

        This method automatically discovers all application caches in standard
        Linux cache locations following XDG Base Directory Specification.
        """
        if self._cache_paths:
            return self._cache_paths

        home = self.get_home_dir()
        cache_home = self._get_xdg_cache_home()
        config_home = self._get_xdg_config_home()
        data_home = self._get_xdg_data_home()
        paths: list[CachePath] = []

        # ============================================================
        # AUTO-DISCOVER: ~/.cache (XDG Cache Home)
        # ============================================================
        if cache_home.exists():
            # Exclude system caches we handle separately
            exclude = ["cachekaro", "TemporaryItems"]
            discovered = self.discover_caches_in_directory(cache_home, exclude_patterns=exclude)
            paths.extend(discovered)

        # ============================================================
        # SPECIFIC: VS Code and variants in ~/.config
        # ============================================================
        vscode_apps = [
            ("Code", "VS Code"),
            ("Cursor", "Cursor"),
            ("VSCodium", "VSCodium"),
            ("Code - OSS", "Code OSS"),
        ]
        for folder, name in vscode_apps:
            base = config_home / folder
            if base.exists():
                for cache_folder in ["Cache", "CachedData", "CachedExtensionVSIXs", "CachedProfilesData"]:
                    cache_path = base / cache_folder
                    if cache_path.exists():
                        paths.append(CachePath(
                            path=cache_path,
                            name=f"{name} {cache_folder}",
                            category=Category.DEVELOPMENT,
                            description=f"{name} {cache_folder}",
                            risk_level=RiskLevel.SAFE,
                            app_specific=True,
                            app_name=name,
                        ))

        # Browser Service Workers in ~/.config
        browsers = [
            ("google-chrome", "Chrome"),
            ("chromium", "Chromium"),
            ("BraveSoftware/Brave-Browser", "Brave"),
            ("microsoft-edge", "Edge"),
        ]
        for folder, name in browsers:
            sw_path = config_home / folder / "Default" / "Service Worker"
            if sw_path.exists():
                paths.append(CachePath(
                    path=sw_path,
                    name=f"{name} Service Workers",
                    category=Category.BROWSER,
                    description=f"{name} web app service workers",
                    risk_level=RiskLevel.SAFE,
                    app_specific=True,
                    app_name=name,
                ))

        # ============================================================
        # SPECIFIC: Development tool caches (fixed locations)
        # ============================================================
        dev_caches = [
            (home / ".npm" / "_cacache", "npm Cache", "npm package manager cache"),
            (home / ".gradle" / "caches", "Gradle Cache", "Gradle build system cache"),
            (home / ".m2" / "repository", "Maven Repository", "Maven dependency cache"),
            (home / ".cargo" / "registry" / "cache", "Cargo Cache", "Rust Cargo package cache"),
            (home / "go" / "pkg" / "mod" / "cache", "Go Module Cache", "Go module download cache"),
            (home / ".docker" / "buildx", "Docker Buildx Cache", "Docker buildx builder cache"),
            (home / ".composer" / "cache", "Composer Cache", "PHP Composer package cache"),
            (home / ".gem", "RubyGems Cache", "Ruby gems cache"),
            (home / ".bundle" / "cache", "Bundler Cache", "Ruby Bundler cache"),
            (home / ".pub-cache", "Dart/Flutter Cache", "Dart and Flutter package cache"),
            (home / ".nuget" / "packages", "NuGet Cache", ".NET NuGet package cache"),
            (home / ".android" / "cache", "Android SDK Cache", "Android SDK cache"),
        ]

        for path, name, description in dev_caches:
            if path.exists():
                paths.append(CachePath(
                    path=path,
                    name=name,
                    category=Category.DEVELOPMENT,
                    description=description,
                    risk_level=RiskLevel.SAFE,
                ))

        # ============================================================
        # AUTO-DISCOVER: ~/.local/share (XDG Data Home) logs
        # ============================================================
        if data_home.exists():
            for item in data_home.iterdir():
                if item.is_dir() and item.name.lower() in ["jetbrains", "logs"]:
                    try:
                        if any(item.iterdir()):
                            app_name, _ = identify_app_from_path(item.name)
                            paths.append(CachePath(
                                path=item,
                                name=f"{app_name} Data",
                                category=Category.LOGS,
                                description=f"Application data for {app_name}",
                                risk_level=RiskLevel.MODERATE,
                                app_specific=True,
                                app_name=app_name,
                            ))
                    except PermissionError:
                        continue

        # X Session errors log
        xsession_errors = home / ".xsession-errors"
        if xsession_errors.exists():
            paths.append(CachePath(
                path=xsession_errors,
                name="X Session Errors",
                category=Category.LOGS,
                description="X Window session error log",
                risk_level=RiskLevel.SAFE,
                clean_contents_only=False,
            ))

        # ============================================================
        # GAME CACHES
        # ============================================================
        paths.extend(self.get_game_cache_paths())

        # ============================================================
        # TRASH
        # ============================================================
        trash_path = self.get_trash_path()
        if trash_path:
            for subfolder in ["files", "info"]:
                trash_sub = trash_path / subfolder
                if trash_sub.exists():
                    paths.append(CachePath(
                        path=trash_sub,
                        name=f"Trash {subfolder.capitalize()}",
                        category=Category.TRASH,
                        description=f"Trash {subfolder}",
                        risk_level=RiskLevel.SAFE,
                    ))

        # ============================================================
        # DOWNLOADS
        # ============================================================
        downloads_path = home / "Downloads"
        xdg_downloads = os.environ.get("XDG_DOWNLOAD_DIR")
        if xdg_downloads:
            downloads_path = Path(xdg_downloads)

        if downloads_path.exists():
            paths.append(CachePath(
                path=downloads_path,
                name="Downloads",
                category=Category.DOWNLOADS,
                description="Downloaded files (review before deleting!)",
                risk_level=RiskLevel.CAUTION,
            ))

        # ============================================================
        # SNAP & FLATPAK CACHES
        # ============================================================
        snap_path = home / "snap"
        if snap_path.exists():
            paths.append(CachePath(
                path=snap_path,
                name="Snap Packages",
                category=Category.CONTAINER,
                description="Snap package data (use with caution)",
                risk_level=RiskLevel.CAUTION,
            ))

        flatpak_path = data_home / "flatpak"
        if flatpak_path.exists():
            paths.append(CachePath(
                path=flatpak_path,
                name="Flatpak Data",
                category=Category.CONTAINER,
                description="Flatpak application data",
                risk_level=RiskLevel.CAUTION,
            ))

        self._cache_paths = paths
        return self._cache_paths

    def get_game_cache_paths(self) -> list[CachePath]:
        """Get Linux game-specific cache paths."""
        home = self.get_home_dir()
        data_home = self._get_xdg_data_home()
        paths: list[CachePath] = []

        # Steam
        steam_paths = [
            (home / ".steam" / "steam" / "appcache", "Steam App Cache", "Steam application cache"),
            (home / ".steam" / "steam" / "depotcache", "Steam Depot Cache", "Steam game depot cache"),
            (home / ".steam" / "steam" / "htmlcache", "Steam HTML Cache", "Steam browser cache"),
            (data_home / "Steam" / "appcache", "Steam App Cache", "Steam application cache"),
        ]
        for path, name, desc in steam_paths:
            if path.exists():
                paths.append(CachePath(
                    path=path,
                    name=name,
                    category=Category.GAME,
                    description=desc,
                    risk_level=RiskLevel.SAFE,
                    app_specific=True,
                    app_name="Steam",
                ))

        # Proton/Wine prefixes cache
        proton_cache = home / ".steam" / "steam" / "steamapps" / "shadercache"
        if proton_cache.exists():
            paths.append(CachePath(
                path=proton_cache,
                name="Steam Shader Cache",
                category=Category.GAME,
                description="Steam/Proton shader compilation cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Steam",
            ))

        # Lutris
        lutris_cache = home / ".cache" / "lutris"
        if lutris_cache.exists():
            paths.append(CachePath(
                path=lutris_cache,
                name="Lutris Cache",
                category=Category.GAME,
                description="Lutris game manager cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Lutris",
            ))

        # Heroic Games Launcher (Epic Games on Linux)
        heroic_cache = home / ".config" / "heroic" / "store_cache"
        if heroic_cache.exists():
            paths.append(CachePath(
                path=heroic_cache,
                name="Heroic Games Cache",
                category=Category.GAME,
                description="Heroic Games Launcher (Epic) cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Heroic",
            ))

        # Minecraft
        minecraft_paths = [
            (home / ".minecraft" / "assets", "Minecraft Assets", "Minecraft game assets cache"),
            (home / ".minecraft" / "versions", "Minecraft Versions", "Minecraft version cache"),
        ]
        for path, name, desc in minecraft_paths:
            if path.exists():
                paths.append(CachePath(
                    path=path,
                    name=name,
                    category=Category.GAME,
                    description=desc,
                    risk_level=RiskLevel.MODERATE,
                    app_specific=True,
                    app_name="Minecraft",
                ))

        # Unity
        unity_cache = home / ".cache" / "unity3d"
        if unity_cache.exists():
            paths.append(CachePath(
                path=unity_cache,
                name="Unity Editor Cache",
                category=Category.GAME,
                description="Unity game engine editor cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Unity",
            ))

        # Wine prefixes
        wine_cache = home / ".wine" / "drive_c" / "windows" / "temp"
        if wine_cache.exists():
            paths.append(CachePath(
                path=wine_cache,
                name="Wine Temp",
                category=Category.GAME,
                description="Wine Windows emulation temp files",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Wine",
            ))

        return paths
