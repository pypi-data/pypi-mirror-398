"""
Runtime Configuration Loader

Loads maqet.conf from hierarchical locations similar to Ansible's ansible.cfg.
Provides runtime settings like directories and logging configuration.

This is separate from VM configuration (which uses YAML VM configs).
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .merger import ConfigMerger
from ..logger import LOG


class RuntimeConfig:
    """
    Runtime configuration loader for maqet.conf files.

    Searches for configuration files in this order (first found wins):
    1. MAQET_CONFIG environment variable
    2. ./maqet.conf or ./.maqet.conf (current directory)
    3. ~/.config/maqet/maqet.conf (user config)
    4. /etc/maqet/maqet.conf (system-wide)

    CLI flags always override config file settings.
    """

    # Default configuration values
    DEFAULTS: Dict[str, Any] = {
        "directories": {
            "data_dir": None,  # None = use XDG default
            "config_dir": None,  # None = use XDG default
            "runtime_dir": None,  # None = use XDG default
        },
        "logging": {
            "verbosity": 0,  # 0=errors, 1=warnings, 2=info, 3=debug
            "log_file": None,
        },
    }

    # Configuration file search paths (in priority order)
    # Note: Path.cwd() and Path.home() are evaluated at runtime in _get_search_paths()
    # to support testing with monkeypatch.chdir() and monkeypatch.setenv("HOME")

    def __init__(self):
        """Initialize runtime configuration."""
        self._config: Dict[str, Any] = {}
        self._config_file_path: Optional[Path] = None
        self._load_config()

    def _get_search_paths(self) -> list[Path]:
        """
        Get configuration file search paths.

        Evaluated at runtime to support testing with monkeypatch.

        Returns:
            List of paths to search for config files
        """
        return [
            # Current directory variants
            Path.cwd() / "maqet.conf",
            Path.cwd() / ".maqet.conf",
            # User config
            Path.home() / ".config" / "maqet" / "maqet.conf",
            # System-wide
            Path("/etc") / "maqet" / "maqet.conf",
        ]

    def _find_config_file(self) -> Optional[Path]:
        """
        Find the first available configuration file.

        Returns:
            Path to config file or None if not found
        """
        # Check environment variable first
        env_config = os.environ.get("MAQET_CONFIG")
        if env_config:
            env_path = Path(env_config)
            if env_path.exists():
                LOG.debug(
                    f"Using config from MAQET_CONFIG: {env_path}"
                )
                return env_path
            else:
                LOG.warning(
                    f"MAQET_CONFIG points to non-existent file: {env_path}"
                )

        # Search standard paths
        for path in self._get_search_paths():
            if path.exists():
                LOG.debug(f"Found config file: {path}")
                return path

        LOG.debug("No maqet.conf file found, using defaults")
        return None

    def _load_config(self) -> None:
        """Load configuration from file or use defaults."""
        # Start with defaults
        self._config = self._deep_copy_defaults()

        # Find config file
        config_file = self._find_config_file()
        if not config_file:
            return

        # Load and merge config file
        try:
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f) or {}

            if not isinstance(file_config, dict):
                LOG.warning(
                    f"Config file {config_file} does not contain a dictionary, using defaults"
                )
                return

            # Merge file config with defaults using ConfigMerger
            self._config = ConfigMerger.deep_merge(self._config, file_config)
            self._config_file_path = config_file
            LOG.debug(f"Loaded configuration from {config_file}")

        except yaml.YAMLError as e:
            LOG.warning(
                f"Failed to parse config file {config_file}: {e}, using defaults"
            )
        except Exception as e:
            LOG.warning(
                f"Failed to load config file {config_file}: {e}, using defaults"
            )

    def _deep_copy_defaults(self) -> Dict[str, Any]:
        """
        Deep copy the defaults dictionary.

        Returns:
            Deep copy of DEFAULTS
        """
        import copy

        return copy.deepcopy(self.DEFAULTS)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Dot-separated key path (e.g., "directories.data_dir")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            config.get("directories.data_dir")
            config.get("logging.verbosity", 1)
        """
        keys = key_path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_directories(self) -> Dict[str, Optional[str]]:
        """
        Get directory configuration.

        Returns:
            Dictionary with data_dir, config_dir, runtime_dir
        """
        return self._config.get("directories", self.DEFAULTS["directories"])

    def get_logging(self) -> Dict[str, Any]:
        """
        Get logging configuration.

        Returns:
            Dictionary with verbosity and log_file
        """
        return self._config.get("logging", self.DEFAULTS["logging"])

    def get_data_dir(self) -> Optional[str]:
        """Get data directory path."""
        return self.get("directories.data_dir")

    def get_config_dir(self) -> Optional[str]:
        """Get config directory path."""
        return self.get("directories.config_dir")

    def get_runtime_dir(self) -> Optional[str]:
        """Get runtime directory path."""
        return self.get("directories.runtime_dir")

    def get_verbosity(self) -> int:
        """Get logging verbosity level."""
        return self.get("logging.verbosity", 0)

    def get_log_file(self) -> Optional[str]:
        """Get log file path."""
        return self.get("logging.log_file")

    @property
    def config_file_path(self) -> Optional[Path]:
        """Get the path to the loaded config file."""
        return self._config_file_path

    def __repr__(self) -> str:
        """String representation."""
        config_source = (
            str(self._config_file_path) if self._config_file_path else "defaults"
        )
        return f"RuntimeConfig(source={config_source})"
