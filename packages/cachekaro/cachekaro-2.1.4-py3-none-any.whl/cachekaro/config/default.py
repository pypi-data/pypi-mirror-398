"""
Default configuration and config file handling for CacheKaro.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml


@dataclass
class Settings:
    """General settings."""
    stale_threshold_days: int = 30
    min_size_display_bytes: int = 1024  # 1 KB
    default_format: str = "text"
    color_output: bool = True
    show_hidden: bool = False
    backup_before_delete: bool = False
    max_workers: int = 4
    max_largest_files: int = 10


@dataclass
class Exclusions:
    """Paths and patterns to exclude from scanning/cleaning."""
    paths: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=lambda: [".git", ".svn", "node_modules"])


@dataclass
class CustomPath:
    """User-defined custom cache path."""
    path: str
    name: str
    category: str = "custom"
    description: str = ""
    risk_level: str = "safe"


@dataclass
class Config:
    """Complete configuration for CacheKaro."""
    settings: Settings = field(default_factory=Settings)
    exclusions: Exclusions = field(default_factory=Exclusions)
    custom_paths: list[CustomPath] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "settings": asdict(self.settings),
            "exclusions": asdict(self.exclusions),
            "custom_paths": [asdict(p) for p in self.custom_paths],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Config:
        """Create config from dictionary."""
        settings = Settings(**data.get("settings", {}))
        exclusions = Exclusions(**data.get("exclusions", {}))
        custom_paths = [
            CustomPath(**p) for p in data.get("custom_paths", [])
        ]
        return cls(
            settings=settings,
            exclusions=exclusions,
            custom_paths=custom_paths,
        )


def get_config_path() -> Path:
    """Get the configuration file path for current platform."""
    import platform as plat

    system = plat.system().lower()

    if system == "windows":
        # Windows: %APPDATA%\cachekaro\config.yaml
        appdata = os.environ.get("APPDATA")
        if appdata:
            config_dir = Path(appdata) / "cachekaro"
        else:
            config_dir = Path.home() / "AppData" / "Roaming" / "cachekaro"
    else:
        # macOS/Linux: ~/.config/cachekaro/config.yaml
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / "cachekaro"
        else:
            config_dir = Path.home() / ".config" / "cachekaro"

    return config_dir / "config.yaml"


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from file.

    Args:
        config_path: Optional path to config file (default: platform default)

    Returns:
        Config object (defaults if file doesn't exist)
    """
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        return Config()

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return Config()
            return Config.from_dict(data)
    except Exception:
        # Return defaults on any error
        return Config()


def save_config(config: Config, config_path: Path | None = None) -> Path:
    """
    Save configuration to file.

    Args:
        config: Config object to save
        config_path: Optional path (default: platform default)

    Returns:
        Path to saved config file
    """
    if config_path is None:
        config_path = get_config_path()

    # Create directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

    return config_path


def create_default_config(config_path: Path | None = None) -> Path:
    """
    Create a default configuration file with comments.

    Args:
        config_path: Optional path (default: platform default)

    Returns:
        Path to created config file
    """
    if config_path is None:
        config_path = get_config_path()

    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = """# CacheKaro Configuration
# https://github.com/mohitbagri/cachekaro

settings:
  # Days after which a cache is considered stale
  stale_threshold_days: 30

  # Minimum size to display (in bytes)
  min_size_display_bytes: 1024

  # Default output format (text, json, csv, html)
  default_format: text

  # Enable colored output in terminal
  color_output: true

  # Show hidden files and directories
  show_hidden: false

  # Create backup before deleting
  backup_before_delete: false

  # Number of parallel scanning workers
  max_workers: 4

  # Number of largest files to track per location
  max_largest_files: 10

exclusions:
  # Paths to never scan or clean
  paths: []

  # Patterns to exclude (glob-style)
  patterns:
    - ".git"
    - ".svn"
    - "node_modules"

# Custom cache paths to scan
# Uncomment and modify to add your own paths
# custom_paths:
#   - path: ~/my-app/cache
#     name: My App Cache
#     category: custom
#     description: Cache for my custom application
#     risk_level: safe  # safe, moderate, or caution
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(default_config)

    return config_path
