"""
Configuration system for CacheKaro.
"""

from cachekaro.config.default import Config, get_config_path, load_config, save_config

__all__ = [
    "Config",
    "load_config",
    "save_config",
    "get_config_path",
]
