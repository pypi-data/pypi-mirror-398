"""
Unified Storage Management System

Provides extensible storage device management with integrated snapshot support.
Supports multiple storage types (QCOW2, Raw, VirtFS) with plugin-style extensibility.

Path Handling:
- Functions accept Union[str, Path] for path parameters
- Internally uses pathlib.Path objects for all path operations
- Converts to str only when calling qemu-img subprocess or serializing
- Storage paths are validated using pathlib path traversal protection
"""

import fcntl
import os
import shutil
import stat
import subprocess
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .logger import LOG
from .exceptions import StorageError, ConfigValidationError
from .constants import SecurityPaths
from .security.validation import InputValidator, ValidationError
from .utils.subprocess_utils import run_with_output_limit


class BaseStorageDevice(ABC):
    """Abstract base class for all storage devices.

    # NOTE: Good - abstract base classes with @abstractmethod decorators
    # enforce
    # a consistent interface across all storage types. This makes the system
    #       predictable and extensible.
    """

    def __init__(self, config: Dict[str, Any], vm_id: str, index: int):
        """
        Initialize storage device.

        Args:
            config: Storage device configuration dictionary
            vm_id: VM identifier
            index: Device index for naming/ordering
        """
        self.config = config
        self.vm_id = vm_id
        self.index = index
        self.name = config.get("name", f"storage{index}")

    @abstractmethod
    def get_qemu_args(self) -> List[str]:
        """
        Get QEMU command line arguments for this storage device.

        Returns:
            List of QEMU arguments
        """

    @abstractmethod
    def create_if_needed(self) -> None:
        """Create storage device if it doesn't exist and should be auto-created."""

    @abstractmethod
    def supports_snapshots(self) -> bool:
        """Check if this storage type supports snapshots."""

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this storage device.

        Returns:
            Dictionary with device information
        """
        return {
            "name": self.name,
            "type": self.get_type(),
            "config": self.config,
            "supports_snapshots": self.supports_snapshots(),
        }

    @abstractmethod
    def get_type(self) -> str:
        """Get storage device type name."""


class FileBasedStorageDevice(BaseStorageDevice):
    """Base class for file-based storage devices (QCOW2, Raw)."""

    # Class-level cache for qemu-img binary path (shared across all instances)
    _qemu_img_path: Optional[str] = None
    _qemu_img_lock = threading.Lock()

    VALID_INTERFACES = {"virtio", "sata", "ide", "scsi", "none"}

    def __init__(self, config: Dict[str, Any], vm_id: str, index: int):
        """Initialize file-based storage device."""
        super().__init__(config, vm_id, index)

        # Get or generate file path
        self.file_path = self._get_file_path()
        self.backing_file = config.get("backing_file")
        self.backing_format = config.get("backing_format", "qcow2")

        # Size is optional when backing_file is specified (inherited from backing file)
        # Default to 10G for non-backed images
        self.size = config.get("size", "10G" if not self.backing_file else None)
        self.interface = config.get("interface", "virtio")

        # Validate configuration
        if self.backing_file:
            self._validate_backing_file()
        if self.size:
            self._validate_size(self.size)
        self._validate_interface(self.interface)

    def _get_file_path(self) -> Path:
        """Get storage file path with security validation."""
        file_config = self.config.get("file")
        if file_config:
            # Convert to absolute path and resolve symlinks
            try:
                user_path = Path(file_config).resolve(strict=False)
            except (OSError, RuntimeError) as e:
                raise ValueError(
                    f"Invalid storage file path '{file_config}': {e}"
                )

            # Validate path is not dangerous
            self._validate_storage_path(user_path)
            return user_path

        # Generate default path in /tmp
        file_extension = self.get_type().lower()
        return Path(f"/tmp/maqet-{self.vm_id}-{self.name}.{file_extension}")

    def _validate_storage_path(self, path: Path) -> None:
        """
        Validate storage path is safe to write to.

        Delegates to InputValidator for security validation.

        Args:
            path: Storage file path to validate

        Raises:
            ValueError: If path is dangerous or invalid
        """
        try:
            InputValidator.validate_storage_path(path, description="Storage file")
        except ValidationError as e:
            raise ValueError(str(e))

        # Note: File existence check removed - files are only created if they don't exist
        # (see create_if_needed which checks file_path.exists() before creating)

    def _validate_size(self, size: str) -> None:
        """
        Validate size format is compatible with qemu-img.

        Delegates to InputValidator for validation logic.
        """
        try:
            InputValidator.parse_size(size)
        except ValidationError as e:
            raise ValueError(str(e))

    def _validate_interface(self, interface: str) -> None:
        """Validate interface type is supported."""
        if interface not in self.VALID_INTERFACES:
            raise ValueError(
                f"Invalid interface '{interface}'. "
                f"Valid interfaces: {', '.join(sorted(self.VALID_INTERFACES))}"
            )

    def _validate_backing_file(self) -> None:
        """Validate backing file exists and is accessible.

        The original backing_file path (relative or absolute) is preserved unchanged
        for qemu-img. Validation resolves the path temporarily to verify existence
        and accessibility, but self.backing_file remains as originally configured.
        """
        if not self.backing_file:
            return

        backing_path = Path(self.backing_file)

        # Resolve relative paths relative to delta image's directory for validation
        # Absolute paths are used as-is
        if not backing_path.is_absolute():
            delta_dir = self.file_path.parent
            backing_path = delta_dir / backing_path

        # Resolve to absolute path FOR VALIDATION ONLY
        # self.backing_file remains unchanged (preserves original relative/absolute path)
        try:
            backing_path = backing_path.resolve(strict=True)
        except (OSError, RuntimeError, FileNotFoundError) as e:
            raise ValueError(
                f"Backing file does not exist or cannot be accessed: {self.backing_file}. "
                f"Resolved path: {backing_path}. Error: {e}"
            )

        # Check it's a regular file
        if not backing_path.is_file():
            raise ValueError(
                f"Backing file is not a regular file: {backing_path}"
            )

        # Check it's readable
        if not os.access(backing_path, os.R_OK):
            raise ValueError(
                f"Backing file is not readable: {backing_path}. "
                f"Check permissions: ls -l {backing_path}"
            )

        # Validate backing format
        valid_formats = {"qcow2", "raw"}
        if self.backing_format not in valid_formats:
            raise ValueError(
                f"Invalid backing_format '{self.backing_format}'. "
                f"Valid formats: {', '.join(sorted(valid_formats))}"
            )

        # Original backing_file path preserved unchanged for qemu-img portability
        # (Resolution above was only for validation)

    @classmethod
    def _get_qemu_img_path(cls) -> str:
        """
        Get cached qemu-img path with thread-safe initialization.

        Uses double-checked locking pattern for optimal performance:
        - Fast path: No lock needed if cache already populated (99% of calls)
        - Slow path: Acquire lock for initialization (1% of calls, first access only)

        Returns:
            Path to qemu-img binary

        Raises:
            StorageError: If qemu-img not found in PATH
        """
        # Fast path - no lock needed (optimization for common case)
        if FileBasedStorageDevice._qemu_img_path is not None:
            LOG.debug(f"CACHE HIT: {FileBasedStorageDevice._qemu_img_path}")
            return FileBasedStorageDevice._qemu_img_path

        # Slow path - acquire lock for initialization
        with FileBasedStorageDevice._qemu_img_lock:
            # Double-check after acquiring lock (another thread may have initialized)
            if FileBasedStorageDevice._qemu_img_path is None:
                LOG.debug("CACHE MISS: Looking up qemu-img binary")
                path = shutil.which("qemu-img")
                if not path:
                    raise StorageError(
                        "qemu-img binary not found in PATH. "
                        "Please install QEMU tools (qemu-utils or qemu-img package)."
                    )
                FileBasedStorageDevice._qemu_img_path = path
                LOG.debug(f"CACHE POPULATED: {path}")
            else:
                LOG.debug("CACHE HIT (after lock): Another thread initialized")

        return FileBasedStorageDevice._qemu_img_path

    def create_if_needed(self) -> None:
        """Create storage file if it doesn't exist and should be auto-created.

        After creation, persists the actual file path to config to ensure
        subsequent operations (like offline snapshots) use the correct path.
        """
        if not self.file_path.exists() and self._should_auto_create():
            self._create_storage_file()
            # Persist actual path to config so subsequent operations use correct path
            # This is critical for offline snapshots after VM stop
            self.config["file"] = str(self.file_path)

    def _should_auto_create(self) -> bool:
        """Determine if we should auto-create this storage file."""
        try:
            # Resolve to absolute path for comparison
            resolved_path = self.file_path.resolve()

            # Check if path is in safe subdirectory allowlist (e.g., /dev/shm)
            is_in_safe_subdir = False
            for safe_path in SecurityPaths.SAFE_SUBDIRECTORIES:
                try:
                    if resolved_path.is_relative_to(safe_path.resolve()):
                        is_in_safe_subdir = True
                        break
                except (ValueError, RuntimeError):
                    continue

            # Don't auto-create in system directories (unless in safe subdirectory)
            if not is_in_safe_subdir:
                for sys_path in SecurityPaths.DANGEROUS_SYSTEM_PATHS:
                    try:
                        if resolved_path.is_relative_to(sys_path.resolve()):
                            return False
                    except (ValueError, RuntimeError):
                        # is_relative_to can raise ValueError if paths are on different drives
                        # or RuntimeError for resolution issues - skip this check
                        continue

            # Check if we can write to parent directory
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                return True
            except PermissionError:
                return False

        except Exception:
            return False

    def _create_storage_file(self) -> None:
        """Create storage file with TOCTOU protection using file descriptors.

        Uses POSIX file descriptor-based operations to eliminate race conditions:
        - O_DIRECTORY ensures parent is directory, not symlink to file
        - O_NOFOLLOW prevents following symlinks during creation
        - dir_fd parameter makes all operations relative to parent FD
        - Post-creation verification confirms file is regular (not symlink)

        This prevents attackers from replacing directories with symlinks
        between validation and file creation (Time-of-Check-Time-of-Use attack).
        """
        lock_file = None
        parent_fd = None

        try:
            # Get cached qemu-img binary path (no subprocess call)
            qemu_img_path = self._get_qemu_img_path()

            # Step 1: Open parent directory to get stable file descriptor
            parent = self.file_path.parent
            try:
                # O_DIRECTORY ensures this is a directory (not symlink to file)
                parent_fd = os.open(str(parent), os.O_DIRECTORY | os.O_RDONLY)
            except FileNotFoundError:
                parent.mkdir(parents=True, exist_ok=True)
                parent_fd = os.open(str(parent), os.O_DIRECTORY | os.O_RDONLY)
            except NotADirectoryError:
                raise StorageError(f"Parent path is not a directory: {parent}")

            # All subsequent operations relative to parent_fd (no path traversal)

            # Step 2: Disk space check using FD (skip for backed images - they start small)
            if not self.backing_file and self.size:
                stat_result = os.statvfs(parent_fd)
                available_bytes = stat_result.f_bavail * stat_result.f_frsize
                required_bytes = self._parse_size_to_bytes(self.size)
                if self.get_type().lower() == "qcow2":
                    required_bytes = int(required_bytes * 1.1)
                if required_bytes > available_bytes:
                    raise StorageError(
                        f"Insufficient disk space: need {self._format_bytes(required_bytes)}, "
                        f"have {self._format_bytes(available_bytes)}"
                    )

            # Step 3: Create lock file using openat() (relative to parent_fd)
            lock_filename = f".{self.file_path.name}.lock"
            try:
                lock_fd = os.open(
                    lock_filename,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                    dir_fd=parent_fd,
                    mode=0o600
                )
                lock_file = os.fdopen(lock_fd, 'w')
            except FileExistsError:
                # Lock exists - acquire it
                lock_fd = os.open(lock_filename, os.O_WRONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
                lock_file = os.fdopen(lock_fd, 'w')

            # Step 4: Acquire exclusive lock
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise StorageError(
                    f"Storage file {self.file_path} is being created by another process"
                )

            # Step 5: Check if file exists using fstatat (follows symlinks = False)
            try:
                os.stat(self.file_path.name, dir_fd=parent_fd, follow_symlinks=False)
                LOG.warning(f"Storage file {self.file_path} already exists")
                return
            except FileNotFoundError:
                pass  # Good - doesn't exist

            # Step 6: Create empty file atomically with O_NOFOLLOW
            try:
                fd = os.open(
                    self.file_path.name,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                    dir_fd=parent_fd,
                    mode=0o600
                )
                os.close(fd)
            except FileExistsError:
                LOG.warning(f"File created by another process: {self.file_path}")
                return

            # Step 7: Now safe to run qemu-img (file exists, is owned by us, not a symlink)
            if self.backing_file:
                LOG.info(
                    f"Creating {self.get_type()} storage with backing file: "
                    f"{self.file_path} (backing: {self.backing_file})"
                )
            else:
                LOG.info(f"Creating {self.get_type()} storage: {self.file_path} ({self.size})")

            cmd = [
                qemu_img_path,
                "create",
                "-f", self.get_type().lower(),
            ]

            # Add backing file parameters if specified
            if self.backing_file:
                cmd.extend(["-b", self.backing_file, "-F", self.backing_format])

            # Explicit end of options
            cmd.append("--")
            # Output file path
            cmd.append(str(self.file_path.resolve()))

            # Size only required when not using backing file (inherited otherwise)
            if not self.backing_file and self.size:
                cmd.append(self.size)

            result = run_with_output_limit(
                cmd, capture_output=True, text=True, check=True,
                timeout=30, cwd="/tmp"  # Run in safe directory
            )

            # Step 8: Verify created file is regular (not symlink)
            stat_result = os.stat(
                self.file_path.name,
                dir_fd=parent_fd,
                follow_symlinks=False
            )
            if not stat.S_ISREG(stat_result.st_mode):
                raise StorageError(
                    f"Created file {self.file_path} is not regular. Possible symlink attack."
                )

            LOG.info(f"Successfully created storage file: {self.file_path}")

        except subprocess.CalledProcessError as e:
            LOG.error(f"Failed to create storage file {self.file_path}: {e.stderr}")
            # Clean up partial file
            if self.file_path.exists():
                try:
                    if parent_fd is not None:
                        os.unlink(self.file_path.name, dir_fd=parent_fd)
                    else:
                        self.file_path.unlink()
                except Exception:
                    pass
            raise StorageError(f"Failed to create storage file: {e.stderr}")

        finally:
            # Release lock (before closing parent_fd)
            if lock_file:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    if parent_fd is not None:
                        os.unlink(lock_filename, dir_fd=parent_fd)
                except Exception as e:
                    LOG.debug(f"Error cleaning lock: {e}")

            # Close parent FD
            if parent_fd is not None:
                try:
                    os.close(parent_fd)
                except Exception as e:
                    LOG.debug(f"Error closing parent FD: {e}")

    def _parse_size_to_bytes(self, size_str: str) -> int:
        """
        Parse size string (e.g., '10G', '512M') to bytes.

        Delegates to InputValidator for parsing logic.
        """
        try:
            return InputValidator.parse_size(size_str)
        except ValidationError as e:
            raise ValueError(str(e))

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"

    def get_qemu_args(self) -> List[str]:
        """Get QEMU arguments for file-based storage."""
        drive_spec = (
            f"file={self.file_path},if={self.interface},"
            f"format={self.get_type().lower()}"
        )
        return ["-drive", drive_spec]

    def get_info(self) -> Dict[str, Any]:
        """Get detailed information about file-based storage."""
        info = super().get_info()
        info.update(
            {
                "file_path": str(self.file_path),
                "size": self.size,
                "interface": self.interface,
                "exists": self.file_path.exists(),
            }
        )
        if self.backing_file:
            info["backing_file"] = self.backing_file
            info["backing_format"] = self.backing_format
        return info


class QCOW2StorageDevice(FileBasedStorageDevice):
    """QCOW2 storage device with snapshot support."""

    def get_type(self) -> str:
        """Get storage type."""
        return "qcow2"

    def supports_snapshots(self) -> bool:
        """QCOW2 supports snapshots."""
        return True

    @staticmethod
    def __default_options():
        return {
            'security_model': 'none',
            'writeout': 'immediate',
        }


class RawStorageDevice(FileBasedStorageDevice):
    """Raw storage device without snapshot support."""

    def get_type(self) -> str:
        """Get storage type."""
        return "raw"

    def supports_snapshots(self) -> bool:
        """Raw storage does not support snapshots."""
        return False


class VirtFSStorageDevice(BaseStorageDevice):
    """VirtFS (9p) storage device for folder sharing."""

    VALID_SECURITY_MODELS = {
        "passthrough",
        "mapped-xattr",
        "mapped-file",
        "none",
    }

    def __init__(self, config: Dict[str, Any], vm_id: str, index: int):
        """Initialize VirtFS storage device."""
        super().__init__(config, vm_id, index)

        self.share_path = config.get("path", "./share")
        self.options = config.get("options", {})
        self.mount_tag = self.options.get("mount_tag", self.name)
        self.fs_id = self.options.get("id", self.name)
        self.readonly = self.options.get("readonly", False)

        # Validate configuration
        self._validate_security_model()
        self._validate_share_path()

    def get_type(self) -> str:
        """Get storage type."""
        return "virtfs"

    def supports_snapshots(self) -> bool:
        """VirtFS does not support snapshots."""
        return False

    def _validate_security_model(self) -> None:
        """Validate security_model is one of the supported values."""
        security_model = self.options.get("security_model", "passthrough")
        if security_model not in self.VALID_SECURITY_MODELS:
            raise ValueError(
                f"Invalid security_model '{security_model}'. "
                f"Valid models: {', '.join(sorted(self.VALID_SECURITY_MODELS))}"
            )

    def _validate_share_path(self) -> None:
        """Validate share_path exists, is accessible, and is safe to share."""
        share_path = Path(self.share_path)

        # Check if path exists - warn if it doesn't (will be created later)
        if not share_path.exists():
            LOG.warning(
                f"VirtFS share path does not exist: {share_path}. "
                "It will be created when VM starts."
            )
            return

        # Delegate to InputValidator for all standard validation
        try:
            share_path = InputValidator.validate_share_path(
                share_path,
                description="VirtFS share path"
            )
        except ValidationError as e:
            raise ValueError(str(e))

        # VirtFS-specific: Check permissions
        if not os.access(share_path, os.R_OK):
            raise ValueError(
                f"VirtFS share path is not readable: {share_path}"
            )

        if not self.readonly and not os.access(share_path, os.W_OK):
            raise ValueError(
                f"VirtFS share path is not writable: {share_path}. "
                "Set readonly=true in options if read-only access is intended."
            )

    def create_if_needed(self) -> None:
        """Ensure share directory exists."""
        share_dir = Path(self.share_path)
        try:
            share_dir.mkdir(parents=True, exist_ok=True)
            LOG.debug(f"VirtFS share directory ready: {share_dir}")
        except Exception as e:
            LOG.warning(f"Could not create VirtFS directory {share_dir}: {e}")

    def get_qemu_args(self) -> List[str]:
        """Get QEMU arguments for VirtFS."""
        security_model = self.options.get("security_model", "passthrough")

        # Build VirtFS arguments starting with required fields
        virtfs_args = (
            f"local,path={self.share_path},mount_tag={self.mount_tag},"
            f"security_model={security_model},id={self.fs_id}"
        )

        # Add readonly if specified
        if self.readonly:
            virtfs_args += ",readonly=on"

        # Add any additional options from config
        for key, value in self.options.items():
            if key not in ["mount_tag", "id", "security_model", "readonly"]:
                virtfs_args += f",{key}={value}"

        return ["-virtfs", virtfs_args]

    def get_info(self) -> Dict[str, Any]:
        """Get VirtFS information."""
        info = super().get_info()
        info.update(
            {
                "share_path": self.share_path,
                "mount_tag": self.mount_tag,
                "fs_id": self.fs_id,
                "exists": Path(self.share_path).exists(),
            }
        )
        return info


def validate_storage_config(storage_configs: List[Dict[str, Any]]) -> None:
    """
    Validate storage configuration without creating device objects.

    This allows early validation during config parsing to fail fast
    with clear errors before VM creation. Called from ConfigParser.

    Args:
        storage_configs: List of storage configuration dictionaries

    Raises:
        ConfigValidationError: If storage configuration is invalid
    """
    if not isinstance(storage_configs, list):
        raise ConfigValidationError("Storage configuration must be a list")

    # Track device names to detect duplicates
    seen_names = set()

    for index, config in enumerate(storage_configs):
        if not isinstance(config, dict):
            raise ConfigValidationError(f"Storage {index}: Configuration must be a dictionary")

        storage_type = config.get("type", "qcow2").lower()

        # Check for duplicate names
        storage_name = config.get("name", f"storage{index}")
        if storage_name in seen_names:
            raise ConfigValidationError(
                f"Storage {index}: Duplicate storage name '{storage_name}'. "
                f"Each storage device must have a unique name."
            )
        seen_names.add(storage_name)

        # Validate storage type
        supported_types = ["qcow2", "raw", "virtfs"]
        if storage_type not in supported_types:
            raise ConfigValidationError(
                f"Storage {index}: Unknown type '{storage_type}'. "
                f"Supported types: {', '.join(supported_types)}"
            )

        # Validate type-specific config
        if storage_type in ("qcow2", "raw"):
            # Validate size format (if provided) - delegate to InputValidator
            if "size" in config:
                try:
                    InputValidator.parse_size(str(config["size"]))
                except ValidationError as e:
                    raise ConfigValidationError(f"Storage {index}: {e}")

            # Validate interface (if provided) - use class constant
            if "interface" in config:
                interface = config["interface"]
                if interface not in FileBasedStorageDevice.VALID_INTERFACES:
                    raise ConfigValidationError(
                        f"Storage {index}: Invalid interface '{interface}'. "
                        f"Valid interfaces: {', '.join(sorted(FileBasedStorageDevice.VALID_INTERFACES))}"
                    )

        elif storage_type == "virtfs":
            # Validate security model (if provided) - use class constant
            options = config.get("options", {})
            if "security_model" in options:
                security_model = options["security_model"]
                if security_model not in VirtFSStorageDevice.VALID_SECURITY_MODELS:
                    raise ConfigValidationError(
                        f"Storage {index}: Invalid security_model '{security_model}'. "
                        f"Valid models: {', '.join(sorted(VirtFSStorageDevice.VALID_SECURITY_MODELS))}"
                    )

            # Validate path is provided
            if "path" not in config:
                raise ConfigValidationError(
                    f"Storage {index}: VirtFS storage requires 'path' field"
                )


class StorageManager:
    """
    Manages VM storage devices with extensible type system.

    Provides unified interface for different storage types and integrates
    with snapshot functionality.

    # NOTE: Good - plugin architecture with device type registry allows easy
    #       addition of new storage types without modifying existing code.
    #       Just implement BaseStorageDevice and register.
    # NOTE: Storage validation happens both at config parse time
    # (validate_storage_config)
    # and at device creation time (device __init__). Early validation provides
    # clear errors before VM creation. Device validation includes runtime
    # checks
    #       like path resolution and disk space.
    """

    # Registry of storage device types
    _device_types: Dict[str, Type[BaseStorageDevice]] = {
        "qcow2": QCOW2StorageDevice,
        "raw": RawStorageDevice,
        "virtfs": VirtFSStorageDevice,
    }

    def __init__(self, vm_id: str):
        """
        Initialize storage manager for a VM.

        Args:
            vm_id: VM identifier
        """
        self.vm_id = vm_id
        self.devices: List[BaseStorageDevice] = []

    @classmethod
    def register_device_type(
        cls, type_name: str, device_class: Type[BaseStorageDevice]
    ):
        """
        Register a new storage device type.

        Args:
            type_name: Storage type name (e.g., 'nvme', 'scsi')
            device_class: Storage device class
        """
        cls._device_types[type_name.lower()] = device_class
        LOG.debug(f"Registered storage device type: {type_name}")

    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported storage types."""
        return list(cls._device_types.keys())

    def add_storage_from_config(self, storage_configs: List[Dict[str, Any]]):
        """
        Add storage devices from configuration list.

        Args:
            storage_configs: List of storage configuration dictionaries
        """
        for index, config in enumerate(storage_configs):
            storage_type = config.get("type", "qcow2").lower()

            if storage_type not in self._device_types:
                LOG.warning(
                    f"Unknown storage type '{storage_type}', "
                    f"defaulting to qcow2. Supported types: "
                    f"{', '.join(self.get_supported_types())}"
                )
                storage_type = "qcow2"

            device_class = self._device_types[storage_type]
            device = device_class(config, self.vm_id, index)
            self.devices.append(device)

    def create_storage_files(self):
        """Create storage files for all devices that need them."""
        for device in self.devices:
            try:
                device.create_if_needed()
            except StorageError as e:
                LOG.error(f"Failed to create storage for {device.name}: {e}")
                raise

    def get_qemu_args(self) -> List[List[str]]:
        """
        Get all QEMU arguments for storage devices.

        Returns:
            List of QEMU argument lists (each device returns a list of args)
        """
        args = []
        for device in self.devices:
            args.append(device.get_qemu_args())
        return args

    def get_device_by_name(self, name: str) -> Optional[BaseStorageDevice]:
        """
        Get storage device by name.

        Args:
            name: Device name

        Returns:
            Storage device or None if not found
        """
        for device in self.devices:
            if device.name == name:
                return device
        return None

    def get_snapshot_capable_devices(self) -> List[BaseStorageDevice]:
        """Get list of devices that support snapshots."""
        return [
            device for device in self.devices if device.supports_snapshots()
        ]

    def get_file_based_devices(self) -> List["FileBasedStorageDevice"]:
        """
        Get list of file-based storage devices (QCOW2, Raw).

        Returns file-based storage devices that have actual disk image files
        on the filesystem. Excludes non-file storage like VirtFS.

        Returns:
            List of FileBasedStorageDevice instances
        """
        return [
            device for device in self.devices
            if isinstance(device, FileBasedStorageDevice)
        ]

    def get_storage_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all storage devices.

        Returns:
            List of device information dictionaries
        """
        return [device.get_info() for device in self.devices]

    def get_storage_configs(self) -> List[Dict[str, Any]]:
        """
        Get current storage device configurations.

        Returns the configs with any runtime updates (e.g., auto-generated file paths
        that were persisted after creation). This is needed to ensure the database
        has the correct file paths for offline operations like snapshots.

        Returns:
            List of storage configuration dictionaries
        """
        return [device.config for device in self.devices]
