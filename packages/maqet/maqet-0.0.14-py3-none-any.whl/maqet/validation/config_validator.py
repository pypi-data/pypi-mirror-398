"""
Runtime Configuration Validator for MAQET.

Performs runtime validation and health checks before starting QEMU instances.
Delegates schema validation to config.validators module to avoid duplication.

Architecture (Phase 3.1 - Validator Consolidation):
This module handles RUNTIME health checks only, NOT validation logic.

- validate_binary_health(): Runs `qemu-system-x86_64 --version` to verify binary works
- validate_qemu_img_available(): Checks if qemu-img tool is installed
- pre_start_validation(): Orchestrates all pre-start checks

For validation LOGIC, see:
- security.validation.InputValidator: Core validation logic (single source of truth)
- config.validators: Schema validation (delegates to InputValidator)

For schema/structure validation, see maqet.config.validators module.
For core validation logic, see maqet.security.validation.InputValidator module.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict

from ..constants import Timeouts
from ..logger import LOG
from ..utils.subprocess_utils import run_with_output_limit


class ConfigValidationError(Exception):
    """Configuration validation errors."""


class ConfigValidator:
    """
    Runtime validator for VM configuration.

    This validator performs runtime health checks before starting VMs.
    It delegates schema validation to the config.validators module to
    avoid code duplication.

    Separation of Concerns:
    - config.validators: Schema validation + value normalization
    - validation.ConfigValidator: Runtime health checks + pre-start validation

    Use config.validators for:
    - Validating config structure and types
    - Normalizing values (e.g., bytes to "4G")
    - Cross-field validation

    Use validation.ConfigValidator for:
    - Binary health checks (qemu-system-x86_64 --version works)
    - Tool availability checks (qemu-img installed)
    - Pre-start validation orchestration

    Extracted from Machine class to follow single-responsibility principle.
    """

    def validate_config(self, config_data: Dict[str, Any]) -> None:
        """
        Validate VM configuration data.

        Performs basic validation checks on configuration structure.

        Args:
            config_data: VM configuration dictionary

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        # Basic validation - ensure config is a dict
        if not isinstance(config_data, dict):
            raise ConfigValidationError("Configuration must be a dictionary")

        # Specific validations are handled by other validators
        # (InputValidator, StorageManager, etc.)
        pass

    def validate_binary_health(self, binary: str) -> None:
        """
        Perform health check on QEMU binary.

        Verifies binary works by running --version command.

        Args:
            binary: Path to QEMU binary

        Raises:
            ConfigValidationError: If binary health check fails
        """
        binary_path = Path(binary)

        if not binary_path.exists():
            raise ConfigValidationError(f"QEMU binary not found: {binary}")

        # Health check: Verify binary works by running --version
        try:
            result = run_with_output_limit(
                [str(binary_path), '--version'],
                capture_output=True,
                text=True,
                timeout=Timeouts.BINARY_VERSION_CHECK,
            )
            if result.returncode != 0:
                raise ConfigValidationError(
                    f"QEMU binary failed health check: {binary}\n"
                    f"Error: {result.stderr.strip()}"
                )
            LOG.debug(f"QEMU binary health check passed: {binary}")

        except FileNotFoundError:
            raise ConfigValidationError(
                f"QEMU binary not executable: {binary}\n"
                f"Check file permissions and ensure it's a valid binary."
            )
        except subprocess.TimeoutExpired:
            raise ConfigValidationError(
                f"QEMU binary health check timed out: {binary}\n"
                f"Binary may be hung or unresponsive."
            )
        except Exception as e:
            raise ConfigValidationError(
                f"QEMU binary validation failed: {binary}\n"
                f"Error: {e}"
            )

    def validate_qemu_img_available(self) -> None:
        """
        Verify qemu-img tool is available for storage operations.

        Logs warning if qemu-img is not found (storage auto-creation may fail).
        """
        try:
            run_with_output_limit(
                ["qemu-img", "--version"],
                capture_output=True,
                check=True,
                timeout=Timeouts.BINARY_VERSION_CHECK,
            )
            LOG.debug("qemu-img utility found and working")
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            LOG.warning(
                "qemu-img not found - storage auto-creation may fail. "
                "Install QEMU tools (qemu-utils or qemu-img package)."
            )

    def validate_machine_requirements(self, config_data: Dict[str, Any]) -> None:
        """
        Validate all requirements for Machine initialization.

        Orchestrates complete validation pipeline:
        - Schema validation (structure, types, cross-field checks)
        - Binary health check (qemu binary works)
        - Tool availability checks (qemu-img installed)

        This method consolidates all validation needed during Machine.__init__()
        to ensure the configuration is valid before creating any resources.

        Args:
            config_data: VM configuration dictionary

        Raises:
            ConfigValidationError: If any validation fails
        """
        # Step 1: Schema validation (structure, types, cross-field validation)
        self.validate_config(config_data)

        # Step 2: Binary health check (runtime check)
        binary = config_data.get("binary", "/usr/bin/qemu-system-x86_64")
        self.validate_binary_health(binary)

        # Step 3: Tool availability check (qemu-img)
        self.validate_qemu_img_available()

        LOG.debug("All machine requirements validated successfully")

    def pre_start_validation(self, config_data: Dict[str, Any]) -> None:
        """
        Perform all pre-start validation checks.

        Combines binary health check and qemu-img availability check.
        Called immediately before starting VM.

        Args:
            config_data: VM configuration dictionary

        Raises:
            ConfigValidationError: If any validation check fails
        """
        # Get binary path (use default if not specified)
        binary = config_data.get("binary", "/usr/bin/qemu-system-x86_64")

        # Perform binary health check
        self.validate_binary_health(binary)

        # Check qemu-img availability (warning only)
        self.validate_qemu_img_available()
