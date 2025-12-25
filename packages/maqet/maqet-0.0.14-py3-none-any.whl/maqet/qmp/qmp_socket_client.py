"""
QMP Socket Client - Direct QMP socket communication for cross-process operations.

Provides direct Unix socket communication with QEMU's QMP (QEMU Machine Protocol)
server, bypassing the QEMUMachine wrapper. This enables QMP commands to work
across process boundaries without requiring access to the QEMUMachine instance.

Architecture:
    This client implements the QMP JSON-RPC protocol directly over Unix sockets,
    allowing CLI commands to communicate with QEMU processes even after the
    original CLI process that started the VM has exited.

QMP Protocol Flow:
    1. Connect to Unix socket
    2. Read greeting: {"QMP": {"version": {...}, "capabilities": [...]}}
    3. Send capabilities: {"execute": "qmp_capabilities"}
    4. Wait for ack: {"return": {}}
    5. Execute commands: {"execute": "command-name", "arguments": {...}}
    6. Receive responses: {"return": {...}} or {"error": {...}}

See Also:
    - specs/fix-cross-process-qmp-communication.md (specification)
    - QEMU QMP documentation: https://wiki.qemu.org/Documentation/QMP
    - managers/qmp_manager.py (IPC-based alternative approach)
"""

import json
import socket
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..utils.paths import ensure_path

from ..exceptions import QMPConnectionError, QMPError, QMPTimeoutError
from ..logger import LOG


class QMPSocketError(QMPError):
    """QMP socket communication errors."""


