"""Path utilities for maqet.

Provides canonical path conversion and validation functions for consistent
path handling across the codebase, as well as XDG-compliant runtime path
resolution.
"""

import os
from pathlib import Path
from typing import Union


def ensure_path(path: Union[str, Path]) -> Path:
    """
    Convert path parameter to Path object if needed.

    This is the canonical boundary conversion for all API functions
    that accept Union[str, Path] parameters. Use this at the entry
    point of public API functions to normalize path types.

    Args:
        path: String path or Path object

    Returns:
        Path object (returns input unchanged if already Path)

    Raises:
        TypeError: If path is neither str nor Path

    Example:
        def load_config(config: Union[str, Path]) -> Dict:
            config = ensure_path(config)  # Normalize at boundary
            # ... rest uses Path operations

    Note:
        This function does NOT validate path existence or permissions.
        Use Path.exists(), Path.is_file(), etc. for validation.
    """
    if isinstance(path, Path):
        return path
    if isinstance(path, str):
        return Path(path)
    raise TypeError(
        f"Expected str or Path, got {type(path).__name__}. "
        f"Use ensure_path('path') or ensure_path(Path('path'))"
    )


def safe_resolve(path: Union[str, Path], strict: bool = False) -> Path:
    """
    Resolve path to absolute with exception handling.

    Handles edge cases like broken symlinks and permission errors
    by falling back to absolute path without symlink resolution.

    Args:
        path: Path to resolve
        strict: If True, raise FileNotFoundError for missing paths

    Returns:
        Resolved absolute Path

    Raises:
        FileNotFoundError: If strict=True and path doesn't exist
        RuntimeError: If path resolution fails (symlink loops, etc.)

    Example:
        # Safe for potentially broken symlinks
        resolved = safe_resolve(config_path)

        # Strict mode for validation
        try:
            resolved = safe_resolve(config_path, strict=True)
        except FileNotFoundError:
            print(f"Config not found: {config_path}")
    """
    path = ensure_path(path)

    try:
        return path.resolve(strict=strict)
    except (RuntimeError, OSError) as e:
        if strict:
            raise
        # Fallback: return absolute path without symlink resolution
        return path.absolute()


def get_socket_path(vm_id: str) -> Path:
    """
    Get Unix socket path for VM runner.

    Socket location: XDG_RUNTIME_DIR/maqet/sockets/{vm_id}.sock
    Falls back to /tmp/maqet-{uid}/sockets/ if XDG_RUNTIME_DIR not available.

    This is the single source of truth for socket path resolution.

    Args:
        vm_id: VM identifier

    Returns:
        Path to Unix socket

    Example:
        >>> get_socket_path("vm1")
        PosixPath('/run/user/1000/maqet/sockets/vm1.sock')
    """
    # Get runtime directory (prefer XDG_RUNTIME_DIR)
    runtime_dir_base = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")

    if not Path(runtime_dir_base).exists():
        # Fallback to /tmp (already includes maqet-{uid})
        socket_dir = Path(f"/tmp/maqet-{os.getuid()}") / "sockets"
    else:
        # XDG_RUNTIME_DIR exists (e.g., /run/user/1000)
        socket_dir = Path(runtime_dir_base) / "maqet" / "sockets"

    # Ensure socket directory exists
    socket_dir.mkdir(parents=True, exist_ok=True)

    return socket_dir / f"{vm_id}.sock"


def get_log_path(vm_id: str) -> Path:
    """
    Get log file path for VM runner.

    Log location: XDG_DATA_HOME/maqet/logs/vm_{vm_id}.log

    Args:
        vm_id: VM identifier

    Returns:
        Path to log file
    """
    xdg_data_home = os.environ.get(
        "XDG_DATA_HOME", str(Path.home() / ".local" / "share")
    )
    log_dir = Path(xdg_data_home) / "maqet" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    return log_dir / f"vm_{vm_id}.log"


def get_runner_error_path(vm_id: str) -> Path:
    """
    Get path to VM runner error file.

    Error files contain structured error information when runner fails.
    Separate from logs for easier parsing by parent process.

    Args:
        vm_id: VM identifier

    Returns:
        Path to error file
    """
    xdg_data_home = os.environ.get(
        "XDG_DATA_HOME", str(Path.home() / ".local" / "share")
    )
    log_dir = Path(xdg_data_home) / "maqet" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    return log_dir / f"vm_{vm_id}.error"


def get_runner_status_path(vm_id: str) -> Path:
    """
    Get path to VM runner status marker file.

    Status files mark successful startup completion.
    Format: READY:{runner_pid}:{qemu_pid}:{timestamp}

    Args:
        vm_id: VM identifier

    Returns:
        Path to status file
    """
    xdg_data_home = os.environ.get(
        "XDG_DATA_HOME", str(Path.home() / ".local" / "share")
    )
    status_dir = Path(xdg_data_home) / "maqet" / "status"
    status_dir.mkdir(parents=True, exist_ok=True)

    return status_dir / f"vm_{vm_id}.status"


def get_runtime_dir() -> Path:
    """
    Get maqet runtime directory.

    Returns:
        Path to runtime directory
    """
    runtime_dir_base = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")

    if not Path(runtime_dir_base).exists():
        return Path(f"/tmp/maqet-{os.getuid()}")

    return Path(runtime_dir_base) / "maqet"
