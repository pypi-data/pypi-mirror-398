"""Storage registry protocol interfaces.

Defines protocols for storage file registration and cleanup operations.
These protocols enable dependency inversion for storage management components.
"""

from pathlib import Path
from typing import List, Protocol, runtime_checkable


@runtime_checkable
class StorageRegistryProtocol(Protocol):
    """Protocol for storage file registry operations.

    Provides operations for tracking VM storage files (disks, snapshots)
    and coordinating cleanup without coupling to specific registry implementation.
    """

    def register_storage(self, vm_name: str, path: Path) -> None:
        """Register a storage file for VM.

        Args:
            vm_name: VM identifier
            path: Absolute path to storage file

        Raises:
            ValueError: If path is not absolute or invalid
        """
        ...

    def get_storage_files(self, vm_name: str) -> List[Path]:
        """Get all registered storage files for VM.

        Args:
            vm_name: VM identifier

        Returns:
            List of absolute paths to registered storage files
        """
        ...

    def cleanup_storage(self, vm_name: str) -> None:
        """Clean up storage files for VM.

        Removes all registered storage files and unregisters them.
        Silently succeeds if files don't exist.

        Args:
            vm_name: VM identifier
        """
        ...
