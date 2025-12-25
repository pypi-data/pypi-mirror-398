"""State management protocol interfaces.

Defines protocols for VM state repository and path resolution operations.
These protocols enable dependency inversion for state management components.
"""

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from maqet.vm_instance import VMInstance


@runtime_checkable
class VMRepositoryProtocol(Protocol):
    """Protocol for VM state repository operations.

    Provides core CRUD operations for VM instance state management
    without coupling to specific storage implementation.
    """

    def get_vm(self, name: str) -> Optional["VMInstance"]:
        """Retrieve VM instance by name.

        Args:
            name: VM identifier

        Returns:
            VMInstance if found, None otherwise
        """
        ...

    def list_vms(self, status: Optional[str] = None) -> List["VMInstance"]:
        """List all VM instances, optionally filtered by status.

        Args:
            status: Optional status filter (running, stopped, etc.)

        Returns:
            List of VMInstance objects matching criteria
        """
        ...

    def update_vm(self, name: str, **fields) -> "VMInstance":
        """Update VM instance fields.

        Args:
            name: VM identifier
            **fields: Fields to update

        Returns:
            Updated VMInstance

        Raises:
            ValueError: If VM not found
        """
        ...

    def exists(self, name: str) -> bool:
        """Check if VM exists in repository.

        Args:
            name: VM identifier

        Returns:
            True if VM exists
        """
        ...


@runtime_checkable
class PathResolverProtocol(Protocol):
    """Protocol for VM path resolution operations.

    Provides standardized path resolution for VM-related files and directories
    without coupling to specific storage layout implementation.
    """

    def get_vm_socket_path(self, vm_name: str) -> Path:
        """Get QMP socket path for VM.

        Args:
            vm_name: VM identifier

        Returns:
            Absolute path to QMP socket file
        """
        ...

    def get_vm_storage_dir(self, vm_name: str) -> Path:
        """Get storage directory for VM persistent files.

        Args:
            vm_name: VM identifier

        Returns:
            Absolute path to VM storage directory
        """
        ...

    def get_runtime_dir(self) -> Path:
        """Get runtime directory for transient files.

        Returns:
            Absolute path to runtime directory (sockets, PIDs, etc.)
        """
        ...


@runtime_checkable
class StateProtocol(VMRepositoryProtocol, PathResolverProtocol, Protocol):
    """Combined protocol for state management operations.

    Unifies VM repository and path resolver protocols into a single
    interface for components requiring both capabilities.
    """

    pass