class QMPSocketClient:
    """
    Direct QMP socket client for cross-process communication.

    Connects directly to QMP Unix socket without requiring QEMUMachine instance.
    Implements QMP JSON-RPC protocol for command execution.

    This enables QMP commands to work from CLI even after the CLI process that
    started the VM has exited, fixing the cross-process communication limitation.

    Example:
        >>> client = QMPSocketClient("/run/user/1000/maqet/myvm.qmp.sock")
        >>> client.connect()
        >>> result = client.execute("query-status")
        >>> print(result)
        {'status': 'running', 'singlestep': False, 'running': True}
        >>> client.disconnect()

    Context Manager Support:
        >>> with QMPSocketClient("/path/to/socket") as client:
        ...     result = client.execute("query-status")
        ...     print(result)

    Thread Safety:
        This class is NOT thread-safe. Create separate instances for
        concurrent operations.

    See Also:
        - docs/dev/architecture/qmp-architecture.md
        - QEMU QMP documentation: https://wiki.qemu.org/Documentation/QMP
    """

    def __init__(self, socket_path: Union[str, Path], timeout: int = 30):
        """
        Initialize QMP socket client.

        Args:
            socket_path: Path to QMP Unix socket
            timeout: Command timeout in seconds (default: 30)

        Raises:
            ValueError: If socket_path is empty or invalid
        """
        # Convert to Path immediately at boundary
        if not socket_path:
            raise ValueError("socket_path cannot be empty")

        self.socket_path = ensure_path(socket_path)
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None
        self._connected = False

        LOG.debug(
            f"QMPSocketClient initialized: socket={self.socket_path}, "
            f"timeout={self.timeout}s"
        )

    def __enter__(self):
        """Context manager entry - connect to socket."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect from socket."""
        self.disconnect()
        return False

    def connect(self) -> None:
        """
        Connect to QMP socket and complete capability negotiation.

        QMP Protocol Handshake:
        1. Server sends greeting: {"QMP": {...}}
        2. Client sends: {"execute": "qmp_capabilities"}
        3. Server replies: {"return": {}}
        4. Connection ready for commands

        Raises:
            QMPSocketError: If connection or negotiation fails
            QMPConnectionError: If socket not found or permission denied
            QMPTimeoutError: If connection times out
        """
        if self._connected:
            LOG.warning(f"QMP socket already connected: {self.socket_path}")
            return

        # Validate socket exists
        if not self.socket_path.exists():
            raise QMPConnectionError(
                f"QMP socket not found: {self.socket_path}. "
                f"VM may have crashed or not started yet."
            )

        # Check socket is a socket (not regular file)
        if not self.socket_path.is_socket():
            raise QMPSocketError(
                f"Path is not a Unix socket: {self.socket_path}"
            )

        # Create Unix socket
        try:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)

            LOG.debug(f"Connecting to QMP socket: {self.socket_path}")
            self._socket.connect(str(self.socket_path))

        except PermissionError as e:
            raise QMPConnectionError(
                f"Permission denied accessing QMP socket: {self.socket_path}. "
                f"Socket may be owned by different user."
            ) from e
        except socket.timeout as e:
            raise QMPTimeoutError(
                f"Connection timeout to QMP socket: {self.socket_path}. "
                f"VM may be unresponsive."
            ) from e
        except OSError as e:
            raise QMPConnectionError(
                f"Failed to connect to QMP socket {self.socket_path}: {e}"
            ) from e

        # Perform QMP capability negotiation
        try:
            self._negotiate_capabilities()
            self._connected = True
            LOG.debug(f"QMP connection established: {self.socket_path}")

        except Exception as e:
            # Close socket on negotiation failure
            self._close_socket()
            raise QMPSocketError(
                f"QMP capability negotiation failed: {e}"
            ) from e

    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute QMP command and return result.

        Args:
            command: QMP command name (e.g., "query-status", "screendump")
            **kwargs: Command arguments (e.g., filename="/tmp/screen.ppm")

        Returns:
            Command result dictionary from QMP server

        Raises:
            QMPSocketError: If not connected or command execution fails
            QMPTimeoutError: If command times out
            QMPError: If QMP server returns error response

        Example:
            >>> result = client.execute("query-status")
            >>> result = client.execute("screendump", filename="/tmp/screen.ppm")
            >>> result = client.execute("send-key", keys=["ctrl", "alt", "f2"])
        """
        if not self._connected or not self._socket:
            raise QMPSocketError(
                "Not connected to QMP socket. Call connect() first."
            )

        # Build QMP command
        qmp_command: Dict[str, Any] = {"execute": command}
        if kwargs:
            qmp_command["arguments"] = kwargs

        LOG.debug(f"Executing QMP command: {qmp_command}")

        try:
            # Send command
            self._send_json(qmp_command)

            # Read response
            response = self._read_json()

            # Check for QMP error response
            if "error" in response:
                error_class = response["error"].get("class", "Unknown")
                error_desc = response["error"].get("desc", "Unknown error")
                raise QMPError(
                    f"QMP command '{command}' failed: {error_class}: {error_desc}"
                )

            # Return successful result
            if "return" in response:
                LOG.debug(f"QMP command '{command}' completed successfully")
                return response["return"]

            # Unexpected response format
            raise QMPSocketError(
                f"Unexpected QMP response format (no 'return' or 'error'): {response}"
            )

        except socket.timeout as e:
            raise QMPTimeoutError(
                f"QMP command '{command}' timed out after {self.timeout} seconds. "
                f"VM may be unresponsive."
            ) from e
        except (OSError, ConnectionError) as e:
            raise QMPSocketError(
                f"QMP socket communication error during '{command}': {e}"
            ) from e

    def disconnect(self) -> None:
        """
        Close QMP socket connection.

        Safe to call multiple times or when not connected.
        """
        if self._connected:
            LOG.debug(f"Disconnecting from QMP socket: {self.socket_path}")
            self._close_socket()
            self._connected = False
        else:
            LOG.debug("QMP socket already disconnected")

    def _negotiate_capabilities(self) -> None:
        """
        Perform QMP capability negotiation.

        QMP handshake sequence:
        1. Read greeting: {"QMP": {"version": {...}, "capabilities": [...]}}
        2. Send capabilities: {"execute": "qmp_capabilities"}
        3. Wait for ack: {"return": {}}

        Raises:
            QMPSocketError: If negotiation fails or protocol violation
            QMPTimeoutError: If negotiation times out
        """
        # Step 1: Read greeting
        try:
            greeting = self._read_json()
        except socket.timeout as e:
            raise QMPTimeoutError(
                f"Timeout waiting for QMP greeting from {self.socket_path}"
            ) from e

        # Validate greeting format
        if "QMP" not in greeting:
            raise QMPSocketError(
                f"Invalid QMP greeting (missing 'QMP' key): {greeting}"
            )

        qmp_info = greeting["QMP"]
        version_info = qmp_info.get("version", {})
        capabilities = qmp_info.get("capabilities", [])

        LOG.debug(
            f"QMP greeting received: version={version_info}, "
            f"capabilities={capabilities}"
        )

        # Step 2: Send qmp_capabilities command
        try:
            self._send_json({"execute": "qmp_capabilities"})
        except socket.timeout as e:
            raise QMPTimeoutError(
                f"Timeout sending qmp_capabilities to {self.socket_path}"
            ) from e

        # Step 3: Wait for acknowledgment
        try:
            response = self._read_json()
        except socket.timeout as e:
            raise QMPTimeoutError(
                f"Timeout waiting for qmp_capabilities acknowledgment from {self.socket_path}"
            ) from e

        # Validate acknowledgment
        if "return" not in response:
            error_info = response.get("error", "Unknown error")
            raise QMPSocketError(
                f"QMP capability negotiation failed: {error_info}"
            )

        LOG.debug("QMP capability negotiation completed successfully")

    def _send_json(self, data: Dict[str, Any]) -> None:
        """
        Send JSON-RPC message to QMP socket.

        QMP protocol uses newline-delimited JSON. Each message must be
        followed by exactly one newline character.

        Args:
            data: Dictionary to send as JSON

        Raises:
            QMPSocketError: If not connected
            socket.timeout: If send times out
            OSError: If socket communication fails
        """
        if not self._socket:
            raise QMPSocketError("Socket not connected")

        # Encode JSON with newline delimiter
        message = json.dumps(data).encode('utf-8') + b'\n'

        # Send all bytes (handles partial sends)
        self._socket.sendall(message)

        LOG.debug(f"Sent QMP message: {data}")

    def _read_json(self) -> Dict[str, Any]:
        """
        Read JSON-RPC response from QMP socket.

        QMP protocol uses newline-delimited JSON. Reads from socket until
        newline is encountered, then parses JSON.

        Returns:
            Parsed JSON response as dictionary

        Raises:
            QMPSocketError: If connection closed or invalid JSON
            socket.timeout: If read times out
            OSError: If socket communication fails
        """
        if not self._socket:
            raise QMPSocketError("Socket not connected")

        # Read until newline delimiter
        buffer = b""
        while b'\n' not in buffer:
            try:
                chunk = self._socket.recv(4096)
            except socket.timeout:
                # Re-raise timeout for caller to handle
                raise

            # Check for connection close
            if not chunk:
                raise QMPSocketError(
                    "QMP connection closed unexpectedly (recv returned empty). "
                    "VM may have crashed or socket was closed."
                )

            buffer += chunk

        # Extract first complete JSON message (up to newline)
        line, _ = buffer.split(b'\n', 1)

        # Parse JSON
        try:
            response = json.loads(line.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise QMPSocketError(
                f"Invalid JSON from QMP socket: {line.decode('utf-8', errors='replace')}"
            ) from e

        LOG.debug(f"Received QMP message: {response}")
        return response

    def _close_socket(self) -> None:
        """
        Close socket connection safely.

        Handles any exceptions during close to ensure cleanup always succeeds.
        """
        if self._socket:
            try:
                self._socket.close()
            except Exception as e:
                LOG.warning(f"Error closing QMP socket: {e}")
            finally:
                self._socket = None
