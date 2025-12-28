"""Process management protocol interfaces.

Defines protocols for process lifecycle operations and VM process spawning.
These protocols enable dependency inversion for process management components.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessProtocol(Protocol):
    """Protocol for process lifecycle management operations.

    Provides core operations for checking process status and waiting for
    process termination without coupling to specific process implementation.
    """

    def is_alive(self, pid: int) -> bool:
        """Check if process is currently running.

        Args:
            pid: Process identifier

        Returns:
            True if process exists and is running
        """
        ...

    def verify_or_raise(self, pid: int, process_type: str) -> None:
        """Verify process is alive or raise exception.

        Args:
            pid: Process identifier
            process_type: Human-readable process type for error messages

        Raises:
            ProcessLookupError: If process is not running
        """
        ...

    def wait_for_exit(self, pid: int, timeout: float) -> bool:
        """Wait for process to exit within timeout.

        Args:
            pid: Process identifier
            timeout: Maximum wait time in seconds

        Returns:
            True if process exited within timeout, False if still running
        """
        ...


@runtime_checkable
class ProcessSpawnerProtocol(Protocol):
    """Protocol for spawning VM runner processes.

    Provides process spawning operations for VM execution without coupling
    to specific process management implementation.
    """

    def spawn_vm_runner(
        self, vm_name: str, config_path: str, socket_path: Path
    ) -> int:
        """Spawn VM runner process.

        Args:
            vm_name: VM identifier
            config_path: Path to VM configuration file
            socket_path: Path where QMP socket should be created

        Returns:
            Process ID of spawned runner

        Raises:
            RuntimeError: If spawn fails
        """
        ...
