"""
Wait Conditions for VM Operations

Concrete wait condition implementations for VM lifecycle events:
- process-started: VM runner process responding to IPC (default)
- file-exists: Generic file existence check
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from maqet.logger import LOG
from maqet.process_spawner import get_socket_path
from maqet.utils.process_validation import validate_pid_exists
from maqet.utils.wait_logic import WaitCondition

if TYPE_CHECKING:
    from maqet.protocols.ipc import IPCClientProtocol
    from maqet.state import StateManager, VMInstance


class ProcessStartedCondition(WaitCondition):
    """
    Wait condition: VM runner process started and responding to IPC.

    Checks that:
    1. Socket file exists
    2. Runner responds to authenticated ping
    3. QEMU process (optional) is running

    This is the default wait condition for 'maqet start'.

    Refactored to accept VMInstance directly, removing StateManager dependency
    and circular imports per fix-architecture-circular-deps.md spec.
    """

    def __init__(
        self,
        vm: Union[str, "VMInstance"],
        state_manager: Optional["StateManager"] = None,
        runner_client: Optional["IPCClientProtocol"] = None,
        verify_qemu: bool = True
    ):
        """
        Initialize process started condition.

        Args:
            vm: VMInstance object or vm_id string (legacy)
            state_manager: Optional StateManager (needed for legacy vm_id or RunnerClient creation)
            runner_client: Optional pre-created IPC client (avoids creating new one)
            verify_qemu: Also verify QEMU process is running (default True)

        Note:
            New code should pass VMInstance and optionally runner_client.
            Legacy vm_id + state_manager still supported for backward compatibility.
        """
        # Handle backward compatibility: vm can be string (vm_id) or VMInstance
        if isinstance(vm, str):
            # Legacy mode: vm_id string
            if state_manager is None:
                raise ValueError("state_manager required when passing vm_id string")
            self.vm_id = vm
            self.vm_instance = None  # Will fetch on demand
            self.state_manager = state_manager
        else:
            # New mode: VMInstance object
            self.vm_id = vm.id
            self.vm_instance = vm
            self.state_manager = state_manager  # Optional, needed for RunnerClient creation

        super().__init__(f"process-started[{self.vm_id}]")
        self.verify_qemu = verify_qemu
        self._client = runner_client
        self._client_owned = runner_client is None  # Track if we created the client

    def _get_vm_instance(self) -> "VMInstance":
        """Get VMInstance, fetching from state_manager if needed (legacy mode)."""
        if self.vm_instance is not None:
            return self.vm_instance

        # Legacy mode: fetch from state_manager
        if self.state_manager is None:
            raise RuntimeError("Cannot fetch VM: no VMInstance or StateManager provided")

        vm = self.state_manager.get_vm(self.vm_id)
        if vm is None:
            raise RuntimeError(f"VM {self.vm_id} not found in state")

        # Cache for subsequent calls
        self.vm_instance = vm
        return vm

    def check(self) -> bool:
        """
        Check if VM runner is responding.

        Returns:
            True if runner ready, False otherwise
        """
        # Get socket path
        if self.vm_instance is not None and self.vm_instance.socket_path:
            # New mode: use VMInstance.socket_path if available
            socket_path = Path(self.vm_instance.socket_path)
        else:
            # Legacy mode or socket_path not set: use get_socket_path
            socket_path = get_socket_path(self.vm_id)

        # Quick check: socket exists
        if not socket_path.exists():
            return False

        try:
            # Create client if needed
            if self._client is None:
                from maqet.ipc.runner_client import RunnerClient
                if self.state_manager is None:
                    raise RuntimeError("Cannot create RunnerClient: no StateManager provided")
                self._client = RunnerClient(self.vm_id, self.state_manager)
                self._client_owned = True

            # Authenticated ping
            if not self._client.ping():
                return False

            # Optional: Verify QEMU process
            if self.verify_qemu:
                status = self._client.status()
                qemu_pid = status.get("qemu_pid")

                if not qemu_pid:
                    LOG.debug(f"QEMU not started yet for {self.vm_id}")
                    return False

                # Verify QEMU process exists
                try:
                    if not validate_pid_exists(qemu_pid):
                        LOG.warning(f"QEMU PID {qemu_pid} not found")
                        return False
                except Exception as e:
                    LOG.debug(f"QEMU process validation failed: {e}")
                    return False

            return True

        except Exception as e:
            LOG.debug(f"Process readiness check failed: {e}")
            return False

    def cleanup(self) -> None:
        """Close IPC client connection."""
        if self._client and self._client_owned:
            try:
                # RunnerClient doesn't have explicit cleanup currently
                # but we set to None to allow reconnection if needed
                self._client = None
            except Exception as e:
                LOG.debug(f"Client cleanup warning: {e}")


class FileExistsCondition(WaitCondition):
    """
    Wait condition: File exists on filesystem.

    Generic condition for waiting on file creation.
    Useful for socket files, PID files, marker files, etc.
    """

    def __init__(self, file_path: Path, description: Optional[str] = None):
        """
        Initialize file exists condition.

        Args:
            file_path: Path to file
            description: Optional description for logging (defaults to filename)
        """
        if description is None:
            description = file_path.name
        super().__init__(f"file-exists[{description}]")
        self.file_path = Path(file_path)

    def check(self) -> bool:
        """
        Check if file exists.

        Returns:
            True if file exists, False otherwise
        """
        return self.file_path.exists()


def get_wait_condition(
    condition_name: str,
    vm_id: str,
    state_manager: "StateManager",
    **kwargs
) -> WaitCondition:
    """
    Factory function to create wait conditions by name.

    Args:
        condition_name: Condition name (process-started, file-exists)
        vm_id: VM identifier (can also pass vm_instance via kwargs for new code)
        state_manager: StateManager instance
        **kwargs: Additional condition-specific parameters
            - verify_qemu: bool (process-started)
            - runner_client: IPCClientProtocol (process-started)
            - vm_instance: VMInstance (process-started, preferred over vm_id)
            - file_path: Path (file-exists, required)
            - description: str (file-exists, optional)

    Returns:
        WaitCondition instance

    Raises:
        ValueError: If condition_name unknown

    Example:
        # Legacy mode
        condition = get_wait_condition(
            "process-started",
            "myvm",
            state_manager,
        )

        # New mode with VMInstance
        condition = get_wait_condition(
            "process-started",
            vm.id,
            state_manager,
            vm_instance=vm,
        )
    """
    condition_name = condition_name.lower()

    if condition_name == "process-started":
        verify_qemu = kwargs.get("verify_qemu", True)
        runner_client = kwargs.get("runner_client")
        vm_instance = kwargs.get("vm_instance")

        # Prefer vm_instance if provided, otherwise use vm_id (legacy)
        vm = vm_instance if vm_instance is not None else vm_id

        return ProcessStartedCondition(
            vm,
            state_manager=state_manager,
            runner_client=runner_client,
            verify_qemu=verify_qemu
        )

    elif condition_name == "file-exists":
        file_path = kwargs.get("file_path")
        if file_path is None:
            raise ValueError("file-exists condition requires 'file_path' parameter")
        description = kwargs.get("description")
        return FileExistsCondition(file_path, description)

    elif condition_name == "ssh-ready":
        raise ValueError(
            "Invalid wait condition 'ssh-ready'\n\n"
            "SSH readiness checking was removed in maqet v0.1.0.\n\n"
            "Available conditions:\n"
            "  - process-started (default): VM runner process is ready\n"
            "  - file-exists: Wait for specific file to exist\n\n"
            "For SSH checking, use standard tools:\n"
            "  m.start(\"myvm\")  # Wait for VM infrastructure\n"
            "  \n"
            "  # Then use external SSH checking\n"
            "  import subprocess\n"
            "  subprocess.run([\"ssh-keyscan\", \"-p\", \"2222\", \"localhost\"])\n\n"
            "See: https://gitlab.com/m4x0n_24/maqet/docs/MIGRATION_v0.1.0.md"
        )

    elif condition_name == "boot-complete":
        raise ValueError(
            "Invalid wait condition 'boot-complete'\n\n"
            "Boot complete checking was removed in maqet v0.1.0.\n\n"
            "Available conditions:\n"
            "  - process-started (default): VM runner process is ready\n"
            "  - file-exists: Wait for specific file to exist\n\n"
            "For boot detection, use standard tools:\n"
            "  m.start(\"myvm\")  # Wait for VM infrastructure\n"
            "  \n"
            "  # Then check boot status via your preferred method\n"
            "  # (guest agent, file marker, SSH, etc.)\n\n"
            "See: https://gitlab.com/m4x0n_24/maqet/docs/MIGRATION_v0.1.0.md"
        )

    else:
        raise ValueError(
            f"Unknown wait condition '{condition_name}'. "
            f"Available: process-started, file-exists"
        )


# Convenience aliases for common conditions
CONDITION_ALIASES = {
    "process": "process-started",
    "started": "process-started",
}


def normalize_condition_name(condition_name: str) -> str:
    """
    Normalize condition name using aliases.

    Args:
        condition_name: Condition name or alias

    Returns:
        Normalized condition name

    Example:
        normalize_condition_name("process") -> "process-started"
        normalize_condition_name("started") -> "process-started"
    """
    condition_lower = condition_name.lower()
    return CONDITION_ALIASES.get(condition_lower, condition_lower)
