"""
Security utilities for maqet.

Provides secure file operations, secret management, and cryptographic functions.
"""

import os
import secrets
import stat
from pathlib import Path


def create_auth_secret_file(socket_path: Path) -> str:
    """
    Create authentication secret file with atomic secure permissions.

    This function atomically creates a secret file with mode 0600 (user-only access)
    and writes a cryptographically secure random token. The atomic creation prevents
    TOCTOU (Time-Of-Check-Time-Of-Use) vulnerabilities by ensuring:

    1. File creation and permission setting happen atomically (O_CREAT | O_EXCL)
    2. No symlink attacks possible (O_NOFOLLOW)
    3. No window where file exists with insecure permissions
    4. Verification after creation ensures permissions stuck

    Security Features:
    - O_CREAT | O_EXCL: Atomic creation, fails if file exists (prevents race)
    - O_NOFOLLOW: Prevents symlink attacks
    - mode=0o600: Permissions set atomically at creation (no vulnerability window)
    - Post-creation verification to ensure permissions are correct

    Args:
        socket_path: Path to Unix socket (secret file will be {socket_path}.auth)

    Returns:
        The generated authentication secret (hex string)

    Raises:
        RuntimeError: If secret file already exists
        AssertionError: If created file has incorrect permissions

    Example:
        >>> socket_path = Path("/run/user/1000/maqet/sockets/vm1.sock")
        >>> secret = create_auth_secret_file(socket_path)
        >>> # Secret file created at /run/user/1000/maqet/sockets/vm1.auth
        >>> # with mode 0600 and containing the secret token
    """
    secret_file = socket_path.with_suffix('.auth')
    auth_secret = secrets.token_hex(32)  # 256-bit secret

    # Remove stale auth file from crashed VM (if exists)
    # This handles the case where VM crashed without cleanup
    if secret_file.exists():
        try:
            secret_file.unlink()
        except OSError:
            # If we can't remove it, we'll fail on O_EXCL below anyway
            pass

    # Create file with atomic O_EXCL (fail if exists) and mode 0600
    # O_CREAT: Create file if it doesn't exist
    # O_EXCL: Fail if file already exists (atomic check-and-create)
    # O_WRONLY: Write-only access
    # O_NOFOLLOW: Don't follow symlinks (prevent symlink attacks)
    # mode=0o600: User read/write only, set atomically
    try:
        fd = os.open(
            str(secret_file),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
            mode=0o600
        )
    except FileExistsError:
        raise RuntimeError(f"Secret file already exists: {secret_file}")

    try:
        # Write secret to file descriptor
        os.write(fd, auth_secret.encode('utf-8'))
    finally:
        # Always close file descriptor, even if write fails
        os.close(fd)

    # Verify creation succeeded with correct permissions
    # This is a safety check to ensure the OS honored our mode setting
    stat_info = os.stat(str(secret_file))
    file_mode = stat.S_IMODE(stat_info.st_mode)
    expected_mode = 0o600

    assert file_mode == expected_mode, (
        f"Secret file has wrong permissions: got {oct(file_mode)}, "
        f"expected {oct(expected_mode)}"
    )

    return auth_secret
