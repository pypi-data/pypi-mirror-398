"""
Unix Socket IPC Server

Simple Unix domain socket server for IPC between CLI and VM runner.
Uses JSON-RPC style protocol for request/response communication.

Architecture:
- Each VM runner process has its own Unix socket
- Non-blocking async I/O using asyncio
- Simple request/response pattern
- Socket cleanup on server stop
- Challenge-response authentication for security
"""

import asyncio
import hashlib
import hmac
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ..constants import Timeouts
from ..logger import LOG


class UnixSocketIPCServerError(Exception):
    """Unix socket IPC server errors."""


class UnixSocketIPCServer:
    """
    Unix domain socket server for IPC between CLI and VM runner.

    Protocol: JSON-RPC style
    - Client sends: {"method": "qmp", "args": [...], "kwargs": {...}}
    - Server responds: {"status": "success", "result": ...} or
                       {"status": "error", "error": "..."}

    Socket lifecycle:
    1. Server starts, binds to socket path
    2. Accepts connections from CLI clients
    3. Reads JSON request, calls handler
    4. Writes JSON response
    5. Closes connection
    """

    def __init__(
        self,
        socket_path: Path,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        auth_secret: Optional[str] = None
    ):
        """
        Initialize Unix socket server with authentication support.

        Args:
            socket_path: Path to Unix socket file
            handler: Async function to handle requests
                     Takes request dict, returns response dict
            auth_secret: Optional authentication secret for challenge-response
        """
        self.socket_path = Path(socket_path)
        self.handler = handler
        self.auth_secret = auth_secret
        self.server: Optional[asyncio.Server] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        LOG.debug(f"UnixSocketIPCServer initialized for {socket_path}")

    async def start(self) -> None:
        """
        Start listening on Unix socket with secure permissions.

        Process:
        1. Remove existing socket if present (stale socket handling)
        2. Set restrictive umask before socket creation
        3. Create Unix socket server
        4. Verify socket permissions are secure (0600)
        5. Start accepting connections
        6. Keep server running until stop() called

        Security:
        - Socket created with 0600 permissions (user-only access)
        - Prevents local privilege escalation (CVSS 7.8)
        - Original umask restored after socket creation

        Raises:
            UnixSocketIPCServerError: If socket already in use or bind fails
        """
        # Store event loop for cross-thread communication
        self._loop = asyncio.get_running_loop()

        # Remove existing socket if present
        if self.socket_path.exists():
            # Try to connect to check if someone is using it
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_unix_connection(str(self.socket_path)),
                    timeout=Timeouts.IPC_HEALTH_CHECK,
                )
                writer.close()
                await writer.wait_closed()
                # Someone is using it
                raise UnixSocketIPCServerError(
                    f"Socket already in use: {self.socket_path}"
                )
            except (ConnectionRefusedError, FileNotFoundError, asyncio.TimeoutError):
                # Stale socket, remove it
                LOG.debug(f"Removing stale socket {self.socket_path}")
                self.socket_path.unlink()

        # Set restrictive umask before socket creation
        # This ensures only the owner can access the socket
        old_umask = os.umask(0o077)

        try:
            # Create Unix socket server
            self.server = await asyncio.start_unix_server(
                self._handle_client, path=str(self.socket_path)
            )
            self._running = True

            # Verify socket has correct permissions (0600 for socket files)
            socket_stat = self.socket_path.stat()
            expected_mode = stat.S_IRUSR | stat.S_IWUSR  # 0o600
            actual_mode = stat.S_IMODE(socket_stat.st_mode)

            if actual_mode != expected_mode:
                LOG.warning(
                    f"Socket permissions {oct(actual_mode)} differ from "
                    f"expected {oct(expected_mode)}. Attempting to fix."
                )
                os.chmod(self.socket_path, expected_mode)

            LOG.info(
                f"IPC server listening on {self.socket_path} (mode: 0600)"
            )

            # Keep server running
            async with self.server:
                await self.server.serve_forever()

        except asyncio.CancelledError:
            # Server was stopped via stop() - this is normal
            LOG.debug("IPC server cancelled (normal shutdown)")
        except Exception as e:
            raise UnixSocketIPCServerError(f"Failed to start IPC server: {e}")
        finally:
            # Restore original umask
            os.umask(old_umask)

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Handle single client connection with authentication.

        Process:
        1. (If auth enabled) Perform challenge-response authentication
        2. Read JSON request from client
        3. Parse and validate request
        4. Call handler function
        5. Write JSON response to client
        6. Close connection

        Args:
            reader: Async stream reader
            writer: Async stream writer
        """
        try:
            # Step 1: Authentication (if enabled)
            if self.auth_secret:
                if not await self._authenticate_client(reader, writer):
                    LOG.warning("Client authentication failed")
                    return

            # Step 2: Read request with newline framing (consistent with auth)
            try:
                data = await asyncio.wait_for(
                    reader.readuntil(b'\n'), timeout=Timeouts.IPC_COMMAND
                )
            except asyncio.LimitOverrunError:
                LOG.warning("Request message too long or missing newline delimiter")
                response = {"status": "error", "error": "Request too large or malformed"}
                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()
                return
            except asyncio.TimeoutError:
                LOG.warning("Request read timeout")
                return

            if not data:
                return

            # Step 3: Parse JSON request
            try:
                request = json.loads(data.decode("utf-8").strip())
            except json.JSONDecodeError as e:
                response = {"status": "error", "error": f"Invalid JSON: {e}"}
                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()
                return

            LOG.debug(f"IPC request: {request.get('method', 'unknown')}")

            # Step 4: Call handler
            try:
                response = await self.handler(request)
            except Exception as e:
                LOG.error(f"Handler error: {e}")
                response = {"status": "error", "error": str(e)}

            # Step 5: Write response with newline framing (consistent protocol)
            response_data = (json.dumps(response) + "\n").encode("utf-8")
            writer.write(response_data)
            await writer.drain()

            LOG.debug(f"IPC response: {response.get('status', 'unknown')}")

        except Exception as e:
            LOG.error(f"Error handling client: {e}")

        finally:
            # Close connection
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                LOG.debug(f"Error closing connection: {e}")

    async def _authenticate_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> bool:
        """
        Perform challenge-response authentication with client.

        Protocol:
        1. Server sends challenge: {"type": "challenge", "value": "<random-hex>"}
        2. Client computes HMAC-SHA256(auth_secret, challenge)
        3. Client sends: {"auth": "<hmac-hex>"}
        4. Server verifies HMAC matches expected value

        Args:
            reader: Async stream reader
            writer: Async stream writer

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Generate 128-bit random challenge
            challenge = secrets.token_hex(16)

            # Send challenge to client with newline framing (consistent protocol)
            challenge_msg = json.dumps({"type": "challenge", "value": challenge}) + "\n"
            writer.write(challenge_msg.encode("utf-8"))
            await writer.drain()

            LOG.debug("Sent authentication challenge")

            # Receive response from client
            # Use readuntil() with newline delimiter for proper message framing
            # This ensures we don't consume data beyond the auth response
            try:
                response_data = await asyncio.wait_for(
                    reader.readuntil(b'\n'), timeout=Timeouts.IPC_AUTH
                )
            except asyncio.LimitOverrunError:
                # Message too long or no delimiter found
                LOG.warning("Authentication response too long or malformed")
                return False

            if not response_data:
                LOG.warning("Empty authentication response")
                return False

            # Parse response
            try:
                response = json.loads(response_data.decode("utf-8").strip())
            except json.JSONDecodeError:
                LOG.warning("Invalid JSON in authentication response")
                return False

            # Verify HMAC response
            expected_hmac = hmac.new(
                self.auth_secret.encode("utf-8"),
                challenge.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            client_hmac = response.get("auth", "")

            # Use constant-time comparison to prevent timing attacks
            if not hmac.compare_digest(expected_hmac, client_hmac):
                LOG.warning("Authentication failed: HMAC mismatch")
                error_msg = json.dumps({"status": "error", "error": "Authentication failed"})
                writer.write(error_msg.encode("utf-8"))
                await writer.drain()
                return False

            LOG.debug("Client authenticated successfully")
            return True

        except asyncio.TimeoutError:
            LOG.warning("Authentication timeout")
            return False
        except Exception as e:
            LOG.error(f"Authentication error: {e}")
            return False

    async def stop(self) -> None:
        """
        Stop server and cleanup socket (async version).

        Process:
        1. Close server (stop accepting connections)
        2. Remove socket file

        Note: This should be called from within the same event loop as start().
        For cross-thread stopping, use stop_sync() instead.
        """
        LOG.debug("Stopping IPC server")
        self._running = False

        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Remove socket file
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
                LOG.debug(f"Removed socket {self.socket_path}")
            except Exception as e:
                LOG.warning(f"Failed to remove socket: {e}")

    def stop_sync(self) -> None:
        """
        Stop server from another thread (synchronous).

        This method is thread-safe and can be called from the main thread
        to stop the IPC server running in a background thread.

        Process:
        1. Mark server as stopped
        2. Close server socket (cancels serve_forever)
        3. Remove socket file from filesystem
        """
        LOG.debug("Stopping IPC server (sync)")
        self._running = False

        # Close server socket from any thread
        # This will cause serve_forever() to raise CancelledError
        if self.server:
            # Call server.close() in a thread-safe way
            if self._loop and self._loop.is_running():
                # Schedule close in the IPC server's event loop
                self._loop.call_soon_threadsafe(self.server.close)
            else:
                # Event loop not running, close directly
                self.server.close()

        # Remove socket file (filesystem operation, thread-safe)
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
                LOG.debug(f"Removed socket {self.socket_path}")
            except Exception as e:
                LOG.warning(f"Failed to remove socket: {e}")

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
