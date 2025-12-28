"""
Configuration Manager

Simplified configuration coordinator that consolidates maqet configuration
handling with clear precedence rules.

Responsibilities:
- Merge CLI overrides with runtime config
- Provide unified access to directories (data, config, runtime)
- Apply precedence: CLI flags > config file > XDG defaults
- Coordinate between RuntimeConfig and CLI flags

This is a SIMPLIFIED manager (~200 lines) focused on actual value:
- Eliminates duplication of precedence logic (was in __main__.py)
- Provides single source of truth for configuration
- Keeps implementation simple and maintainable
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..config import RuntimeConfig
from ..logger import LOG


class ConfigManager:
    """
    Simplified configuration manager for maqet.

    Consolidates configuration from CLI overrides and runtime config
    with clear precedence rules.

    Precedence (highest to lowest):
    1. CLI flags (--maqet-data-dir, --maqet-config-dir, etc.)
    2. Config files (maqet.conf via RuntimeConfig)
    3. XDG defaults (from StateManager)

    Example:
        # Create with CLI overrides
        config_mgr = ConfigManager(
            data_dir="/custom/data",
            config_dir="/custom/config"
        )

        # Access resolved directories
        data_dir = config_mgr.get_data_dir()
        config_dir = config_mgr.get_config_dir()
    """

    def __init__(
        self,
        data_dir: Optional[Union[str, Path]] = None,
        config_dir: Optional[Union[str, Path]] = None,
        runtime_dir: Optional[Union[str, Path]] = None,
        runtime_config: Optional[RuntimeConfig] = None,
    ):
        """
        Initialize configuration manager.

        Args:
            data_dir: CLI override for data directory
            config_dir: CLI override for config directory
            runtime_dir: CLI override for runtime directory
            runtime_config: Pre-loaded RuntimeConfig instance (optional)

        Note:
            Directories can be str or Path. None means "use default from runtime config or XDG".
        """
        # Store CLI overrides (highest precedence)
        self._cli_data_dir = Path(data_dir) if data_dir else None
        self._cli_config_dir = Path(config_dir) if config_dir else None
        self._cli_runtime_dir = Path(runtime_dir) if runtime_dir else None

        # Load runtime config (config file + environment + XDG defaults)
        self._runtime_config = runtime_config or RuntimeConfig()

        LOG.debug(
            f"ConfigManager initialized: "
            f"data_dir={self._cli_data_dir}, "
            f"config_dir={self._cli_config_dir}, "
            f"runtime_dir={self._cli_runtime_dir}"
        )

    def get_data_dir(self) -> Optional[Path]:
        """
        Get resolved data directory with precedence applied.

        Precedence: CLI flag > config file > None (caller uses XDG default)

        Returns:
            Data directory path or None for XDG default

        Example:
            data_dir = config_mgr.get_data_dir()
            # Returns CLI override if set, else config file value, else None
        """
        if self._cli_data_dir:
            return self._cli_data_dir

        # Get from runtime config (config file or None)
        runtime_data_dir = self._runtime_config.get_data_dir()
        return Path(runtime_data_dir) if runtime_data_dir else None

    def get_config_dir(self) -> Optional[Path]:
        """
        Get resolved config directory with precedence applied.

        Precedence: CLI flag > config file > None (caller uses XDG default)

        Returns:
            Config directory path or None for XDG default

        Example:
            config_dir = config_mgr.get_config_dir()
        """
        if self._cli_config_dir:
            return self._cli_config_dir

        runtime_config_dir = self._runtime_config.get_config_dir()
        return Path(runtime_config_dir) if runtime_config_dir else None

    def get_runtime_dir(self) -> Optional[Path]:
        """
        Get resolved runtime directory with precedence applied.

        Precedence: CLI flag > config file > None (caller uses XDG default)

        Returns:
            Runtime directory path or None for XDG default

        Example:
            runtime_dir = config_mgr.get_runtime_dir()
        """
        if self._cli_runtime_dir:
            return self._cli_runtime_dir

        runtime_runtime_dir = self._runtime_config.get_runtime_dir()
        return Path(runtime_runtime_dir) if runtime_runtime_dir else None

    def get_verbosity(self) -> int:
        """
        Get logging verbosity level.

        Returns:
            Verbosity level (0=errors, 1=warnings, 2=info, 3=debug)

        Example:
            verbosity = config_mgr.get_verbosity()
        """
        return self._runtime_config.get_verbosity()

    def get_log_file(self) -> Optional[Path]:
        """
        Get log file path from configuration.

        Returns:
            Log file path or None if not configured

        Example:
            log_file = config_mgr.get_log_file()
        """
        log_file = self._runtime_config.get_log_file()
        return Path(log_file) if log_file else None

    def get_runtime_config(self) -> RuntimeConfig:
        """
        Get underlying RuntimeConfig instance.

        Returns:
            RuntimeConfig instance for advanced access

        Example:
            runtime_config = config_mgr.get_runtime_config()
            config_file_path = runtime_config.config_file_path
        """
        return self._runtime_config

    def to_dict(self) -> Dict[str, Any]:
        """
        Export resolved configuration as dictionary.

        Returns:
            Dictionary with all resolved configuration values

        Example:
            config_dict = config_mgr.to_dict()
            print(config_dict["directories"]["data_dir"])
        """
        return {
            "directories": {
                "data_dir": str(self.get_data_dir()) if self.get_data_dir() else None,
                "config_dir": str(self.get_config_dir()) if self.get_config_dir() else None,
                "runtime_dir": str(self.get_runtime_dir()) if self.get_runtime_dir() else None,
            },
            "logging": {
                "verbosity": self.get_verbosity(),
                "log_file": str(self.get_log_file()) if self.get_log_file() else None,
            },
            "sources": {
                "config_file": str(self._runtime_config.config_file_path)
                if self._runtime_config.config_file_path
                else None,
                "cli_overrides": {
                    "data_dir": str(self._cli_data_dir) if self._cli_data_dir else None,
                    "config_dir": str(self._cli_config_dir) if self._cli_config_dir else None,
                    "runtime_dir": str(self._cli_runtime_dir) if self._cli_runtime_dir else None,
                },
            },
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"ConfigManager("
            f"data_dir={self.get_data_dir()}, "
            f"config_dir={self.get_config_dir()}, "
            f"runtime_dir={self.get_runtime_dir()}, "
            f"verbosity={self.get_verbosity()})"
        )
