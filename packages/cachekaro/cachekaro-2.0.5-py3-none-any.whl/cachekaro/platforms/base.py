"""
Base platform class defining the interface for platform-specific implementations.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RiskLevel(Enum):
    """Risk level for cleaning a cache path."""
    SAFE = "safe"           # 100% safe to clean, no data loss
    MODERATE = "moderate"   # Generally safe, may require re-login
    CAUTION = "caution"     # May affect app behavior, use with care


class Category(Enum):
    """Categories for cache paths."""
    USER_CACHE = "user_cache"
    SYSTEM_CACHE = "system_cache"
    BROWSER = "browser"
    DEVELOPMENT = "development"
    LOGS = "logs"
    TRASH = "trash"
    DOWNLOADS = "downloads"
    APPLICATION = "application"
    CONTAINER = "container"
    GAME = "game"
    CUSTOM = "custom"


# Known app identifiers to friendly names mapping
KNOWN_APPS: dict[str, tuple[str, Category]] = {
    # Browsers
    "com.apple.safari": ("Safari", Category.BROWSER),
    "com.google.chrome": ("Chrome", Category.BROWSER),
    "google": ("Chrome", Category.BROWSER),
    "chromium": ("Chromium", Category.BROWSER),
    "firefox": ("Firefox", Category.BROWSER),
    "org.mozilla.firefox": ("Firefox", Category.BROWSER),
    "brave": ("Brave", Category.BROWSER),
    "bravesoftware": ("Brave", Category.BROWSER),
    "com.microsoft.edge": ("Edge", Category.BROWSER),
    "microsoft.edge": ("Edge", Category.BROWSER),
    "opera": ("Opera", Category.BROWSER),
    "com.operasoftware": ("Opera", Category.BROWSER),
    "vivaldi": ("Vivaldi", Category.BROWSER),
    "arc": ("Arc", Category.BROWSER),
    "com.thebrowser.browser": ("Arc", Category.BROWSER),

    # Communication
    "com.discord": ("Discord", Category.APPLICATION),
    "discord": ("Discord", Category.APPLICATION),
    "com.hnc.discord": ("Discord", Category.APPLICATION),
    "slack": ("Slack", Category.APPLICATION),
    "com.tinyspeck.slackmacgap": ("Slack", Category.APPLICATION),
    "zoom": ("Zoom", Category.APPLICATION),
    "us.zoom": ("Zoom", Category.APPLICATION),
    "us.zoom.xos": ("Zoom", Category.APPLICATION),
    "telegram": ("Telegram", Category.APPLICATION),
    "whatsapp": ("WhatsApp", Category.APPLICATION),
    "skype": ("Skype", Category.APPLICATION),
    "microsoft.teams": ("Teams", Category.APPLICATION),
    "com.microsoft.teams": ("Teams", Category.APPLICATION),

    # Music & Media
    "com.spotify.client": ("Spotify", Category.APPLICATION),
    "spotify": ("Spotify", Category.APPLICATION),
    "com.apple.music": ("Apple Music", Category.APPLICATION),
    "vlc": ("VLC", Category.APPLICATION),
    "org.videolan.vlc": ("VLC", Category.APPLICATION),
    "netflix": ("Netflix", Category.APPLICATION),
    "com.netflix": ("Netflix", Category.APPLICATION),
    "youtube": ("YouTube", Category.APPLICATION),
    "com.google.youtube": ("YouTube", Category.APPLICATION),

    # Development
    "com.microsoft.vscode": ("VS Code", Category.DEVELOPMENT),
    "code": ("VS Code", Category.DEVELOPMENT),
    "cursor": ("Cursor", Category.DEVELOPMENT),
    "jetbrains": ("JetBrains", Category.DEVELOPMENT),
    "com.jetbrains": ("JetBrains", Category.DEVELOPMENT),
    "intellij": ("IntelliJ", Category.DEVELOPMENT),
    "pycharm": ("PyCharm", Category.DEVELOPMENT),
    "webstorm": ("WebStorm", Category.DEVELOPMENT),
    "phpstorm": ("PhpStorm", Category.DEVELOPMENT),
    "clion": ("CLion", Category.DEVELOPMENT),
    "goland": ("GoLand", Category.DEVELOPMENT),
    "rider": ("Rider", Category.DEVELOPMENT),
    "rubymine": ("RubyMine", Category.DEVELOPMENT),
    "datagrip": ("DataGrip", Category.DEVELOPMENT),
    "androidstudio": ("Android Studio", Category.DEVELOPMENT),
    "android studio": ("Android Studio", Category.DEVELOPMENT),
    "com.google.android.studio": ("Android Studio", Category.DEVELOPMENT),
    "xcode": ("Xcode", Category.DEVELOPMENT),
    "com.apple.dt.xcode": ("Xcode", Category.DEVELOPMENT),
    "sublime": ("Sublime Text", Category.DEVELOPMENT),
    "sublimetext": ("Sublime Text", Category.DEVELOPMENT),
    "atom": ("Atom", Category.DEVELOPMENT),
    "github": ("GitHub Desktop", Category.DEVELOPMENT),
    "com.github.desktop": ("GitHub Desktop", Category.DEVELOPMENT),
    "docker": ("Docker", Category.DEVELOPMENT),
    "com.docker": ("Docker", Category.DEVELOPMENT),
    "postman": ("Postman", Category.DEVELOPMENT),
    "insomnia": ("Insomnia", Category.DEVELOPMENT),
    "sourcetree": ("Sourcetree", Category.DEVELOPMENT),
    "iterm": ("iTerm", Category.DEVELOPMENT),
    "com.googlecode.iterm2": ("iTerm", Category.DEVELOPMENT),
    "terminal": ("Terminal", Category.DEVELOPMENT),
    "hyper": ("Hyper", Category.DEVELOPMENT),
    "warp": ("Warp", Category.DEVELOPMENT),
    "dev.warp.warp-terminal": ("Warp", Category.DEVELOPMENT),

    # Package managers & Dev tools
    "npm": ("npm", Category.DEVELOPMENT),
    "yarn": ("Yarn", Category.DEVELOPMENT),
    "pnpm": ("pnpm", Category.DEVELOPMENT),
    "pip": ("pip", Category.DEVELOPMENT),
    "homebrew": ("Homebrew", Category.DEVELOPMENT),
    "cocoapods": ("CocoaPods", Category.DEVELOPMENT),
    "carthage": ("Carthage", Category.DEVELOPMENT),
    "gradle": ("Gradle", Category.DEVELOPMENT),
    "maven": ("Maven", Category.DEVELOPMENT),
    "cargo": ("Cargo", Category.DEVELOPMENT),
    "go": ("Go", Category.DEVELOPMENT),
    "rust": ("Rust", Category.DEVELOPMENT),
    "node": ("Node.js", Category.DEVELOPMENT),
    "node-gyp": ("node-gyp", Category.DEVELOPMENT),
    "typescript": ("TypeScript", Category.DEVELOPMENT),
    "eslint": ("ESLint", Category.DEVELOPMENT),
    "prettier": ("Prettier", Category.DEVELOPMENT),
    "webpack": ("Webpack", Category.DEVELOPMENT),
    "vite": ("Vite", Category.DEVELOPMENT),
    "huggingface": ("HuggingFace", Category.DEVELOPMENT),
    "puppeteer": ("Puppeteer", Category.DEVELOPMENT),
    "playwright": ("Playwright", Category.DEVELOPMENT),
    "cypress": ("Cypress", Category.DEVELOPMENT),
    "pre-commit": ("pre-commit", Category.DEVELOPMENT),
    "uv": ("uv", Category.DEVELOPMENT),
    "ruff": ("ruff", Category.DEVELOPMENT),

    # Games
    "steam": ("Steam", Category.GAME),
    "com.valvesoftware.steam": ("Steam", Category.GAME),
    "valve": ("Steam", Category.GAME),
    "epicgames": ("Epic Games", Category.GAME),
    "epic games": ("Epic Games", Category.GAME),
    "epicgameslauncher": ("Epic Games", Category.GAME),
    "com.epicgames": ("Epic Games", Category.GAME),
    "riotgames": ("Riot Games", Category.GAME),
    "riot games": ("Riot Games", Category.GAME),
    "riot client": ("Riot Client", Category.GAME),
    "riotclient": ("Riot Client", Category.GAME),
    "valorant": ("Valorant", Category.GAME),
    "leagueoflegends": ("League of Legends", Category.GAME),
    "league of legends": ("League of Legends", Category.GAME),
    "battlenet": ("Battle.net", Category.GAME),
    "battle.net": ("Battle.net", Category.GAME),
    "blizzard": ("Blizzard", Category.GAME),
    "blizzard entertainment": ("Blizzard", Category.GAME),
    "origin": ("Origin", Category.GAME),
    "ea": ("EA", Category.GAME),
    "electronic arts": ("EA", Category.GAME),
    "ubisoft": ("Ubisoft", Category.GAME),
    "uplay": ("Ubisoft Connect", Category.GAME),
    "gog": ("GOG Galaxy", Category.GAME),
    "gogalaxy": ("GOG Galaxy", Category.GAME),
    "minecraft": ("Minecraft", Category.GAME),
    "mojang": ("Minecraft", Category.GAME),
    "unity": ("Unity", Category.GAME),
    "unrealengine": ("Unreal Engine", Category.GAME),
    "unreal engine": ("Unreal Engine", Category.GAME),
    "xbox": ("Xbox", Category.GAME),
    "nvidia": ("NVIDIA", Category.GAME),
    "geforce": ("GeForce", Category.GAME),

    # Productivity & Design
    "notion": ("Notion", Category.APPLICATION),
    "obsidian": ("Obsidian", Category.APPLICATION),
    "evernote": ("Evernote", Category.APPLICATION),
    "todoist": ("Todoist", Category.APPLICATION),
    "trello": ("Trello", Category.APPLICATION),
    "asana": ("Asana", Category.APPLICATION),
    "linear": ("Linear", Category.APPLICATION),
    "figma": ("Figma", Category.APPLICATION),
    "sketch": ("Sketch", Category.APPLICATION),
    "canva": ("Canva", Category.APPLICATION),

    # Adobe Creative Suite
    "adobe": ("Adobe", Category.APPLICATION),
    "com.adobe": ("Adobe", Category.APPLICATION),
    "photoshop": ("Photoshop", Category.APPLICATION),
    "com.adobe.photoshop": ("Photoshop", Category.APPLICATION),
    "illustrator": ("Illustrator", Category.APPLICATION),
    "com.adobe.illustrator": ("Illustrator", Category.APPLICATION),
    "premiere": ("Premiere Pro", Category.APPLICATION),
    "premierepro": ("Premiere Pro", Category.APPLICATION),
    "com.adobe.premiere": ("Premiere Pro", Category.APPLICATION),
    "aftereffects": ("After Effects", Category.APPLICATION),
    "after effects": ("After Effects", Category.APPLICATION),
    "com.adobe.aftereffects": ("After Effects", Category.APPLICATION),
    "lightroom": ("Lightroom", Category.APPLICATION),
    "com.adobe.lightroom": ("Lightroom", Category.APPLICATION),
    "acrobat": ("Acrobat", Category.APPLICATION),
    "com.adobe.acrobat": ("Acrobat", Category.APPLICATION),
    "indesign": ("InDesign", Category.APPLICATION),
    "com.adobe.indesign": ("InDesign", Category.APPLICATION),
    "xd": ("Adobe XD", Category.APPLICATION),
    "adobexd": ("Adobe XD", Category.APPLICATION),
    "com.adobe.xd": ("Adobe XD", Category.APPLICATION),
    "animate": ("Adobe Animate", Category.APPLICATION),
    "audition": ("Adobe Audition", Category.APPLICATION),
    "mediaencoder": ("Media Encoder", Category.APPLICATION),
    "media encoder": ("Media Encoder", Category.APPLICATION),
    "bridge": ("Adobe Bridge", Category.APPLICATION),
    "creative cloud": ("Creative Cloud", Category.APPLICATION),
    "creativecloud": ("Creative Cloud", Category.APPLICATION),
    "com.adobe.acc": ("Creative Cloud", Category.APPLICATION),

    # Video Editing & 3D
    "davinciresolve": ("DaVinci Resolve", Category.APPLICATION),
    "davinci resolve": ("DaVinci Resolve", Category.APPLICATION),
    "blackmagic": ("DaVinci Resolve", Category.APPLICATION),
    "finalcut": ("Final Cut Pro", Category.APPLICATION),
    "final cut": ("Final Cut Pro", Category.APPLICATION),
    "com.apple.finalcutpro": ("Final Cut Pro", Category.APPLICATION),
    "logic": ("Logic Pro", Category.APPLICATION),
    "logicpro": ("Logic Pro", Category.APPLICATION),
    "com.apple.logicpro": ("Logic Pro", Category.APPLICATION),
    "garageband": ("GarageBand", Category.APPLICATION),
    "com.apple.garageband": ("GarageBand", Category.APPLICATION),
    "blender": ("Blender", Category.APPLICATION),
    "org.blender": ("Blender", Category.APPLICATION),
    "cinema4d": ("Cinema 4D", Category.APPLICATION),
    "cinema 4d": ("Cinema 4D", Category.APPLICATION),
    "maxon": ("Cinema 4D", Category.APPLICATION),
    "maya": ("Maya", Category.APPLICATION),
    "autodesk": ("Autodesk", Category.APPLICATION),
    "3dsmax": ("3ds Max", Category.APPLICATION),
    "3ds max": ("3ds Max", Category.APPLICATION),
    "zbrush": ("ZBrush", Category.APPLICATION),
    "houdini": ("Houdini", Category.APPLICATION),
    "sidefx": ("Houdini", Category.APPLICATION),
    "nuke": ("Nuke", Category.APPLICATION),
    "foundry": ("Nuke", Category.APPLICATION),
    "obs": ("OBS Studio", Category.APPLICATION),
    "obs-studio": ("OBS Studio", Category.APPLICATION),
    "com.obsproject": ("OBS Studio", Category.APPLICATION),
    "handbrake": ("HandBrake", Category.APPLICATION),
    "ffmpeg": ("FFmpeg", Category.DEVELOPMENT),

    # Audio & Music Production
    "ableton": ("Ableton Live", Category.APPLICATION),
    "ableton live": ("Ableton Live", Category.APPLICATION),
    "flstudio": ("FL Studio", Category.APPLICATION),
    "fl studio": ("FL Studio", Category.APPLICATION),
    "imageline": ("FL Studio", Category.APPLICATION),
    "protools": ("Pro Tools", Category.APPLICATION),
    "pro tools": ("Pro Tools", Category.APPLICATION),
    "avid": ("Pro Tools", Category.APPLICATION),
    "cubase": ("Cubase", Category.APPLICATION),
    "steinberg": ("Cubase", Category.APPLICATION),
    "reaper": ("Reaper", Category.APPLICATION),
    "bitwig": ("Bitwig", Category.APPLICATION),

    # CAD & Engineering
    "autocad": ("AutoCAD", Category.APPLICATION),
    "solidworks": ("SolidWorks", Category.APPLICATION),
    "fusion360": ("Fusion 360", Category.APPLICATION),
    "fusion 360": ("Fusion 360", Category.APPLICATION),
    "rhino": ("Rhino", Category.APPLICATION),
    "rhinoceros": ("Rhino", Category.APPLICATION),
    "sketchup": ("SketchUp", Category.APPLICATION),
    "archicad": ("ArchiCAD", Category.APPLICATION),
    "revit": ("Revit", Category.APPLICATION),
    "vectorworks": ("Vectorworks", Category.APPLICATION),

    # Cloud & Storage
    "dropbox": ("Dropbox", Category.APPLICATION),
    "googledrive": ("Google Drive", Category.APPLICATION),
    "google drive": ("Google Drive", Category.APPLICATION),
    "onedrive": ("OneDrive", Category.APPLICATION),
    "icloud": ("iCloud", Category.APPLICATION),
    "box": ("Box", Category.APPLICATION),

    # AI
    "com.openai.chat": ("ChatGPT", Category.APPLICATION),
    "openai": ("OpenAI", Category.APPLICATION),
    "chatgpt": ("ChatGPT", Category.APPLICATION),
    "claude": ("Claude", Category.APPLICATION),
    "anthropic": ("Claude", Category.APPLICATION),
    "copilot": ("Copilot", Category.APPLICATION),

    # System & Utilities
    "electron": ("Electron Apps", Category.APPLICATION),
    "1password": ("1Password", Category.APPLICATION),
    "lastpass": ("LastPass", Category.APPLICATION),
    "bitwarden": ("Bitwarden", Category.APPLICATION),
    "dashlane": ("Dashlane", Category.APPLICATION),
    "alfred": ("Alfred", Category.APPLICATION),
    "raycast": ("Raycast", Category.APPLICATION),
    "bartender": ("Bartender", Category.APPLICATION),
    "cleanmymac": ("CleanMyMac", Category.APPLICATION),
    "malwarebytes": ("Malwarebytes", Category.APPLICATION),
    "avast": ("Avast", Category.APPLICATION),
    "norton": ("Norton", Category.APPLICATION),
    "mcafee": ("McAfee", Category.APPLICATION),
}


def identify_app_from_path(folder_name: str) -> tuple[str, Category]:
    """
    Identify an application from its cache folder name.

    Args:
        folder_name: The name of the cache folder

    Returns:
        Tuple of (friendly_name, category)
    """
    # Normalize the folder name for matching
    normalized = folder_name.lower().replace("-", "").replace("_", "").replace(" ", "")

    # Try exact match first
    if normalized in KNOWN_APPS:
        return KNOWN_APPS[normalized]

    # Try matching parts of the name (for bundle IDs like com.apple.Safari)
    for key, value in KNOWN_APPS.items():
        if key in normalized or normalized in key:
            return value

    # Try matching individual words
    words = re.split(r"[.\-_\s]", folder_name.lower())
    for word in words:
        if word and word in KNOWN_APPS:
            return KNOWN_APPS[word]

    # Format the folder name as a friendly name
    # Convert "com.example.AppName" to "AppName"
    parts = folder_name.split(".")
    if len(parts) > 1:
        # Take the last part and capitalize properly
        name = parts[-1]
    else:
        name = folder_name

    # Convert camelCase or snake_case to Title Case
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    name = name.replace("_", " ").replace("-", " ")
    name = " ".join(word.capitalize() for word in name.split())

    return (name, Category.APPLICATION)


@dataclass
class CachePath:
    """Represents a cache path to scan/clean."""
    path: Path
    name: str
    category: Category
    description: str
    risk_level: RiskLevel = RiskLevel.SAFE
    clean_contents_only: bool = True  # If True, clean contents but keep directory
    requires_admin: bool = False
    app_specific: bool = False
    app_name: str | None = None

    def exists(self) -> bool:
        """Check if the path exists."""
        return self.path.exists()

    def is_accessible(self) -> bool:
        """Check if the path is readable."""
        try:
            if self.path.is_dir():
                list(self.path.iterdir())
            return True
        except (PermissionError, OSError):
            return False


@dataclass
class DiskUsage:
    """Disk usage information."""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    mount_point: str = "/"

    @property
    def used_percent(self) -> float:
        """Calculate percentage of disk used."""
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100

    @property
    def free_percent(self) -> float:
        """Calculate percentage of disk free."""
        return 100.0 - self.used_percent


@dataclass
class PlatformInfo:
    """Information about the current platform."""
    name: str
    version: str
    architecture: str
    hostname: str
    username: str
    home_dir: Path
    temp_dir: Path


class PlatformBase(ABC):
    """
    Abstract base class for platform-specific implementations.

    Each platform (macOS, Linux, Windows) must implement this interface
    to provide cache paths and system operations specific to that OS.
    """

    def __init__(self) -> None:
        self._cache_paths: list[CachePath] = []
        self._platform_info: PlatformInfo | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the platform name (e.g., 'macOS', 'Linux', 'Windows')."""
        pass

    @abstractmethod
    def get_platform_info(self) -> PlatformInfo:
        """Get detailed platform information."""
        pass

    @abstractmethod
    def get_home_dir(self) -> Path:
        """Get the user's home directory."""
        pass

    @abstractmethod
    def get_temp_dir(self) -> Path:
        """Get the system temporary directory."""
        pass

    @abstractmethod
    def get_cache_paths(self) -> list[CachePath]:
        """
        Get all cache paths for this platform.

        Returns:
            List of CachePath objects representing scannable locations.
        """
        pass

    @abstractmethod
    def get_trash_path(self) -> Path | None:
        """Get the path to the user's trash/recycle bin."""
        pass

    @abstractmethod
    def get_disk_usage(self, path: str = "/") -> DiskUsage:
        """
        Get disk usage for the specified mount point.

        Args:
            path: Path to check (default: root)

        Returns:
            DiskUsage object with space information.
        """
        pass

    @abstractmethod
    def flush_dns_cache(self) -> tuple[bool, str]:
        """
        Flush the DNS cache.

        Returns:
            Tuple of (success, message)
        """
        pass

    @abstractmethod
    def is_admin(self) -> bool:
        """Check if running with administrator/root privileges."""
        pass

    @abstractmethod
    def get_config_dir(self) -> Path:
        """Get the directory for storing configuration files."""
        pass

    def get_paths_by_category(self, category: Category) -> list[CachePath]:
        """Get cache paths filtered by category."""
        return [p for p in self.get_cache_paths() if p.category == category]

    def get_paths_by_risk(self, max_risk: RiskLevel) -> list[CachePath]:
        """Get cache paths filtered by maximum risk level."""
        risk_order = [RiskLevel.SAFE, RiskLevel.MODERATE, RiskLevel.CAUTION]
        max_index = risk_order.index(max_risk)
        return [
            p for p in self.get_cache_paths()
            if risk_order.index(p.risk_level) <= max_index
        ]

    def get_existing_paths(self) -> list[CachePath]:
        """Get only cache paths that exist on this system."""
        return [p for p in self.get_cache_paths() if p.exists()]

    def discover_caches_in_directory(
        self,
        directory: Path,
        default_category: Category = Category.APPLICATION,
        exclude_patterns: list[str] | None = None,
    ) -> list[CachePath]:
        """
        Auto-discover all application caches in a directory.

        This method scans a cache directory (like ~/Library/Caches or ~/.cache)
        and automatically identifies all applications with caches.

        Args:
            directory: The directory to scan for cache folders
            default_category: Default category for unknown apps
            exclude_patterns: Folder names to exclude (e.g., ["cachekaro"])

        Returns:
            List of discovered CachePath objects
        """
        discovered: list[CachePath] = []
        exclude = set(exclude_patterns or [])

        if not directory.exists():
            return discovered

        try:
            for item in directory.iterdir():
                # Skip non-directories
                if not item.is_dir():
                    continue

                # Skip excluded patterns
                if item.name in exclude or item.name.startswith("."):
                    continue

                # Skip empty directories
                try:
                    if not any(item.iterdir()):
                        continue
                except PermissionError:
                    continue

                # Identify the app
                app_name, category = identify_app_from_path(item.name)

                # Create the cache path entry
                cache_path = CachePath(
                    path=item,
                    name=f"{app_name} Cache",
                    category=category,
                    description=f"Cache for {app_name}",
                    risk_level=RiskLevel.SAFE,
                    app_specific=True,
                    app_name=app_name,
                )
                discovered.append(cache_path)

        except PermissionError:
            pass

        return discovered

    def get_game_cache_paths(self) -> list[CachePath]:
        """
        Get game-specific cache paths.

        Override in platform-specific implementations to add
        platform-specific game cache locations.

        Returns:
            List of game-related CachePath objects
        """
        return []
