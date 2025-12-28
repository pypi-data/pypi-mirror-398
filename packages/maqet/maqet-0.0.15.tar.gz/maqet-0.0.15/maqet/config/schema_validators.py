"""
Dynamic configuration validation system using decorators.

This module provides a flexible, extensible validation system for YAML configurations.
Validators can be registered dynamically using the @config_validator decorator.

Architecture:
- Decorator-based validator registration
- Single source of truth for validation logic (delegates to InputValidator)
- Extensible at runtime (validators can be added dynamically)
- Validates configuration structure and normalizes values

Design Principles:
- DRY: Delegates validation logic to security.validation.InputValidator
- Open for extension: Use @config_validator to add new validators
- Clear separation: Schema validation here, runtime checks in validation.ConfigValidator
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..security.validation import InputValidator, ValidationError


class ConfigValidationError(Exception):
    """Configuration validation errors."""
    pass


@dataclass
class ValidatorMetadata:
    """Metadata for a registered validator."""
    key: str
    func: Callable
    required: bool
    description: Optional[str] = None


# Global registry of validators
_VALIDATOR_REGISTRY: Dict[str, ValidatorMetadata] = {}


def config_validator(key: str, required: bool = False, description: Optional[str] = None):
    """
    Decorator to register configuration validators.

    Validators are stored in a global registry and called during config validation.
    The decorated function should take a value and return the validated/normalized value.

    Args:
        key: Configuration key to validate (e.g., "binary", "memory")
        required: Whether this field is required in the configuration
        description: Optional human-readable description of what is validated

    Returns:
        Decorator function that registers the validator

    Example:
        @config_validator("custom_field", required=True)
        def validate_custom(value):
            if not isinstance(value, str):
                raise ValueError("Must be string")
            return value.upper()
    """
    def decorator(func: Callable) -> Callable:
        """Register validator and return original function."""
        metadata = ValidatorMetadata(
            key=key,
            func=func,
            required=required,
            description=description
        )
        _VALIDATOR_REGISTRY[key] = metadata
        return func

    return decorator


def get_validators() -> Dict[str, ValidatorMetadata]:
    """
    Get all registered validators.

    Returns:
        Dictionary mapping config keys to validator metadata
    """
    return _VALIDATOR_REGISTRY.copy()


def get_required_keys() -> List[str]:
    """
    Get list of required configuration keys.

    Returns:
        List of keys marked as required in their validators
    """
    return [
        key for key, metadata in _VALIDATOR_REGISTRY.items()
        if metadata.required
    ]


def validate_config_data(config_data: Any) -> Dict[str, Any]:
    """
    Validate and normalize configuration data.

    Applies all registered validators to the configuration.
    Unknown keys are preserved (forward compatibility).

    Args:
        config_data: Configuration dictionary to validate

    Returns:
        Validated and normalized configuration

    Raises:
        ConfigValidationError: If validation fails
    """
    # Check config_data is a dictionary
    if not isinstance(config_data, dict):
        raise ConfigValidationError(
            f"Configuration must be a dictionary, got {type(config_data).__name__}"
        )

    # Check required keys are present
    required_keys = get_required_keys()
    missing_keys = [key for key in required_keys if key not in config_data]
    if missing_keys:
        raise ConfigValidationError(
            f"Missing required configuration keys: {', '.join(missing_keys)}"
        )

    # Validate and normalize each key that has a validator
    validated_config = config_data.copy()

    for key, value in config_data.items():
        if key in _VALIDATOR_REGISTRY:
            validator_meta = _VALIDATOR_REGISTRY[key]
            try:
                # Apply validator function
                validated_config[key] = validator_meta.func(value)
            except (ValueError, ValidationError) as e:
                raise ConfigValidationError(
                    f"Validation failed for '{key}': {e}"
                )
            except ConfigValidationError:
                # Re-raise ConfigValidationError as-is
                raise

    return validated_config


# Built-in validators using InputValidator

@config_validator("binary", required=False, description="QEMU binary path")
def validate_binary(value: Any) -> str:
    """
    Validate QEMU binary path format (schema validation only).

    This performs lightweight format validation during configuration parsing.
    Expensive runtime checks (existence, permissions, health) are deferred to
    validation.ConfigValidator.validate_binary_health() when the binary is used.

    Schema Validation (this function):
    - Non-empty string or Path object
    - No whitespace-only values
    - Type validation

    Runtime Validation (validate_binary_health):
    - File exists
    - Is a file (not directory)
    - Has executable permissions
    - Binary health check (runs --version)

    Args:
        value: Binary path (string or Path)

    Returns:
        Validated path as string (format validated, may not exist on disk)

    Raises:
        ConfigValidationError: If path format is invalid

    Note:
        Allows test configs with mock binaries. Production code must call
        validate_binary_health() before using the binary.
    """
    if not value:
        raise ConfigValidationError("Binary path cannot be empty")

    if not isinstance(value, (str, Path)):
        raise ConfigValidationError(
            f"Binary must be string or Path, got {type(value).__name__}"
        )

    binary_str = str(value).strip()
    if not binary_str:
        raise ConfigValidationError("Binary path cannot be empty or whitespace")

    # Note: We only validate the path format here, not existence
    # Existence checks are done at runtime in validation.ConfigValidator.validate_binary_health()
    # This allows tests to use mock binaries and avoids failing during config parsing
    return binary_str


@config_validator("memory", required=False, description="VM memory allocation")
def validate_memory(value: Any) -> str:
    """
    Validate and normalize memory specification.

    Delegates to InputValidator.validate_memory for parsing and normalization.

    Args:
        value: Memory specification (string like "4G" or integer bytes)

    Returns:
        Normalized memory string (e.g., "4G", "2048M")

    Raises:
        ConfigValidationError: If memory format is invalid
    """
    try:
        return InputValidator.validate_memory(value)
    except ValidationError as e:
        raise ConfigValidationError(str(e))


@config_validator("cpu", required=False, description="CPU count")
def validate_cpu(value: Any) -> int:
    """
    Validate CPU count.

    Delegates to InputValidator.validate_cpu for range checking.

    Args:
        value: CPU count (int or string)

    Returns:
        Validated CPU count as integer

    Raises:
        ConfigValidationError: If CPU count is invalid
    """
    try:
        return InputValidator.validate_cpu(value)
    except ValidationError as e:
        raise ConfigValidationError(str(e))


@config_validator("storage", required=False, description="Storage configuration")
def validate_storage(value: Any) -> List[Dict[str, Any]]:
    """
    Validate storage configuration.

    Checks storage type and structure. Path validation delegated to
    storage.validate_storage_config for detailed checks.

    Args:
        value: Storage configuration (list of dicts)

    Returns:
        Validated storage configuration

    Raises:
        ConfigValidationError: If storage configuration is invalid
    """
    if not isinstance(value, list):
        raise ConfigValidationError(
            f"Storage must be a list, got {type(value).__name__}"
        )

    # Validate each storage device
    validated_storage = []

    for idx, storage_config in enumerate(value):
        if not isinstance(storage_config, dict):
            raise ConfigValidationError(
                f"Storage item {idx} must be a dictionary, got {type(storage_config).__name__}"
            )

        # Check required fields
        if "type" not in storage_config:
            raise ConfigValidationError(f"Storage item {idx} missing required 'type' field")

        storage_type = storage_config["type"]

        # Validate storage type
        valid_types = ["qcow2", "raw", "vmdk", "vdi", "vhd", "virtfs", "cdrom"]
        if storage_type not in valid_types:
            raise ConfigValidationError(
                f"Storage item {idx} has invalid type '{storage_type}'. "
                f"Valid types: {', '.join(valid_types)}"
            )

        # Type-specific validation
        if storage_type in ["qcow2", "raw", "vmdk", "vdi", "vhd", "cdrom"]:
            # File-based storage - path is optional for auto-creation
            # Check if path or file is provided
            path_value = storage_config.get("path") or storage_config.get("file")

            if path_value:
                # If path/file is provided, validate type
                if not isinstance(path_value, (str, Path)):
                    raise ConfigValidationError(
                        f"Storage item {idx} path must be string or Path, "
                        f"got {type(path_value).__name__}"
                    )
            # If no path/file, it will be auto-created - that's OK

        elif storage_type == "virtfs":
            # VirtFS requires path
            if "path" not in storage_config:
                raise ConfigValidationError(
                    f"Storage item {idx} (type=virtfs) missing required 'path' field"
                )

            # VirtFS can have mount_tag in options or top-level
            options = storage_config.get("options", {})
            if "mount_tag" not in options and "mount_tag" not in storage_config:
                # mount_tag is optional - will use name if not provided
                pass

        validated_storage.append(storage_config)

    return validated_storage


@config_validator("name", required=False, description="VM name")
def validate_name(value: Any) -> str:
    """
    Validate VM name.

    Delegates to InputValidator.validate_vm_name for security checks.

    Args:
        value: VM name

    Returns:
        Validated VM name

    Raises:
        ConfigValidationError: If VM name is invalid
    """
    try:
        return InputValidator.validate_vm_name(str(value))
    except ValidationError as e:
        raise ConfigValidationError(str(e))
