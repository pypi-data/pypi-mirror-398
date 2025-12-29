"""
Windows platform implementation for CacheKaro.

Provides Windows-specific cache paths, system operations, and utilities.
"""

from __future__ import annotations

import ctypes
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


class WindowsPlatform(PlatformBase):
    """Windows-specific platform implementation."""

    @property
    def name(self) -> str:
        return "Windows"

    def get_platform_info(self) -> PlatformInfo:
        """Get detailed Windows platform information."""
        if self._platform_info is not None:
            return self._platform_info

        self._platform_info = PlatformInfo(
            name="Windows",
            version=platform.version(),
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

    def _get_appdata(self) -> Path:
        """Get APPDATA directory (Roaming)."""
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata)
        return self.get_home_dir() / "AppData" / "Roaming"

    def _get_localappdata(self) -> Path:
        """Get LOCALAPPDATA directory."""
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata)
        return self.get_home_dir() / "AppData" / "Local"

    def _get_programdata(self) -> Path:
        """Get ProgramData directory."""
        programdata = os.environ.get("PROGRAMDATA")
        if programdata:
            return Path(programdata)
        return Path("C:/ProgramData")

    def get_trash_path(self) -> Path | None:
        """
        Get Windows Recycle Bin path.

        Note: Windows Recycle Bin is complex and per-drive.
        We can't easily clean it programmatically without special APIs.
        """
        # Windows Recycle Bin is special - return None and handle separately
        return None

    def get_config_dir(self) -> Path:
        """Get configuration directory for CacheKaro."""
        config_dir = self._get_appdata() / "cachekaro"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def get_disk_usage(self, path: str = "C:/") -> DiskUsage:
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
        Flush Windows DNS cache.

        Uses ipconfig /flushdns command.
        """
        try:
            subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True, "DNS cache flushed successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to flush DNS cache: {e}"
        except FileNotFoundError:
            return False, "ipconfig command not found"

    def is_admin(self) -> bool:
        """Check if running as Administrator."""
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            return False

    def empty_recycle_bin(self) -> tuple[bool, str]:
        """
        Empty the Windows Recycle Bin.

        Uses PowerShell to clear the recycle bin.
        """
        try:
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
                ],
                capture_output=True,
                text=True,
            )
            return True, "Recycle Bin emptied successfully"
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return False, f"Failed to empty Recycle Bin: {e}"

    def get_cache_paths(self) -> list[CachePath]:
        """
        Get all Windows cache paths using automatic discovery.

        This method automatically discovers all application caches in standard
        Windows cache locations (AppData, LocalAppData, Temp).
        """
        if self._cache_paths:
            return self._cache_paths

        home = self.get_home_dir()
        appdata = self._get_appdata()
        localappdata = self._get_localappdata()
        temp = self.get_temp_dir()
        paths: list[CachePath] = []

        # ============================================================
        # TEMP DIRECTORIES - Safe
        # ============================================================
        if temp.exists():
            paths.append(CachePath(
                path=temp,
                name="User Temp",
                category=Category.SYSTEM_CACHE,
                description="User temporary files",
                risk_level=RiskLevel.SAFE,
            ))

        system_temp = Path("C:/Windows/Temp")
        if system_temp.exists():
            paths.append(CachePath(
                path=system_temp,
                name="System Temp",
                category=Category.SYSTEM_CACHE,
                description="System temporary files (requires admin)",
                risk_level=RiskLevel.SAFE,
                requires_admin=True,
            ))

        # ============================================================
        # AUTO-DISCOVER: LocalAppData caches
        # ============================================================
        if localappdata.exists():
            # Scan for app folders with cache directories
            for item in localappdata.iterdir():
                if not item.is_dir():
                    continue
                # Skip system folders
                if item.name.lower() in ["microsoft", "packages", "programs", "temp"]:
                    continue
                # Look for cache subdirectories
                cache_subfolders = ["Cache", "cache", "Caches", "GPUCache", "Code Cache"]
                for subfolder in cache_subfolders:
                    cache_path = item / subfolder
                    if cache_path.exists() and cache_path.is_dir():
                        try:
                            if any(cache_path.iterdir()):
                                app_name, category = identify_app_from_path(item.name)
                                paths.append(CachePath(
                                    path=cache_path,
                                    name=f"{app_name} Cache",
                                    category=category,
                                    description=f"Cache for {app_name}",
                                    risk_level=RiskLevel.SAFE,
                                    app_specific=True,
                                    app_name=app_name,
                                ))
                        except PermissionError:
                            continue

        # ============================================================
        # AUTO-DISCOVER: AppData (Roaming) caches
        # ============================================================
        if appdata.exists():
            for item in appdata.iterdir():
                if not item.is_dir():
                    continue
                # Look for cache subdirectories
                cache_subfolders = ["Cache", "cache", "Caches", "Code Cache", "Storage"]
                for subfolder in cache_subfolders:
                    cache_path = item / subfolder
                    if cache_path.exists() and cache_path.is_dir():
                        try:
                            if any(cache_path.iterdir()):
                                app_name, category = identify_app_from_path(item.name)
                                paths.append(CachePath(
                                    path=cache_path,
                                    name=f"{app_name} Cache",
                                    category=category,
                                    description=f"Cache for {app_name}",
                                    risk_level=RiskLevel.SAFE,
                                    app_specific=True,
                                    app_name=app_name,
                                ))
                        except PermissionError:
                            continue

        # ============================================================
        # SPECIFIC: Browser caches (nested paths)
        # ============================================================
        browsers = [
            ("Google/Chrome", "Chrome"),
            ("Microsoft/Edge", "Edge"),
            ("BraveSoftware/Brave-Browser", "Brave"),
            ("Opera Software/Opera Stable", "Opera"),
            ("Vivaldi", "Vivaldi"),
        ]
        for folder, name in browsers:
            for cache_type in ["Cache", "Code Cache", "Service Worker", "GPUCache"]:
                cache_path = localappdata / folder / "User Data" / "Default" / cache_type
                if cache_path.exists():
                    paths.append(CachePath(
                        path=cache_path,
                        name=f"{name} {cache_type}",
                        category=Category.BROWSER,
                        description=f"{name} browser {cache_type.lower()}",
                        risk_level=RiskLevel.SAFE,
                        app_specific=True,
                        app_name=name,
                    ))

        # Firefox profiles
        firefox_profiles = localappdata / "Mozilla" / "Firefox" / "Profiles"
        if firefox_profiles.exists():
            paths.append(CachePath(
                path=firefox_profiles,
                name="Firefox Profiles",
                category=Category.BROWSER,
                description="Firefox browser profiles (contains cache)",
                risk_level=RiskLevel.MODERATE,
                app_specific=True,
                app_name="Firefox",
            ))

        # ============================================================
        # SPECIFIC: VS Code and variants
        # ============================================================
        vscode_apps = [
            ("Code", "VS Code"),
            ("Cursor", "Cursor"),
            ("VSCodium", "VSCodium"),
        ]
        for folder, name in vscode_apps:
            base = appdata / folder
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

        # ============================================================
        # SPECIFIC: Development tool caches
        # ============================================================
        dev_caches = [
            (appdata / "npm-cache", "npm Cache", "npm package manager cache"),
            (localappdata / "pip" / "Cache", "pip Cache", "Python pip package cache"),
            (localappdata / "Yarn" / "Cache", "Yarn Cache", "Yarn package manager cache"),
            (localappdata / "pnpm-cache", "pnpm Cache", "pnpm package manager cache"),
            (localappdata / "NuGet" / "v3-cache", "NuGet Cache", ".NET NuGet package cache"),
            (home / ".gradle" / "caches", "Gradle Cache", "Gradle build system cache"),
            (home / ".m2" / "repository", "Maven Repository", "Maven dependency cache"),
            (home / ".cargo" / "registry" / "cache", "Cargo Cache", "Rust Cargo package cache"),
            (home / "go" / "pkg" / "mod" / "cache", "Go Module Cache", "Go module download cache"),
            (home / ".docker" / "buildx", "Docker Buildx Cache", "Docker buildx builder cache"),
            (home / ".cache" / "huggingface", "HuggingFace Models", "HuggingFace AI models cache"),
            (home / ".pub-cache", "Dart/Flutter Cache", "Dart and Flutter package cache"),
            (localappdata / "JetBrains", "JetBrains Cache", "JetBrains IDE caches"),
            (localappdata / "Android" / "Sdk" / ".temp", "Android SDK Cache", "Android SDK temp files"),
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

        # Docker WSL data (caution)
        docker_wsl = localappdata / "Docker" / "wsl"
        if docker_wsl.exists():
            paths.append(CachePath(
                path=docker_wsl,
                name="Docker WSL Data",
                category=Category.DEVELOPMENT,
                description="Docker Desktop WSL backend data",
                risk_level=RiskLevel.CAUTION,
            ))

        # ============================================================
        # GAME CACHES
        # ============================================================
        paths.extend(self.get_game_cache_paths())

        # ============================================================
        # WINDOWS SYSTEM CACHES
        # ============================================================
        system_caches = [
            (localappdata / "Microsoft" / "Windows" / "INetCache", "Internet Cache", "Windows Internet cache"),
            (localappdata / "Microsoft" / "Windows" / "Explorer", "Explorer Cache", "Windows Explorer thumbnails"),
            (localappdata / "CrashDumps", "Crash Dumps", "Application crash dump files"),
            (localappdata / "Microsoft" / "Windows" / "WER", "Windows Error Reports", "Windows Error Reporting"),
        ]

        for path, name, description in system_caches:
            if path.exists():
                paths.append(CachePath(
                    path=path,
                    name=name,
                    category=Category.SYSTEM_CACHE if "Cache" in name else Category.LOGS,
                    description=description,
                    risk_level=RiskLevel.SAFE,
                ))

        # Windows Update Cache (requires admin)
        win_update = Path("C:/Windows/SoftwareDistribution/Download")
        if win_update.exists():
            paths.append(CachePath(
                path=win_update,
                name="Windows Update Cache",
                category=Category.SYSTEM_CACHE,
                description="Windows Update downloaded files (requires admin)",
                risk_level=RiskLevel.MODERATE,
                requires_admin=True,
            ))

        # Prefetch (requires admin)
        prefetch = Path("C:/Windows/Prefetch")
        if prefetch.exists():
            paths.append(CachePath(
                path=prefetch,
                name="Prefetch",
                category=Category.SYSTEM_CACHE,
                description="Windows Prefetch files (requires admin)",
                risk_level=RiskLevel.MODERATE,
                requires_admin=True,
            ))

        # ============================================================
        # DOWNLOADS
        # ============================================================
        downloads_path = home / "Downloads"
        if downloads_path.exists():
            paths.append(CachePath(
                path=downloads_path,
                name="Downloads",
                category=Category.DOWNLOADS,
                description="Downloaded files (review before deleting!)",
                risk_level=RiskLevel.CAUTION,
            ))

        self._cache_paths = paths
        return self._cache_paths

    def get_game_cache_paths(self) -> list[CachePath]:
        """Get Windows game-specific cache paths."""
        localappdata = self._get_localappdata()
        appdata = self._get_appdata()
        programdata = self._get_programdata()
        paths: list[CachePath] = []

        # Steam
        steam_paths = [
            (Path("C:/Program Files (x86)/Steam/appcache"), "Steam App Cache", "Steam application cache"),
            (Path("C:/Program Files (x86)/Steam/depotcache"), "Steam Depot Cache", "Steam game depot cache"),
            (Path("C:/Program Files (x86)/Steam/htmlcache"), "Steam HTML Cache", "Steam browser cache"),
            (localappdata / "Steam" / "htmlcache", "Steam Local Cache", "Steam local cache"),
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
        epic_paths = [
            (localappdata / "EpicGamesLauncher" / "Saved" / "webcache", "Epic Games Cache", "Epic Games Launcher cache"),
            (programdata / "Epic" / "EpicGamesLauncher" / "Data", "Epic Games Data", "Epic Games data cache"),
        ]
        for path, name, desc in epic_paths:
            if path.exists():
                paths.append(CachePath(
                    path=path,
                    name=name,
                    category=Category.GAME,
                    description=desc,
                    risk_level=RiskLevel.SAFE,
                    app_specific=True,
                    app_name="Epic Games",
                ))

        # Riot Games (Valorant, League of Legends)
        riot_paths = [
            (localappdata / "Riot Games", "Riot Games Cache", "Riot Games client cache"),
            (programdata / "Riot Games", "Riot Games Data", "Riot Games shared data"),
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
        blizzard_cache = programdata / "Battle.net" / "Cache"
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

        # EA / Origin
        origin_cache = localappdata / "Origin" / "cache"
        if origin_cache.exists():
            paths.append(CachePath(
                path=origin_cache,
                name="Origin Cache",
                category=Category.GAME,
                description="EA Origin cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Origin",
            ))

        # Ubisoft Connect
        ubisoft_cache = localappdata / "Ubisoft Game Launcher" / "cache"
        if ubisoft_cache.exists():
            paths.append(CachePath(
                path=ubisoft_cache,
                name="Ubisoft Connect Cache",
                category=Category.GAME,
                description="Ubisoft Connect cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Ubisoft",
            ))

        # GOG Galaxy
        gog_cache = localappdata / "GOG.com" / "Galaxy" / "webcache"
        if gog_cache.exists():
            paths.append(CachePath(
                path=gog_cache,
                name="GOG Galaxy Cache",
                category=Category.GAME,
                description="GOG Galaxy cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="GOG Galaxy",
            ))

        # Minecraft
        minecraft_path = appdata / ".minecraft"
        if minecraft_path.exists():
            for subfolder in ["assets", "versions"]:
                mc_cache = minecraft_path / subfolder
                if mc_cache.exists():
                    paths.append(CachePath(
                        path=mc_cache,
                        name=f"Minecraft {subfolder.capitalize()}",
                        category=Category.GAME,
                        description=f"Minecraft {subfolder} cache",
                        risk_level=RiskLevel.MODERATE,
                        app_specific=True,
                        app_name="Minecraft",
                    ))

        # Xbox / Microsoft Store games
        xbox_cache = localappdata / "Packages"
        if xbox_cache.exists():
            # Look for Xbox-related packages
            for item in xbox_cache.iterdir():
                if item.is_dir() and "xbox" in item.name.lower():
                    temp_state = item / "TempState"
                    if temp_state.exists():
                        paths.append(CachePath(
                            path=temp_state,
                            name="Xbox App Cache",
                            category=Category.GAME,
                            description="Xbox app temporary data",
                            risk_level=RiskLevel.SAFE,
                            app_specific=True,
                            app_name="Xbox",
                        ))
                        break

        # NVIDIA shader cache
        nvidia_cache = localappdata / "NVIDIA" / "DXCache"
        if nvidia_cache.exists():
            paths.append(CachePath(
                path=nvidia_cache,
                name="NVIDIA Shader Cache",
                category=Category.GAME,
                description="NVIDIA DirectX shader cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="NVIDIA",
            ))

        # AMD shader cache
        amd_cache = localappdata / "AMD" / "DxCache"
        if amd_cache.exists():
            paths.append(CachePath(
                path=amd_cache,
                name="AMD Shader Cache",
                category=Category.GAME,
                description="AMD DirectX shader cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="AMD",
            ))

        # Unity
        unity_cache = localappdata / "Unity" / "cache"
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

        # Unreal Engine
        unreal_cache = localappdata / "EpicGames" / "Unreal Engine"
        if unreal_cache.exists():
            paths.append(CachePath(
                path=unreal_cache,
                name="Unreal Engine Cache",
                category=Category.GAME,
                description="Unreal Engine cache",
                risk_level=RiskLevel.SAFE,
                app_specific=True,
                app_name="Unreal Engine",
            ))

        return paths
