"""
Runner Client

Client for communicating with VM runner processes via Unix sockets.
Used by CLI to send commands to running VM runner processes.

Architecture:
- Each VM has unique socket path
- Client connects, sends request, receives response, disconnects
- Synchronous and async interfaces
- Error handling for connection issues
- Challenge-response authentication for security
"""

import asyncio
import errno
import hashlib
import hmac
import json
import os
import stat
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..constants import Intervals, Retries, Timeouts
from ..exceptions import IPCError, SecurityError
from ..logger import LOG
from ..utils.paths import get_socket_path
from .retry import async_retry_with_backoff, CircuitBreaker

# Optional dependency - imported inline with fallback
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class RunnerClientError(IPCError):
    """Runner client communication errors."""


class RunnerClient:
    """
    Client for communicating with a VM runner process.

    Used by CLI to send commands to running VM runners via Unix sockets.
    Provides both synchronous and asynchronous interfaces.

    Example:
        client = RunnerClient("vm1", state_manager)
        result = client.send_command("qmp", "query-status")
    """

    # Class-level cache for authentication secrets
    # Key: vm_id, Value: (secret, cached_timestamp, file_mtime)
    _auth_cache: Dict[str, Tuple[str, float, float]] = {}
    AUTH_CACHE_TTL = 300  # 5 minutes

    def _read_auth_secret_secure(self, secret_file: Path) -> str:
        """
        Read authentication secret with TOCTOU protection.

        Uses file descriptor-based atomic operations to prevent race conditions
        between security checks and file reading. Opens file with O_NOFOLLOW to
        prevent symlink attacks, then validates all security properties on the
        opened file descriptor.

        Args:
            secret_file: Path to authentication secret file

        Returns:
            Authentication secret string (64 hex chars)

        Raises:
            RunnerClientError: If file not found or format invalid
            SecurityError: If security checks fail
        """
        try:
            # Open file descriptor with symlink protection
            fd = os.open(str(secret_file), os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            raise RunnerClientError(
                f"VM runner not started or secret missing. "
                f"Expected secret file: {secret_file}"
            )
        except OSError as e:
            if e.errno == errno.ELOOP:
                raise SecurityError(f"Secret file is a symlink: {secret_file}")
            raise RunnerClientError(f"Cannot open secret file: {e}")

        try:
            # Verify file attributes on OPENED fd (not filename)
            stat_info = os.fstat(fd)
            file_mode = stat.S_IMODE(stat_info.st_mode)

            # Check 1: Permissions must be 0600 (user-only read/write)
            if file_mode != 0o600:
                raise SecurityError(
                    f"Insecure secret file permissions: {oct(file_mode)}. "
                    f"Expected 0600 (user-only). File: {secret_file}"
                )

            # Check 2: Must be regular file (not device, socket, etc.)
            if not stat.S_ISREG(stat_info.st_mode):
                raise SecurityError(
                    f"Secret file is not a regular file: {secret_file}"
                )

            # Check 3: Must be owned by current user (prevent privilege escalation)
            current_uid = os.getuid()
            if stat_info.st_uid != current_uid:
                raise SecurityError(
                    f"Secret file owned by different user. "
                    f"Expected UID {current_uid}, got {stat_info.st_uid}. "
                    f"File: {secret_file}"
                )

            # Check 4: File size sanity check (256-bit secret = 64 hex chars)
            if stat_info.st_size > 1024:  # Max 1KB
                raise SecurityError(
                    f"Secret file too large: {stat_info.st_size} bytes. "
                    f"Expected ~64 bytes. File: {secret_file}"
                )

            # Read secret from fd (no more TOCTOU - reading from verified fd)
            secret_bytes = os.read(fd, stat_info.st_size)
            secret = secret_bytes.decode('utf-8').strip()

            # Validate secret format
            if len(secret) != 64:
                raise RunnerClientError(
                    f"Invalid secret length: {len(secret)} "
                    f"(expected 64 hex chars)"
                )

            if not all(c in '0123456789abcdef' for c in secret):
                raise RunnerClientError(
                    "Invalid secret format (not lowercase hex)"
                )

            return secret

        finally:
            # Always close fd
            os.close(fd)

    def _get_cached_auth_secret(self) -> str:
        """Get authentication secret with caching.

        Returns cached secret if still valid (within TTL and file unchanged),
        otherwise reads from file and updates cache.

        Cache validation checks both TTL and file mtime to ensure
        cached secrets are invalidated when the auth file changes.

        Returns:
            Authentication secret string

        Raises:
            RunnerClientError: If secret file not found or invalid
            SecurityError: If security checks fail
        """
        now = time.time()
        secret_file = self.socket_path.with_suffix('.auth')

        # Get current file mtime for cache validation
        try:
            current_mtime = secret_file.stat().st_mtime
        except FileNotFoundError:
            # File doesn't exist, invalidate cache and let read fail with proper error
            self.invalidate_cache(self.vm_id)
            return self._read_auth_secret_secure(secret_file)

        # Check cache with mtime validation
        if self.vm_id in RunnerClient._auth_cache:
            secret, cached_at, cached_mtime = RunnerClient._auth_cache[self.vm_id]
            if now - cached_at < self.AUTH_CACHE_TTL and cached_mtime == current_mtime:
                LOG.debug(f"Using cached auth secret for {self.vm_id}")
                return secret

        # Cache miss, expired, or file changed - read from file
        secret = self._read_auth_secret_secure(secret_file)

        # Update cache with current mtime
        RunnerClient._auth_cache[self.vm_id] = (secret, now, current_mtime)
        LOG.debug(f"Cached auth secret for {self.vm_id}")

        return secret

    @classmethod
    def invalidate_cache(cls, vm_id: Optional[str] = None) -> None:
        """Invalidate auth secret cache.

        Args:
            vm_id: Specific VM to invalidate. If None, clears entire cache.
        """
        if vm_id is None:
            cls._auth_cache.clear()
            LOG.debug("Cleared all auth secret cache entries")
        elif vm_id in cls._auth_cache:
            del cls._auth_cache[vm_id]
            LOG.debug(f"Invalidated auth secret cache for {vm_id}")

    def __init__(self, vm_id: str, state_manager):
        """
        Initialize runner client.

        Args:
            vm_id: VM identifier
            state_manager: StateManager instance for DB access
        """
        self.vm_id = vm_id
        self.state_manager = state_manager
        self.socket_path = get_socket_path(vm_id)
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5, timeout=60.0
        )

        # Check VM exists
        vm = state_manager.get_vm(vm_id)
        if not vm:
            raise RunnerClientError(f"VM {vm_id} not found")

        # Read auth_secret from ephemeral file with caching
        self.auth_secret = self._get_cached_auth_secret()

        LOG.debug(f"RunnerClient initialized for {vm_id}")

    def is_runner_running(self) -> bool:
        """
        Check if VM runner process is running.

        Uses psutil if available for accurate check, otherwise
        falls back to checking if socket exists.

        Returns:
            True if runner is running, False otherwise
        """
        # Get VM from database
        vm = self.state_manager.get_vm(self.vm_id)
        if not vm or not vm.runner_pid:
            return False

        # Check if process exists (if psutil available)
        if PSUTIL_AVAILABLE:
            return psutil.pid_exists(vm.runner_pid)
        else:
            # Fallback: check if socket exists
            return self.socket_path.exists()

    @async_retry_with_backoff(
        max_attempts=Retries.IPC_MAX_RETRIES,
        backoff_base=Intervals.IPC_BACKOFF_BASE,
        exceptions=(ConnectionRefusedError, FileNotFoundError, OSError),
    )
    async def _connect_to_socket(self):
        """
        Connect to Unix socket with retry logic.

        Internal method that handles connection with automatic retry
        on transient failures.

        Returns:
            Tuple of (reader, writer) for socket communication

        Raises:
            ConnectionRefusedError: If connection refused
            FileNotFoundError: If socket doesn't exist
            OSError: On other connection errors
        """
        return await asyncio.wait_for(
            asyncio.open_unix_connection(str(self.socket_path)),
            timeout=Timeouts.IPC_CONNECT,
        )

    async def _authenticate(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Perform challenge-response authentication with server.

        Protocol:
        1. Server sends challenge: {"type": "challenge", "value": "<random-hex>"}
        2. Client computes HMAC-SHA256(auth_secret, challenge)
        3. Client sends: {"auth": "<hmac-hex>"}
        4. Server verifies and proceeds (or closes connection on failure)

        Args:
            reader: Async stream reader
            writer: Async stream writer

        Raises:
            RunnerClientError: If authentication fails
        """
        try:
            # Step 1: Receive challenge from server with newline framing (consistent protocol)
            try:
                challenge_data = await asyncio.wait_for(
                    reader.readuntil(b'\n'), timeout=Timeouts.IPC_AUTH
                )
            except asyncio.LimitOverrunError:
                raise RunnerClientError("Challenge message too long or missing delimiter")

            if not challenge_data:
                raise RunnerClientError("Empty challenge from server")

            # Parse challenge
            try:
                challenge = json.loads(challenge_data.decode("utf-8").strip())
            except json.JSONDecodeError as e:
                raise RunnerClientError(f"Invalid challenge JSON: {e}")

            if challenge.get("type") != "challenge":
                raise RunnerClientError("Expected challenge from server")

            challenge_value = challenge.get("value")
            if not challenge_value:
                raise RunnerClientError("Challenge missing value")

            LOG.debug("Received authentication challenge")

            # Step 2: Compute HMAC response
            response_hmac = hmac.new(
                self.auth_secret.encode("utf-8"),
                challenge_value.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            # Step 3: Send authentication response with newline delimiter
            # Newline ensures server can properly frame the message
            auth_response = json.dumps({"auth": response_hmac}) + "\n"
            writer.write(auth_response.encode("utf-8"))
            await writer.drain()

            LOG.debug("Sent authentication response")

        except asyncio.TimeoutError:
            raise RunnerClientError("Authentication timeout")
        except RunnerClientError:
            raise
        except Exception as e:
            raise RunnerClientError(f"Authentication error: {e}")

    async def send_command_async(
        self, method: str, *args, **kwargs
    ) -> Dict[str, Any]:
        """
        Send command to VM runner asynchronously with authentication.

        Args:
            method: Method name (e.g., "qmp", "stop", "status", "ping")
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            Result dictionary from runner

        Raises:
            RunnerClientError: If runner not running or communication fails
        """
        # Check circuit breaker
        if self._circuit_breaker.is_open():
            raise RunnerClientError(
                f"Circuit breaker open for {self.vm_id}. "
                f"Too many consecutive failures. Try again later."
            )

        # Check runner running
        if not self.is_runner_running():
            raise RunnerClientError(
                f"VM runner for {self.vm_id} is not running. "
                f"Start VM first with: maqet start {self.vm_id}"
            )

        # Check socket exists
        if not self.socket_path.exists():
            raise RunnerClientError(
                f"Socket not found: {self.socket_path}. "
                f"VM runner may have crashed."
            )

        # Build request
        request = {"method": method, "args": list(args), "kwargs": kwargs}

        LOG.debug(f"Sending IPC request: method={method}")

        try:
            # Connect to Unix socket with retry logic
            reader, writer = await self._connect_to_socket()

            try:
                # Step 1: Perform authentication handshake
                await self._authenticate(reader, writer)

                # Step 2: Send request with newline framing (consistent protocol)
                request_data = (json.dumps(request) + "\n").encode("utf-8")
                writer.write(request_data)
                await writer.drain()

                # Step 3: Receive response with newline framing (consistent protocol)
                try:
                    response_data = await asyncio.wait_for(
                        reader.readuntil(b'\n'), timeout=Timeouts.IPC_COMMAND
                    )
                except asyncio.LimitOverrunError:
                    raise RunnerClientError("Response too large or missing newline delimiter")

                if not response_data:
                    raise RunnerClientError("Empty response from runner")

                # Parse response
                try:
                    response = json.loads(response_data.decode("utf-8").strip())
                except json.JSONDecodeError as e:
                    raise RunnerClientError(f"Invalid JSON response: {e}")

                # Check response status
                if response.get("status") == "error":
                    raise RunnerClientError(response.get("error", "Unknown error"))

                LOG.debug(f"IPC response received: status={response.get('status')}")

                # Record success for circuit breaker
                self._circuit_breaker.record_success()

                return response.get("result", {})

            finally:
                # Always close connection
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception as e:
                    LOG.debug(f"Error closing connection: {e}")

        except ConnectionRefusedError as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(
                f"Connection refused. VM runner for {self.vm_id} "
                f"may have crashed or stopped. Error: {e}"
            )
        except FileNotFoundError as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(
                f"Socket not found: {self.socket_path}. "
                f"VM runner may have exited. Error: {e}"
            )
        except asyncio.TimeoutError as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(
                f"IPC operation timed out for {self.vm_id}. "
                f"Runner may be unresponsive. Error: {e}"
            )
        except OSError as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(f"Communication error: {e}")
        except RunnerClientError:
            # Already a RunnerClientError, don't wrap again
            self._circuit_breaker.record_failure()
            raise
        except Exception as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(f"Unexpected error: {e}")

    def send_command(self, method: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Send command to VM runner synchronously.

        Convenience wrapper around send_command_async() for synchronous usage.

        Args:
            method: Method name (e.g., "qmp", "stop", "status", "ping")
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            Result dictionary from runner

        Raises:
            RunnerClientError: If runner not running or communication fails
        """
        return asyncio.run(self.send_command_async(method, *args, **kwargs))

    def ping(self) -> bool:
        """
        Ping VM runner to check if it's responsive.

        Returns:
            True if runner responds to ping, False otherwise
        """
        try:
            result = self.send_command("ping")
            return result == "pong"
        except RunnerClientError:
            return False

    def status(self) -> dict:
        """
        Get VM runner status including QEMU PID.

        Queries the VM runner for comprehensive status information
        including process IDs, uptime, and running state.

        Returns:
            dict: Status information with keys:
                - runner_pid: VM runner process ID
                - qemu_pid: QEMU process ID (or None if not running)
                - vm_id: VM identifier
                - uptime: Seconds since runner started
                - running: Whether QEMU is currently running
                - socket_path: Unix socket path for IPC

        Raises:
            RunnerClientError: If runner not running or communication fails
        """
        return self.send_command("status")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"RunnerClient(vm_id={self.vm_id}, socket={self.socket_path})"
