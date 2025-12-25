"""
Configuration Parser

Parses YAML configuration files for VM settings only.
Does NOT execute API commands - configs are purely for VM configuration.
Supports multiple config file deep-merging for flexible VM configuration.
"""

import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from ..maqet import Maqet

from .merger import ConfigError


class ConfigParser:
    """
    Parses and validates VM configuration files.

    This parser handles YAML configuration files for VM settings ONLY.
    It does NOT execute API commands - those should be handled separately
    by calling methods on the Maqet instance.

    The parser validates configuration structure and types but does not
    start VMs or execute commands.

    NOTE: Configuration parsing flow:
    1. ConfigParser.parse_config() - Loads and validates YAML
    2. Machine._configure_machine() - Converts config to QEMU args
    3. ConfigHandlers (config_handlers.py) - Handler-based config processing
    4. StorageManager.get_qemu_args() - Storage-specific QEMU args

    The old qemu_args.py approach has been replaced with the extensible
    handler-based system for better maintainability and test coverage.
    """

    def __init__(self, maqet_instance: "Maqet"):
        """
        Initialize config parser.

        Args:
            maqet_instance: Maqet instance for validation context
        """
        self.maqet = maqet_instance

    def parse_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse configuration dictionary.

        Args:
            config_data: Configuration dictionary

        Returns:
            Normalized configuration data
        """
        if not isinstance(config_data, dict):
            raise ConfigError("Configuration must be a dictionary")

        return config_data

    def validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate VM configuration data.

        This method validates VM configuration settings without executing
        any API commands. Configuration files are purely for VM settings.

        Args:
            config_data: Configuration dictionary

        Returns:
            Validated configuration data

        Raises:
            ConfigError: If config contains API commands or validation fails

        Example:
            config = {
                'binary': '/usr/bin/qemu-system-x86_64',
                'memory': '4G',
                'cpu': 2,
                'storage': [
                    {'name': 'hdd', 'size': '20G', 'type': 'qcow2'}
                ]
            }
            validated = parser.validate_config(config)
        """

        # Use validation system
        from maqet.validation.config_validator import ConfigValidationError

        # File integrity validation implemented in _validate_config_file_security():
        # - Size limit check (10MB) prevents DoS with huge YAML
        # - World-writable permission warning for security
        # - File ownership validation (warns if not owned by current user)
        # - yaml.safe_load used in merger.py prevents code execution
        # NOTE: Checksum/signature validation not implemented (would require key management)
        try:
            # Check for API commands in config (prevent confusion)
            api_registry = self.maqet.get_api_registry()
            api_methods = api_registry.get_all_methods()
            # api_methods returns List[APIMethodMetadata], not dicts
            api_names = {method.name for method in api_methods}

            forbidden_keys = set(config_data.keys()) & api_names
            if forbidden_keys:
                raise ConfigError(
                    f"Configuration cannot contain API commands: {forbidden_keys}. "
                    f"API commands should be called via maqet CLI or Python API, "
                    f"not stored in VM configuration files."
                )

            # Unknown keys are silently ignored - no validation needed
            # This allows forward compatibility and flexibility in config files

            # Early storage validation to fail fast before VM creation
            if "storage" in config_data:
                from ..storage import validate_storage_config

                try:
                    validate_storage_config(config_data["storage"])
                except ValueError as e:
                    raise ConfigError(f"Storage configuration error: {e}")

            # Basic validation done, specific validation happens in Machine/Storage classes
            return config_data

        except ConfigValidationError as e:
            raise ConfigError(str(e))

    def _validate_config_file_security(self, config_path: str) -> None:
        """
        Validate configuration file security before loading.

        Args:
            config_path: Path to YAML configuration file

        Raises:
            ConfigError: If file has security issues
        """

        # Using pathlib for modern path handling
        path = Path(config_path)

        # Check if file exists first
        if not path.exists():
            # Let load_and_merge_files handle the FileNotFoundError
            return

        # Check file size to prevent DoS with huge YAML files
        max_size = 10 * 1024 * 1024  # 10MB limit
        file_stat = path.stat()
        file_size = file_stat.st_size
        if file_size > max_size:
            raise ConfigError(
                f"Configuration file too large ({file_size} bytes, max {
                    max_size}). "
                f"This may indicate a malicious or corrupted file."
            )

        # Check file permissions - warn if world-writable
        mode = file_stat.st_mode
        # FIXME(m4x0n, 2025-10-10): Missing import. Issue #1 in
        # CODE_ISSUES_REPORT.md - needs `import stat` at module level.
        if mode & stat.S_IWOTH:
            from ..logger import LOG

            LOG.warning(
                f"Configuration file {config_path} is world-writable. "
                f"This is a security risk as anyone can modify VM settings."
            )

        # Check if file is owned by current user (Unix only)
        # FIXME(m4x0n, 2025-10-10): Missing import. Issue #2 in
        # CODE_ISSUES_REPORT.md - needs `import os` at module level.
        if hasattr(os, "getuid"):
            current_uid = os.getuid()
            if file_stat.st_uid != current_uid:
                from ..logger import LOG

                LOG.warning(
                    f"Configuration file {
                        config_path} is not owned by current user. "
                    f"Verify the file source before using."
                )

    def load_and_validate(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration file and validate it.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Validated configuration data

        Raises:
            ConfigError: If file cannot be loaded or validation fails
        """
        from .merger import ConfigMerger

        # Validate file security before loading
        self._validate_config_file_security(config_path)

        # Load single config file (uses yaml.safe_load for security)
        config_data = ConfigMerger.load_and_merge_files(config_path)

        # Validate the loaded config
        return self.validate_config(config_data)
