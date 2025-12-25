"""IPC client protocol interfaces.

Defines protocols for inter-process communication with VM runner processes.
These protocols enable dependency inversion for QMP and other IPC mechanisms.
"""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class IPCClientProtocol(Protocol):
    """Protocol for IPC client operations.

    Provides operations for connecting to and communicating with VM runner
    processes via IPC mechanisms (QMP, etc.) without coupling to specific
    IPC implementation.
    """

    def connect(self) -> None:
        """Establish IPC connection to VM runner.

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If connection times out
        """
        ...

    def disconnect(self) -> None:
        """Close IPC connection.

        Silently succeeds if not connected.
        """
        ...

    def send_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Send command to VM runner and await response.

        Args:
            command: Command identifier
            **kwargs: Command-specific arguments

        Returns:
            Response data as dictionary

        Raises:
            ConnectionError: If not connected
            RuntimeError: If command fails
        """
        ...

    def get_status(self) -> Dict[str, Any]:
        """Query VM status via IPC.

        Returns:
            Status information as dictionary

        Raises:
            ConnectionError: If not connected
        """
        ...
