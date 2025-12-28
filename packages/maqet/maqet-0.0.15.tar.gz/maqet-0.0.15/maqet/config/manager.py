"""
Configuration Manager

Centralized configuration management for maqet.
Consolidates configuration from CLI args, environment variables,
config files, and defaults with clear precedence rules.
"""

from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional

from ..logger import LOG
from .merger import ConfigError, ConfigMerger
from .parser import ConfigParser
from .runtime_config import RuntimeConfig


class ConfigManager:
    """
    Centralized configuration management for maqet.

    Consolidates configuration from CLI args, environment variables,
    config files, and defaults with clear precedence rules.

    Precedence (highest to lowest):
    1. CLI arguments (cli_overrides)
    2. Environment variables (via RuntimeConfig)
    3. Config files (maqet.conf, VM YAML configs)
    4. Defaults (RuntimeConfig.DEFAULTS)

    Example:
        # Create with CLI overrides
        config = ConfigManager(cli_overrides={
            "directories": {"data_dir": "/custom/data"}
        })

        # Access configuration
        data_dir = config.get_data_dir()
        memory = config.get_vm_default("memory", "2G")
        verbosity = config.get_verbosity()
    """

    def __init__(
        self,
        cli_overrides: Optional[Dict[str, Any]] = None,
        runtime_config: Optional[RuntimeConfig] = None,
        config_parser: Optional[ConfigParser] = None,
    ):
        """
        Initialize configuration manager.

        Args:
            cli_overrides: CLI arguments that override all other sources
            runtime_config: Pre-loaded RuntimeConfig instance (optional)
            config_parser: ConfigParser instance for VM configs (optional)

        Example:
            config = ConfigManager(cli_overrides={
                "directories": {"data_dir": "/custom/data"},
                "logging": {"verbosity": 2}
            })
        """
        self.cli_overrides = cli_overrides or {}
        self._runtime_config = runtime_config
        self._config_parser = config_parser
        self._config: Dict[str, Any] = {}
        self._lock = RLock()

        # Load and merge all configurations
        self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load and merge all configurations.

        Precedence: CLI > Environment > Config File > Defaults

        Returns:
            Merged configuration dictionary
        """
        with self._lock:
            # Start with defaults from RuntimeConfig
            config = RuntimeConfig.DEFAULTS.copy()

            # Load runtime config (includes env vars and config files)
            if self._runtime_config is None:
                self._runtime_config = RuntimeConfig()

            # Merge runtime config (access internal _config)
            runtime_data = self._runtime_config._config
            config = ConfigMerger.deep_merge(config, runtime_data)

            # Merge CLI overrides (highest priority)
            config = ConfigMerger.deep_merge(config, self.cli_overrides)

            # Validate configuration
            self._validate(config)

            self._config = config
            return config

    def reload(self) -> None:
        """
        Reload configuration from disk.

        Useful for long-running processes that need to pick up config changes.
        Resets cache and re-loads all configuration sources.
        """
        with self._lock:
            # Reset runtime config to force reload
            self._runtime_config = None
            self.load()
            LOG.info("Configuration reloaded from disk")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Dot-separated key path (e.g., "directories.data_dir")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            data_dir = config.get("directories.data_dir")
            memory = config.get("vm_defaults.memory", "2G")
        """
        with self._lock:
            keys = key.split(".")
            value = self._config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

    def get_data_dir(self) -> Path:
        """
        Get data directory path.

        Returns:
            Data directory path (guaranteed to return valid Path)
        """
        data_dir = self.get("directories.data_dir")
        if data_dir:
            return Path(data_dir)

        # Fallback to RuntimeConfig, then XDG default
        runtime_dir = self._runtime_config.get_data_dir()
        if runtime_dir:
            return Path(runtime_dir)

        # Ultimate fallback: XDG standard
        import os

        xdg_data_home = os.environ.get(
            "XDG_DATA_HOME", str(Path.home() / ".local" / "share")
        )
        return Path(xdg_data_home) / "maqet"

    def get_config_dir(self) -> Path:
        """
        Get config directory path.

        Returns:
            Config directory path (guaranteed to return valid Path)
        """
        config_dir = self.get("directories.config_dir")
        if config_dir:
            return Path(config_dir)

        # Fallback to RuntimeConfig, then XDG default
        runtime_dir = self._runtime_config.get_config_dir()
        if runtime_dir:
            return Path(runtime_dir)

        # Ultimate fallback: XDG standard
        import os

        xdg_config_home = os.environ.get(
            "XDG_CONFIG_HOME", str(Path.home() / ".config")
        )
        return Path(xdg_config_home) / "maqet"

    def get_runtime_dir(self) -> Path:
        """
        Get runtime directory path.

        Returns:
            Runtime directory path (guaranteed to return valid Path)
        """
        runtime_dir = self.get("directories.runtime_dir")
        if runtime_dir:
            return Path(runtime_dir)

        # Fallback to RuntimeConfig, then XDG default
        rt_dir = self._runtime_config.get_runtime_dir()
        if rt_dir:
            return Path(rt_dir)

        # Ultimate fallback: XDG standard
        import os

        xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
        if xdg_runtime_dir:
            return Path(xdg_runtime_dir) / "maqet"

        # Fallback if XDG_RUNTIME_DIR not set
        return Path("/tmp") / f"maqet-{os.getuid()}"

    def get_vm_default(self, key: str, default: Any = None) -> Any:
        """
        Get VM default configuration value.

        Args:
            key: VM config key (e.g., "memory", "cpu")
            default: Default value if not found

        Returns:
            VM default value or default

        Example:
            memory = config.get_vm_default("memory", "2G")
            cpu = config.get_vm_default("cpu", 2)
        """
        return self.get(f"vm_defaults.{key}", default)

    def get_verbosity(self) -> int:
        """
        Get logging verbosity level.

        Returns:
            Verbosity level (0-3):
            - 0: Errors only
            - 1: Warnings
            - 2: Info
            - 3: Debug
        """
        return self.get("logging.verbosity", 0)

    def get_log_file(self) -> Optional[Path]:
        """
        Get log file path.

        Returns:
            Log file path or None if not configured
        """
        log_file = self.get("logging.log_file")
        return Path(log_file) if log_file else None

    def validate(self) -> None:
        """
        Validate all configuration values.

        Raises:
            ConfigError: If any configuration value is invalid
        """
        with self._lock:
            self._validate(self._config)

    def validate_vm_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate VM-specific configuration.

        Args:
            config_data: VM configuration dictionary

        Returns:
            Validated configuration data

        Raises:
            ConfigValidationError: If validation fails

        Example:
            config = {
                'binary': '/usr/bin/qemu-system-x86_64',
                'memory': '4G',
                'cpu': 2,
                'storage': [
                    {'name': 'hdd', 'size': '20G', 'type': 'qcow2'}
                ]
            }
            validated = config_manager.validate_vm_config(config)
        """
        # Use ConfigParser for VM validation if available
        if self._config_parser:
            return self._config_parser.validate_config(config_data)

        # Otherwise use validators module directly
        from .schema_validators import validate_config_data

        return validate_config_data(config_data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export configuration as dictionary.

        Returns:
            Complete configuration dictionary (deep copy)
        """
        with self._lock:
            import copy

            return copy.deepcopy(self._config)

    def get_config_sources(self) -> Dict[str, Any]:
        """
        Get information about configuration sources.

        Returns:
            Dictionary with:
            - config_file_path: Path to loaded config file
            - cli_overrides: CLI arguments applied
            - defaults_used: List of keys using default values

        Example:
            sources = config.get_config_sources()
            print(f"Config file: {sources['config_file_path']}")
            print(f"CLI overrides: {sources['cli_overrides']}")
        """
        with self._lock:
            config_file_path = None
            if self._runtime_config:
                config_file_path = self._runtime_config._config_file_path

            # Find keys using default values
            defaults_used = []
            for key in self._flatten_keys(RuntimeConfig.DEFAULTS):
                if self.get(key) == self._get_from_dict(
                    RuntimeConfig.DEFAULTS, key
                ):
                    defaults_used.append(key)

            return {
                "config_file_path": str(config_file_path)
                if config_file_path
                else None,
                "cli_overrides": self.cli_overrides.copy(),
                "defaults_used": defaults_used,
            }

    def _validate(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration values.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ConfigError: If validation fails
        """
        # Validate verbosity
        verbosity = config.get("logging", {}).get("verbosity")
        if verbosity is not None:
            if not isinstance(verbosity, int):
                raise ConfigError(
                    f"Invalid verbosity type: {type(verbosity).__name__}. "
                    f"Must be int (0-3)"
                )
            if verbosity < 0 or verbosity > 3:
                raise ConfigError(
                    f"Invalid verbosity: {verbosity}. Must be 0-3 "
                    f"(0=errors, 1=warnings, 2=info, 3=debug)"
                )

        # Validate log file path
        log_file = config.get("logging", {}).get("log_file")
        if log_file:
            log_path = Path(log_file)
            log_dir = log_path.parent
            if not log_dir.exists():
                raise ConfigError(
                    f"Log file directory does not exist: {log_dir}"
                )

        # Validate VM defaults if present
        vm_defaults = config.get("vm_defaults", {})
        if vm_defaults:
            # Validate memory format
            memory = vm_defaults.get("memory")
            if memory and not self._is_valid_memory_format(memory):
                raise ConfigError(
                    f"Invalid memory format: {memory}. "
                    f"Use format like '2G', '512M', '4096K'"
                )

            # Validate CPU count
            cpu = vm_defaults.get("cpu")
            if cpu is not None:
                if not isinstance(cpu, int):
                    raise ConfigError(
                        f"Invalid CPU type: {type(cpu).__name__}. Must be int"
                    )
                if cpu < 1:
                    raise ConfigError(
                        f"Invalid CPU count: {cpu}. Must be >= 1"
                    )

    def _is_valid_memory_format(self, memory: str) -> bool:
        """
        Validate memory format.

        Args:
            memory: Memory string (e.g., '2G', '512M')

        Returns:
            True if valid format, False otherwise
        """
        import re

        return bool(re.match(r"^\d+[KMGT]$", str(memory)))

    def _flatten_keys(self, d: Dict[str, Any], prefix: str = "") -> list:
        """
        Flatten nested dictionary keys into dot notation.

        Args:
            d: Dictionary to flatten
            prefix: Key prefix for recursion

        Returns:
            List of flattened keys
        """
        keys = []
        for k, v in d.items():
            new_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.extend(self._flatten_keys(v, new_key))
            else:
                keys.append(new_key)
        return keys

    def _get_from_dict(self, d: Dict[str, Any], key: str) -> Any:
        """
        Get value from nested dictionary using dot notation.

        Args:
            d: Dictionary to search
            key: Dot-separated key path

        Returns:
            Value or None if not found
        """
        keys = key.split(".")
        value = d
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value
