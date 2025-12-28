"""
Configuration Merger

Handles deep-merging of multiple configuration files.
Provides utilities for loading and merging YAML configuration files
with deep merge support for complex nested structures.
"""

from pathlib import Path
from typing import Any, Dict, List, Union

import yaml

from ..exceptions import ConfigurationError


class ConfigLimits:
    """Configuration protection limits to prevent DoS attacks."""
    MAX_DEPTH = 10
    MAX_SIZE_BYTES = 1 * 1024 * 1024  # 1MB
    MAX_KEYS_PER_LEVEL = 1000


class ConfigError(ConfigurationError):
    """Configuration parsing errors (alias for ConfigurationError)."""


class ConfigMergeError(ConfigError):
    """Error during configuration merge (depth/size limits exceeded)."""


class ConfigMerger:
    """
    Handles deep-merging of multiple configuration files.

    Provides utilities for loading and merging YAML configuration files
    with deep merge support for complex nested structures.
    """

    @staticmethod
    def _merge_arguments_list(
        base_args: List[Any], override_args: List[Any]
    ) -> List[Any]:
        """
        Merge two arguments lists with override behavior.

        For arguments like [{foo: 0}, {bar: 10}] and [{bar: 20}, {baz: 30}],
        later configs override earlier ones by key, producing:
        [{foo: 0}, {bar: 20}, {baz: 30}]

        Args:
            base_args: Base arguments list
            override_args: Override arguments list

        Returns:
            Merged arguments list with overrides applied
        """
        # Track arguments by their keys (for dict items)
        # Use dict to maintain insertion order (Python 3.7+)
        merged = {}

        # Process base arguments first
        for arg in base_args:
            if isinstance(arg, dict):
                # For dict items, use the key as identifier
                for key in arg.keys():
                    merged[key] = arg
            else:
                # For non-dict items (strings), use the item itself as key
                merged[str(arg)] = arg

        # Process override arguments (later configs win)
        for arg in override_args:
            if isinstance(arg, dict):
                # Override or add dict items by key
                for key in arg.keys():
                    merged[key] = arg
            else:
                # Override or add non-dict items
                merged[str(arg)] = arg

        # Convert back to list, preserving order
        return list(merged.values())

    @staticmethod
    def deep_merge(
        base: Dict[str, Any],
        override: Dict[str, Any],
        *,
        _depth: int = 0,
        max_depth: int = ConfigLimits.MAX_DEPTH,
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries with protection limits.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
            _depth: Current recursion depth (internal use)
            max_depth: Maximum allowed recursion depth

        Returns:
            Deep-merged configuration dictionary

        Raises:
            ConfigMergeError: If depth or size limits exceeded
        """
        # Check depth limit
        if _depth > max_depth:
            raise ConfigMergeError(
                f"Configuration nesting exceeds maximum depth ({max_depth}). "
                "This may indicate a circular reference or malformed config."
            )

        # Check key count at this level
        if len(base) > ConfigLimits.MAX_KEYS_PER_LEVEL:
            raise ConfigMergeError(
                f"Configuration has too many keys at depth {_depth} "
                f"({len(base)} > {ConfigLimits.MAX_KEYS_PER_LEVEL})"
            )

        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries with depth tracking
                result[key] = ConfigMerger.deep_merge(
                    result[key], value, _depth=_depth + 1, max_depth=max_depth
                )
            elif (
                key in result
                and isinstance(result[key], list)
                and isinstance(value, list)
            ):
                # Special handling for 'arguments' list: merge dict items by key
                if key == "arguments":
                    result[key] = ConfigMerger._merge_arguments_list(
                        result[key], value
                    )
                else:
                    # For other lists (storage, etc.), concatenate
                    # This allows adding storage devices, network interfaces, etc.
                    result[key] = result[key] + value
            else:
                # Override scalar values and non-dict types
                result[key] = value

        return result

    # QEMU arguments that accept file paths as direct values
    # These will have their relative paths resolved to absolute
    PATH_BEARING_ARGS = frozenset({
        'kernel',     # Kernel image path
        'initrd',     # Initial ramdisk path
        'bios',       # BIOS/UEFI firmware path
        'pflash',     # Flash ROM images (can have multiple)
        'dtb',        # Device Tree Blob path
        'rom',        # ROM file path (option-rom)
        'loadvm',     # VM snapshot file
        'incoming',   # Migration file (can be file:path)
    })

    # Pattern prefixes in argument values that indicate file paths
    # Format: "prefix=path" or "prefix:path"
    PATH_PATTERNS = frozenset({
        'file=',      # drive file=./disk.qcow2
        'path=',      # chardev path=/tmp/serial
        'unix:',      # vnc unix:/tmp/vnc.sock
        'socket=',    # spice socket=/tmp/spice.sock
    })

    @staticmethod
    def _resolve_path_value(value: str, config_dir: Path) -> str:
        """
        Resolve a single path value if it's relative.

        Args:
            value: Path string (may be relative or absolute)
            config_dir: Directory to resolve relative paths against

        Returns:
            Resolved absolute path string
        """
        if not value or not isinstance(value, str):
            return value

        # Check if value is a path and relative
        value_path = Path(value)
        if not value_path.is_absolute():
            return str((config_dir / value).resolve())

        return value

    @staticmethod
    def _resolve_pattern_in_value(
        value: str, config_dir: Path
    ) -> str:
        """
        Resolve file paths in complex argument values with patterns.

        Handles patterns like:
        - file=/path/to/disk.qcow2,media=cdrom
        - path=/tmp/serial,mode=0600
        - unix:/tmp/vnc.sock

        Args:
            value: Argument value string
            config_dir: Directory to resolve relative paths against

        Returns:
            Value with resolved paths
        """
        if not isinstance(value, str):
            return value

        # Check for pattern-based paths
        for pattern in ConfigMerger.PATH_PATTERNS:
            if pattern in value:
                if ',' in value:
                    # Complex pattern: file=./disk.qcow2,media=cdrom
                    parts = value.split(",")
                    for i, part in enumerate(parts):
                        if part.startswith(pattern):
                            # Extract path after pattern prefix
                            path_value = part[len(pattern):]
                            if path_value and not Path(path_value).is_absolute():
                                abs_path = str(
                                    (config_dir / path_value).resolve()
                                )
                                parts[i] = f"{pattern}{abs_path}"
                    return ",".join(parts)
                elif value.startswith(pattern):
                    # Simple pattern: file=./disk.qcow2 or unix:/tmp/vnc.sock
                    path_value = value[len(pattern):]
                    if path_value and not Path(path_value).is_absolute():
                        abs_path = str(
                            (config_dir / path_value).resolve()
                        )
                        return f"{pattern}{abs_path}"

        return value

    @staticmethod
    def _resolve_relative_paths(
        config_data: Dict[str, Any], config_dir: Path
    ) -> Dict[str, Any]:
        """
        Resolve relative file paths in config to absolute paths.

        Layer 3 of automatic path resolution: resolve paths relative to config file location.
        This makes configs portable and allows relative paths like ./live.iso to work.

        Resolves paths in:
        1. storage[].file - Main storage file path (QCOW2, raw, etc.)
        2. storage[].path - VirtFS shared directory path
        3. Path-bearing arguments (kernel, initrd, bios, pflash, dtb, rom, etc.)
        4. Pattern-based paths in arguments (file=, path=, unix:, socket=)

        Note: storage[].backing_file is NOT resolved here. It's resolved relative
        to the delta image directory by storage.py (see commit a6cf3e6).

        Args:
            config_data: Configuration dictionary
            config_dir: Directory containing the config file

        Returns:
            Configuration with resolved absolute paths
        """
        # Resolve storage device file paths using helper method
        if "storage" in config_data and isinstance(
            config_data["storage"], list
        ):
            for storage_item in config_data["storage"]:
                if isinstance(storage_item, dict):
                    # Resolve main storage file path
                    if "file" in storage_item:
                        storage_item["file"] = ConfigMerger._resolve_path_value(
                            storage_item["file"], config_dir
                        )

                    # DON'T resolve backing_file here!
                    # backing_file paths are resolved relative to delta image directory
                    # by storage.py, not config directory. See commit a6cf3e6.
                    # This enables portable delta+base image pairs that can be moved together.

                    # Resolve VirtFS path entries
                    if "path" in storage_item:
                        storage_item["path"] = ConfigMerger._resolve_path_value(
                            storage_item["path"], config_dir
                        )

        # Resolve file paths in arguments
        if "arguments" in config_data and isinstance(
            config_data["arguments"], list
        ):
            for arg_item in config_data["arguments"]:
                if isinstance(arg_item, dict):
                    for key, value in list(arg_item.items()):
                        # Skip non-string values
                        if not isinstance(value, str):
                            continue

                        # Pattern 1: Direct path-bearing arguments
                        # Example: {kernel: "./vmlinuz"} -> {kernel: "/abs/path/vmlinuz"}
                        if key in ConfigMerger.PATH_BEARING_ARGS:
                            arg_item[key] = ConfigMerger._resolve_path_value(
                                value, config_dir
                            )
                            continue

                        # Pattern 2: Complex values with path patterns
                        # Example: {drive: "file=./disk.qcow2,media=cdrom"}
                        # Only process if value contains a pattern to avoid unnecessary overhead
                        if any(pattern in value for pattern in ConfigMerger.PATH_PATTERNS):
                            arg_item[key] = ConfigMerger._resolve_pattern_in_value(
                                value, config_dir
                            )

        return config_data

    @staticmethod
    def validate_config_size(config_path: Path) -> None:
        """Validate config file size before loading.

        Args:
            config_path: Path to configuration file

        Raises:
            ConfigMergeError: If file exceeds size limit
        """
        size = config_path.stat().st_size
        if size > ConfigLimits.MAX_SIZE_BYTES:
            raise ConfigMergeError(
                f"Configuration file too large: {size} bytes "
                f"(max: {ConfigLimits.MAX_SIZE_BYTES})"
            )

    @staticmethod
    def load_and_merge_files(
        config_files: Union[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Load and merge multiple configuration files.

        Args:
            config_files: Single config file path or list of config file paths

        Returns:
            Merged configuration data

        Raises:
            ConfigError: If any config file cannot be loaded or parsed
        """
        if isinstance(config_files, str):
            config_files = [config_files]

        if not config_files:
            return {}

        merged_config = {}

        for config_file in config_files:
            config_path = Path(config_file)
            if not config_path.exists():
                raise ConfigError(
                    f"Configuration file not found: {config_file}"
                )

            # Validate file size before loading
            ConfigMerger.validate_config_size(config_path)

            try:
                with open(config_path) as f:
                    config_data = yaml.safe_load(f) or {}

                if not isinstance(config_data, dict):
                    raise ConfigError(
                        f"Configuration in {config_file} must be a "
                        f"YAML dictionary"
                    )

                # Layer 3: Resolve relative paths in config relative to config file location
                config_dir = config_path.parent.resolve()
                config_data = ConfigMerger._resolve_relative_paths(
                    config_data, config_dir
                )

                # Deep merge with previous configs
                merged_config = ConfigMerger.deep_merge(
                    merged_config, config_data
                )

            except yaml.YAMLError as e:
                raise ConfigError(f"Invalid YAML in {config_file}: {e}")
            except Exception as e:
                raise ConfigError(
                    f"Error loading configuration from {config_file}: {e}"
                )

        return merged_config
