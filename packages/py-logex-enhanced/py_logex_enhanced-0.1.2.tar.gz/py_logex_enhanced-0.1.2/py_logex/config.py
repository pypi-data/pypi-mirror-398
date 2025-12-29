"""Configuration discovery and loading for py_logex."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from .defaults import get_default_yaml
from .utils import (
    get_script_name,
    walk_up_find_file,
    get_common_config_locations,
    ensure_directory_exists,
)


class ConfigManager:
    """Manages configuration discovery and loading."""

    CONFIG_FILENAME = "logging.yaml"
    ENV_VAR = "PYLOGEX_CONFIG"

    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._config_path: Optional[Path] = None

    def discover_config(self) -> Path:
        """
        Discover logging.yaml using multi-level fallback strategy.

        Priority:
        1. PYLOGEX_CONFIG environment variable
        2. Walk up directory tree from script location
        3. Common conventional locations
        4. Create default in current directory

        Returns:
            Path to configuration file
        """
        # Level 1: Environment variable
        env_config = os.environ.get(self.ENV_VAR)
        if env_config:
            path = Path(env_config)
            if path.exists():
                return path
            else:
                raise FileNotFoundError(
                    f"{self.ENV_VAR} points to non-existent file: {env_config}"
                )

        # Level 2: Walk up directory tree
        walked_config = walk_up_find_file(self.CONFIG_FILENAME)
        if walked_config:
            return walked_config

        # Level 3: Common locations
        for location in get_common_config_locations(self.CONFIG_FILENAME):
            if location.exists():
                return location

        # Level 4: Create default in current directory
        default_path = Path.cwd() / self.CONFIG_FILENAME
        self._create_default_config(default_path)
        return default_path

    def _create_default_config(self, path: Path) -> None:
        """
        Create default configuration file.

        Args:
            path: Path where to create the config file
        """
        ensure_directory_exists(path)

        script_name = get_script_name()
        default_yaml = get_default_yaml(script_name)

        with open(path, "w") as f:
            f.write(default_yaml)

    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            config_path: Optional path to config file. If None, auto-discover.

        Returns:
            Configuration dictionary
        """
        if config_path is None:
            config_path = self.discover_config()

        self._config_path = config_path

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if config is None:
            config = {}

        self._config = config
        return config

    def get_config(self) -> Dict[str, Any]:
        """
        Get loaded configuration.

        Returns:
            Configuration dictionary

        Raises:
            RuntimeError: If config hasn't been loaded yet
        """
        if self._config is None:
            self.load_config()
        return self._config

    def get_config_path(self) -> Optional[Path]:
        """
        Get path to loaded configuration file.

        Returns:
            Path to config file, or None if not loaded yet
        """
        return self._config_path

    def get_logger_config(self) -> Dict[str, Any]:
        """
        Get configuration for the logger.

        Returns:
            Logger configuration with defaults applied
        """
        config = self.get_config()
        logger_config = config.get("logger", {})

        # Apply defaults for missing values
        defaults = {
            "file": f"{get_script_name()}.log",
            "level": "INFO",
            "rotation": "500 MB",
            "retention": "10 days",
            "compression": "zip",
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "console": {"enabled": True, "level": "INFO"},
        }

        # Merge logger_config with defaults
        result = defaults.copy()

        for key, value in logger_config.items():
            if key == "console" and isinstance(value, dict):
                # Merge console settings
                result["console"] = {**defaults["console"], **value}
            elif value is not None:
                result[key] = value

        # Replace {script_name} if present in file path
        if "{script_name}" in result["file"]:
            result["file"] = result["file"].replace("{script_name}", get_script_name())

        return result


# Global config manager instance
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    return _config_manager
