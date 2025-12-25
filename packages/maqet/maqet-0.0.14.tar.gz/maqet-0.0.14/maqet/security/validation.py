"""
Input validation for security-sensitive parameters.

This module provides centralized validation to prevent:
- Command injection (shell metacharacters)
- Argument injection (leading hyphens)
- Path traversal (.. sequences)
- Resource exhaustion (length limits)
- Encoding attacks (non-ASCII)
"""

import os
import re
from pathlib import Path
from typing import Pattern, Optional, List, Union

from ..utils.paths import ensure_path
from ..constants import SecurityPaths
from ..exceptions import ConfigValidationError


class ValidationError(ConfigValidationError):
    """Input validation error.

    Inherits from ConfigValidationError to integrate with maqet's
    exception hierarchy, allowing callers to catch configuration
    validation errors consistently.
    """
    pass


class InputValidator:
    """Centralized input validation for security-sensitive inputs."""

    # Validation patterns
    VM_ID_PATTERN: Pattern = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')
    VM_NAME_PATTERN: Pattern = re.compile(r'^[a-zA-Z0-9_\-\.]{1,255}$')
    SOCKET_NAME_PATTERN: Pattern = re.compile(r'^[a-zA-Z0-9_\-\.]{1,100}$')

    # Dangerous characters
    SHELL_METACHARACTERS = frozenset({';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r'})
    PATH_TRAVERSAL_SEQUENCES = frozenset({'..', '~'})

    @classmethod
    def validate_vm_id(cls, vm_id: str) -> str:
        """
        Validate VM ID for security and correctness.

        Requirements:
        - 1-64 characters
        - Alphanumeric, underscore, hyphen only
        - Cannot start with hyphen (argument injection)
        - Cannot contain .. (path traversal)

        Args:
            vm_id: VM identifier from user input

        Returns:
            Validated vm_id (unchanged if valid)

        Raises:
            ValidationError: If vm_id is invalid
        """
        if not vm_id:
            raise ValidationError("VM ID cannot be empty")

        if not isinstance(vm_id, str):
            raise ValidationError(
                f"VM ID must be string, got {type(vm_id).__name__}"
            )

        # Check pattern
        if not cls.VM_ID_PATTERN.match(vm_id):
            raise ValidationError(
                f"Invalid VM ID '{vm_id}'. "
                f"Must contain only alphanumeric, underscore, hyphen (1-64 chars)"
            )

        # Prevent argument injection
        if vm_id.startswith('-'):
            raise ValidationError(
                f"VM ID cannot start with hyphen: '{vm_id}' "
                f"(argument injection risk)"
            )

        # Prevent path traversal
        if '..' in vm_id:
            raise ValidationError(
                f"VM ID cannot contain '..': '{vm_id}' "
                f"(path traversal risk)"
            )

        return vm_id

    @classmethod
    def validate_vm_name(cls, vm_name: str) -> str:
        """
        Validate VM name (more permissive than ID).

        Allows dots for domain-like names (e.g., "web.prod.example").
        """
        if not vm_name:
            raise ValidationError("VM name cannot be empty")

        if not cls.VM_NAME_PATTERN.match(vm_name):
            raise ValidationError(
                f"Invalid VM name '{vm_name}'. "
                f"Must contain only alphanumeric, underscore, hyphen, dot (1-255 chars)"
            )

        if vm_name.startswith('-'):
            raise ValidationError(
                f"VM name cannot start with hyphen: '{vm_name}'"
            )

        # Check for consecutive dots or path traversal
        if '..' in vm_name:
            raise ValidationError(
                f"VM name cannot contain '..': '{vm_name}'"
            )

        return vm_name

    @classmethod
    def validate_path(
        cls,
        path: Union[str, Path],
        must_exist: bool = False,
        must_be_absolute: bool = False,
        allowed_prefixes: Optional[List[Path]] = None,
        description: str = "Path"
    ) -> Path:
        """
        Validate filesystem path for security.

        Args:
            path: Path to validate
            must_exist: If True, path must exist
            must_be_absolute: If True, path must be absolute
            allowed_prefixes: If provided, path must be under one of these
            description: Human-readable description for error messages

        Returns:
            Resolved absolute path

        Raises:
            ValidationError: If path is invalid or unsafe
        """
        if not path:
            raise ValidationError(f"{description} cannot be empty")

        # Convert to Path object
        path = ensure_path(path)

        # Check for null bytes (path injection)
        path_str = str(path)
        if '\0' in path_str:
            raise ValidationError(
                f"{description} contains null byte: {path_str}"
            )

        # Check for shell metacharacters (if used in commands)
        for metachar in cls.SHELL_METACHARACTERS:
            if metachar in path_str:
                raise ValidationError(
                    f"{description} contains shell metacharacter '{metachar}': {path_str}"
                )

        # Check absolute requirement
        if must_be_absolute and not path.is_absolute():
            raise ValidationError(
                f"{description} must be absolute: {path}"
            )

        # Resolve path (follow symlinks, remove ..)
        try:
            resolved_path = path.resolve(strict=must_exist)
        except (OSError, RuntimeError) as e:
            raise ValidationError(
                f"Cannot resolve {description} '{path}': {e}"
            )

        # Check existence
        if must_exist and not resolved_path.exists():
            raise ValidationError(
                f"{description} does not exist: {resolved_path}"
            )

        # Check allowed prefixes
        if allowed_prefixes:
            is_allowed = any(
                resolved_path.is_relative_to(prefix.resolve())
                for prefix in allowed_prefixes
            )
            if not is_allowed:
                raise ValidationError(
                    f"{description} not under allowed prefixes: {resolved_path}. "
                    f"Allowed: {[str(p) for p in allowed_prefixes]}"
                )

        return resolved_path

    @classmethod
    def validate_binary_path(cls, binary_path: Path) -> Path:
        """
        Validate executable binary path.

        Checks:
        - Path exists and is a file
        - File is executable
        - File is not world-writable (security)

        Returns:
            Validated binary path

        Raises:
            ValidationError: If binary is invalid or insecure
        """
        import os
        import stat

        binary_path = cls.validate_path(
            binary_path,
            must_exist=True,
            description="Binary path"
        )

        # Check is file
        if not binary_path.is_file():
            raise ValidationError(
                f"Binary is not a file: {binary_path}"
            )

        # Check executable
        if not os.access(binary_path, os.X_OK):
            raise ValidationError(
                f"Binary is not executable: {binary_path}"
            )

        # Check not world-writable (security risk)
        stat_info = binary_path.stat()
        if stat_info.st_mode & stat.S_IWOTH:
            raise ValidationError(
                f"Binary is world-writable (insecure): {binary_path}"
            )

        return binary_path

    @classmethod
    def validate_memory(cls, value: any) -> str:
        """
        Validate memory specification for VMs.

        Accepts:
        - String format: '4G', '2048M', '1T'
        - Integer (bytes): Converts to megabytes
        - Plain digits as string: Converts to megabytes

        Args:
            value: Memory specification (string or int)

        Returns:
            Normalized memory string (e.g., '4G', '2048M')

        Raises:
            ValidationError: If memory format is invalid

        Examples:
            validate_memory('4G') -> '4G'
            validate_memory(4294967296) -> '4096M'
            validate_memory('2048') -> '1M'
        """
        if isinstance(value, int):
            # Convert bytes to megabytes
            if value < 0:
                raise ValidationError("Memory cannot be negative")
            return f"{value // (1024 * 1024)}M"

        if not isinstance(value, str):
            raise ValidationError(
                f"Memory must be string or integer, got {type(value).__name__}"
            )

        memory = value.strip()

        # Check for valid memory format: digits followed by M/G/T
        if re.match(r"^\d+[MGT]$", memory):
            return memory
        elif memory.isdigit():
            # Assume bytes, convert to megabytes
            mb_value = int(memory) // (1024 * 1024)
            if mb_value == 0:
                raise ValidationError(
                    f"Memory value too small: {memory} bytes. Minimum 1MB required."
                )
            return f"{mb_value}M"
        else:
            raise ValidationError(
                f"Invalid memory format: '{memory}'. "
                f"Use format like '4G', '2048M', or bytes as integer"
            )

    @classmethod
    def validate_cpu(cls, value: any) -> int:
        """
        Validate CPU count for VMs.

        Checks:
        - Must be positive integer
        - Must be at least 1
        - Must not exceed 64 (QEMU practical limit)

        Args:
            value: CPU count (int or string)

        Returns:
            Validated CPU count as integer

        Raises:
            ValidationError: If CPU count is invalid

        Examples:
            validate_cpu(4) -> 4
            validate_cpu('8') -> 8
        """
        try:
            cpu_count = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"CPU count must be integer, got {type(value).__name__}"
            )

        if cpu_count < 1:
            raise ValidationError("CPU count must be at least 1")

        if cpu_count > 64:
            raise ValidationError(
                "CPU count cannot exceed 64 (QEMU maximum)"
            )

        return cpu_count

    @classmethod
    def validate_storage_path(cls, path: Path, description: str = "Storage path") -> Path:
        """
        Validate storage file path is safe to write to.

        Checks:
        1. Path resolves correctly
        2. Not in system directories (checked FIRST for security)
        3. Parent directory exists and is writable

        Args:
            path: Storage file path to validate
            description: Description for error messages

        Returns:
            Resolved absolute path

        Raises:
            ValidationError: If path is unsafe
        """
        # Basic path validation
        resolved = cls.validate_path(path, description=description, must_exist=False)

        # Check if path is in safe subdirectory allowlist (e.g., /dev/shm)
        is_in_safe_subdir = False
        for safe_path in SecurityPaths.SAFE_SUBDIRECTORIES:
            try:
                safe_resolved = safe_path.resolve()
                if resolved.is_relative_to(safe_resolved):
                    is_in_safe_subdir = True
                    break
            except (OSError, RuntimeError, ValueError):
                continue

        # Check not in system directories FIRST (security check takes priority)
        # Skip this check if path is in safe subdirectory allowlist
        if not is_in_safe_subdir:
            for dangerous in SecurityPaths.DANGEROUS_SYSTEM_PATHS:
                try:
                    dangerous_resolved = dangerous.resolve()
                except (OSError, RuntimeError):
                    # Can't resolve dangerous path - skip this check
                    continue

                try:
                    is_relative = resolved.is_relative_to(dangerous_resolved)
                except ValueError:
                    # is_relative_to can raise ValueError if paths are on different drives
                    # Not relative to this dangerous path - OK
                    continue

                if is_relative:
                    raise ValidationError(
                        f"{description} cannot be in system directory: {dangerous}\n"
                        f"Use a user directory like /tmp, /home, or /var/lib/maqet instead"
                    )

        # Only check parent permissions after security checks pass
        parent = resolved.parent
        if not parent.exists():
            raise ValidationError(
                f"Parent directory does not exist: {parent}\n"
                f"Create it first with: mkdir -p {parent}"
            )

        # Check parent is actually a directory (not a file)
        if not parent.is_dir():
            raise ValidationError(
                f"Parent path is not a directory: {parent}\n"
                f"Cannot create storage file in a non-directory"
            )

        if not os.access(parent, os.W_OK):
            raise ValidationError(
                f"Cannot write to directory: {parent}\n"
                f"Check permissions with: ls -ld {parent}"
            )

        return resolved

    @classmethod
    def validate_share_path(cls, path: Path, description: str = "Share path") -> Path:
        """
        Validate VirtFS share path (must exist and be directory).

        Args:
            path: Directory to share via VirtFS
            description: Description for error messages

        Returns:
            Resolved absolute path

        Raises:
            ValidationError: If path is invalid
        """
        # Must exist
        resolved = cls.validate_path(path, description=description, must_exist=True)

        # Must be directory
        if not resolved.is_dir():
            raise ValidationError(f"{description} must be a directory, got file: {path}")

        # Check if path is in safe subdirectory allowlist (e.g., /dev/shm)
        is_in_safe_subdir = False
        for safe_path in SecurityPaths.SAFE_SUBDIRECTORIES:
            try:
                safe_resolved = safe_path.resolve()
                if resolved.is_relative_to(safe_resolved):
                    is_in_safe_subdir = True
                    break
            except (OSError, RuntimeError, ValueError):
                continue

        # Check not in dangerous system paths (warn only, might be intentional for read-only)
        # Skip warning for safe subdirectories
        if not is_in_safe_subdir:
            for dangerous in SecurityPaths.DANGEROUS_SYSTEM_PATHS:
                try:
                    dangerous_resolved = dangerous.resolve()
                except (OSError, RuntimeError):
                    # Can't resolve dangerous path - skip this check
                    continue

                try:
                    is_relative = resolved.is_relative_to(dangerous_resolved)
                except ValueError:
                    # is_relative_to can raise ValueError if paths are on different drives
                    continue

                if is_relative:
                    # Only warn for VirtFS (might be intentional for read-only shares)
                    import logging
                    logging.warning(
                        f"Sharing system directory via VirtFS: {dangerous}. "
                        "This may be intentional but use caution."
                    )

        return resolved

    @classmethod
    def parse_size(cls, size_str: str) -> int:
        """
        Parse size string with units to bytes.

        Supports: K, M, G, T (powers of 1024)
        Examples: "8G" -> 8589934592, "512M" -> 536870912

        Args:
            size_str: Size string (e.g., "8G", "512M")

        Returns:
            Size in bytes

        Raises:
            ValidationError: If format is invalid
        """
        size_str = size_str.strip().upper()

        # Match number + optional unit
        match = re.match(r'^(\d+)([KMGT])?$', size_str)
        if not match:
            raise ValidationError(
                f"Invalid size format: '{size_str}'\n"
                "Use format: <number>[K|M|G|T] (e.g., 8G, 512M)"
            )

        value = int(match.group(1))
        unit = match.group(2) or ''

        # Convert to bytes
        multipliers = {
            '': 1,
            'K': 1024,
            'M': 1024 ** 2,
            'G': 1024 ** 3,
            'T': 1024 ** 4,
        }

        return value * multipliers[unit]
