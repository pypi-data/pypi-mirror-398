"""
macOS platform implementation for CacheKaro.

Provides macOS-specific cache paths, system operations, and utilities.
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


class MacOSPlatform(PlatformBase):
    """macOS-specific platform implementation."""

    @property
    def name(self) -> str:
        return "macOS"

    def get_platform_info(self) -> PlatformInfo:
        """Get detailed macOS platform information."""
        if self._platform_info is not None:
            return self._platform_info

        self._platform_info = PlatformInfo(
            name="macOS",
            version=platform.mac_ver()[0],
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
        """Get macOS Trash path."""
        trash = self.get_home_dir() / ".Trash"
        return trash if trash.exists() else None

    def get_config_dir(self) -> Path:
        """Get configuration directory (XDG-style on macOS)."""
        config_dir = self.get_home_dir() / ".config" / "cachekaro"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

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
        Flush macOS DNS cache.

        Requires sudo privileges.
        """
        try:
            subprocess.run(
                ["sudo", "dscacheutil", "-flushcache"],
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["sudo", "killall", "-HUP", "mDNSResponder"],
                capture_output=True,
                check=True,
            )
            return True, "DNS cache flushed successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to flush DNS cache: {e}"
        except FileNotFoundError:
            return False, "DNS flush commands not available"

    def is_admin(self) -> bool:
        """Check if running as root."""
        # os.geteuid() is Unix-only, use getattr for type safety
        geteuid = getattr(os, "geteuid", None)
        if geteuid is not None:
            return bool(geteuid() == 0)
        return False

    def get_cache_paths(self) -> list[CachePath]:
        """
        Get all macOS cache paths using automatic discovery.

        This method automatically discovers all application caches in standard
        macOS cache locations, identifying apps by their folder names.
        """
        if self._cache_paths:
            return self._cache_paths

        home = self.get_home_dir()
        library = home / "Library"
        paths: list[CachePath] = []

        # ============================================================
        # AUTO-DISCOVER: ~/Library/Caches (Main cache directory)
        # ============================================================
        caches = library / "Caches"
        if caches.exists():
            # Exclude our own cache and temporary system folders
            exclude = ["cachekaro", "TemporaryItems", "CloudKit"]
            discovered = self.discover_caches_in_directory(caches, exclude_patterns=exclude)
            paths.extend(discovered)

        # ============================================================
        # AUTO-DISCOVER: ~/.cache (XDG-style cache)
        # ============================================================
        hidden_cache = home / ".cache"
        if hidden_cache.exists():
            discovered = self.discover_caches_in_directory(hidden_cache)
            paths.extend(discovered)

        # ============================================================
        # AUTO-DISCOVER: ~/Library/Logs
        # ============================================================
        logs = library / "Logs"
        if logs.exists():
            for item in logs.iterdir():
                if item.is_dir():
                    try:
                        if any(item.iterdir()):
                            app_name, _ = identify_app_from_path(item.name)
                            paths.append(CachePath(
                                path=item,
                                name=f"{app_name} Logs",
                                category=Category.LOGS,
                                description=f"Log files for {app_name}",
                                risk_level=RiskLevel.SAFE,
                                app_specific=True,
                                app_name=app_name,
                            ))
                    except PermissionError:
                        continue

        # ============================================================
        # SPECIFIC: Application Support caches (need deeper paths)
        # ============================================================
        app_support = library / "Application Support"

        # VS Code and variants
        vscode_apps = [
            ("Code", "VS Code"),
            ("Cursor", "Cursor"),
            ("VSCodium", "VSCodium"),
        ]
        for folder, name in vscode_apps:
            base = app_support / folder
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

        # Chrome Service Workers
        chrome_sw = app_support / "Google" / "Chrome" / "Default" / "Service Worker"
        if chrome_sw.exists():
            paths.append(CachePath(
                path=chrome_sw,
                name="Chrome Service Workers",
                category=Category.BROWSER,
                description="Chrome web app service workers (PWA cache)",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Chrome",
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
            (home / ".cocoapods" / "repos", "CocoaPods Repos", "CocoaPods repository cache"),
            (home / ".pub-cache", "Dart/Flutter Cache", "Dart and Flutter package cache"),
            (home / ".nuget" / "packages", "NuGet Cache", ".NET NuGet package cache"),
            (home / ".composer" / "cache", "Composer Cache", "PHP Composer package cache"),
            (home / ".gem", "RubyGems Cache", "Ruby gems cache"),
            (home / ".bundle" / "cache", "Bundler Cache", "Ruby Bundler cache"),
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
        # SPECIFIC: Xcode (large development caches)
        # ============================================================
        developer = library / "Developer"
        xcode_caches = [
            (developer / "Xcode" / "DerivedData", "Xcode DerivedData", "Xcode build artifacts (can be very large!)"),
            (developer / "Xcode" / "Archives", "Xcode Archives", "Xcode archived builds (review before deleting)"),
            (developer / "CoreSimulator" / "Caches", "iOS Simulator Cache", "iOS Simulator cache"),
            (developer / "CoreSimulator" / "Devices", "iOS Simulator Devices", "iOS Simulator device data"),
        ]

        for path, name, description in xcode_caches:
            if path.exists():
                risk = RiskLevel.MODERATE if "Archives" in name or "Devices" in name else RiskLevel.SAFE
                paths.append(CachePath(
                    path=path,
                    name=name,
                    category=Category.DEVELOPMENT,
                    description=description,
                    risk_level=risk,
                    app_specific=True,
                    app_name="Xcode",
                ))

        # ============================================================
        # GAME CACHES
        # ============================================================
        paths.extend(self.get_game_cache_paths())

        # ============================================================
        # TRASH & DOWNLOADS
        # ============================================================
        trash = home / ".Trash"
        if trash.exists():
            paths.append(CachePath(
                path=trash,
                name="Trash",
                category=Category.TRASH,
                description="Files in Trash (permanently delete)",
                risk_level=RiskLevel.SAFE,
            ))

        downloads = home / "Downloads"
        if downloads.exists():
            paths.append(CachePath(
                path=downloads,
                name="Downloads",
                category=Category.DOWNLOADS,
                description="Downloaded files (review before deleting!)",
                risk_level=RiskLevel.CAUTION,
            ))

        # NOTE: ~/Library/Containers is NOT included because it contains
        # sandboxed app data (iMessage, Mail, etc.), not cache.

        self._cache_paths = paths
        return self._cache_paths

    def get_game_cache_paths(self) -> list[CachePath]:
        """Get macOS game-specific cache paths."""
        home = self.get_home_dir()
        library = home / "Library"
        app_support = library / "Application Support"
        paths: list[CachePath] = []

        # Steam
        steam_paths = [
            (app_support / "Steam" / "appcache", "Steam App Cache", "Steam application cache"),
            (app_support / "Steam" / "depotcache", "Steam Depot Cache", "Steam game depot cache"),
            (app_support / "Steam" / "htmlcache", "Steam HTML Cache", "Steam browser cache"),
            (library / "Caches" / "com.valvesoftware.steam", "Steam Cache", "Steam main cache"),
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

        # Epic Games
        epic_cache = library / "Caches" / "com.epicgames.EpicGamesLauncher"
        if epic_cache.exists():
            paths.append(CachePath(
                path=epic_cache,
                name="Epic Games Cache",
                category=Category.GAME,
                description="Epic Games Launcher cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Epic Games",
            ))

        # Riot Games (Valorant, League of Legends)
        riot_paths = [
            (app_support / "Riot Games", "Riot Games Data", "Riot Games client data"),
            (library / "Caches" / "com.riotgames.RiotClient", "Riot Client Cache", "Riot Client cache"),
        ]
        for path, name, desc in riot_paths:
            if path.exists():
                paths.append(CachePath(
                    path=path,
                    name=name,
                    category=Category.GAME,
                    description=desc,
                    risk_level=RiskLevel.MODERATE,
                    app_specific=True,
                    app_name="Riot Games",
                ))

        # Battle.net / Blizzard
        blizzard_cache = app_support / "Battle.net" / "Cache"
        if blizzard_cache.exists():
            paths.append(CachePath(
                path=blizzard_cache,
                name="Battle.net Cache",
                category=Category.GAME,
                description="Blizzard Battle.net cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Battle.net",
            ))

        # Minecraft
        minecraft_paths = [
            (app_support / "minecraft" / "assets", "Minecraft Assets", "Minecraft game assets cache"),
            (app_support / "minecraft" / "versions", "Minecraft Versions", "Minecraft version cache"),
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
        unity_cache = library / "Caches" / "com.unity3d.UnityEditor"
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

        return paths
