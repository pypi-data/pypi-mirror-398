"""
Storage Registry for VM Storage Management

Manages tracking of storage files associated with VMs in the database.
Provides functionality for:
- Registering storage files with VMs
- Finding orphaned storage (files without VM entries)
- Verifying storage integrity
- Managing storage lifecycle

Part of the Transactional Storage Management feature.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from .protocols import PathResolverProtocol

from .logger import LOG


# Valid storage types that can be registered
VALID_STORAGE_TYPES = {"disk", "snapshot", "config"}


@dataclass
class StorageEntry:
    """
    Represents a storage file tracked in the registry.

    Attributes:
        vm_name: Name of the VM that owns this storage
        storage_path: Path to the storage file on disk
        storage_type: Type of storage ('disk', 'snapshot', 'config')
        size_bytes: Size of the storage file in bytes (None if not available)
        created_at: Timestamp when storage was registered
        last_verified: Timestamp of last integrity verification
    """

    vm_name: str
    storage_path: Path
    storage_type: str
    size_bytes: Optional[int] = None
    created_at: Optional[str] = None
    last_verified: Optional[str] = None


class StorageRegistry:
    """
    Manages storage file tracking in database.

    Provides methods to register, unregister, and query storage files
    associated with VMs. Enables detection of orphaned storage and
    verification of storage integrity.

    The registry maintains a relationship between VM names and their
    storage files, with CASCADE DELETE to ensure cleanup when VMs are removed.
    """

    def __init__(
        self,
        db_conn: sqlite3.Connection,
        path_resolver: Optional["PathResolverProtocol"] = None,
        data_dir: Optional[Path] = None,
    ):
        """
        Initialize storage registry.

        Args:
            db_conn: SQLite database connection (must have storage_registry table)
            path_resolver: Optional path resolver for dependency injection
            data_dir: Optional XDG data directory (for backward compatibility)
        """
        self.db = db_conn
        self._path_resolver = path_resolver
        self._data_dir = data_dir

    def register_storage(
        self, vm_name: str, storage_path: Path, storage_type: str
    ) -> None:
        """
        Register a storage file for a VM.

        Adds an entry to the storage registry linking a storage file to a VM.
        If the file exists, its size is recorded. Duplicate registrations
        (same vm_name + storage_path) will fail due to UNIQUE constraint.

        Args:
            vm_name: VM name (must exist in vm_instances table)
            storage_path: Path to storage file
            storage_type: Type of storage ('disk', 'snapshot', 'config')

        Raises:
            ValueError: If storage_type is not valid
            sqlite3.IntegrityError: If VM doesn't exist or storage already registered
            sqlite3.OperationalError: If database operation fails
        """
        # Validate storage type
        if storage_type not in VALID_STORAGE_TYPES:
            raise ValueError(
                f"Invalid storage type '{storage_type}'. "
                f"Must be one of: {', '.join(sorted(VALID_STORAGE_TYPES))}"
            )

        # Get file size if it exists
        size_bytes = None
        if storage_path.exists():
            try:
                size_bytes = storage_path.stat().st_size
            except OSError as e:
                LOG.warning(
                    f"Failed to get size for {storage_path}: {e}"
                )

        # Insert storage entry
        self.db.execute(
            """
            INSERT INTO storage_registry (vm_name, storage_path, storage_type, size_bytes)
            VALUES (?, ?, ?, ?)
            """,
            (vm_name, str(storage_path), storage_type, size_bytes),
        )
        self.db.commit()

        LOG.debug(
            f"Registered storage for VM '{vm_name}': {storage_path} ({storage_type})"
        )

    def unregister_storage(self, storage_path: Path) -> None:
        """
        Remove storage from registry.

        This only removes the registry entry - it does NOT delete the
        actual file on disk. Use this when you want to untrack a storage
        file without deleting it.

        Args:
            storage_path: Path to storage file to unregister
        """
        cursor = self.db.execute(
            "DELETE FROM storage_registry WHERE storage_path = ?",
            (str(storage_path),),
        )
        self.db.commit()

        if cursor.rowcount > 0:
            LOG.debug(f"Unregistered storage: {storage_path}")
        else:
            LOG.debug(f"Storage not found in registry: {storage_path}")

    def get_vm_storage(self, vm_name: str) -> List[StorageEntry]:
        """
        Get all storage files for a VM.

        Retrieves all registered storage entries associated with the
        specified VM name.

        Args:
            vm_name: Name of the VM

        Returns:
            List of StorageEntry objects for the VM
        """
        cursor = self.db.execute(
            """
            SELECT vm_name, storage_path, storage_type, size_bytes, created_at, last_verified
            FROM storage_registry
            WHERE vm_name = ?
            """,
            (vm_name,),
        )

        entries = [
            StorageEntry(
                vm_name=row[0],
                storage_path=Path(row[1]),
                storage_type=row[2],
                size_bytes=row[3],
                created_at=row[4],
                last_verified=row[5],
            )
            for row in cursor.fetchall()
        ]

        LOG.debug(f"Found {len(entries)} storage entries for VM '{vm_name}'")
        return entries

    def find_orphaned_storage(self) -> List[StorageEntry]:
        """
        Find storage files that exist on disk but have no VM entry.

        Scans the storage directories for disk image files (.qcow2, .img)
        and compares them against registered storage. Returns files that
        exist on disk but are not registered in the database.

        Returns:
            List of orphaned storage entries (StorageEntry objects with vm_name='unknown')
        """
        # Get all registered storage paths
        cursor = self.db.execute(
            "SELECT DISTINCT storage_path FROM storage_registry"
        )
        registered_paths = {Path(row[0]) for row in cursor.fetchall()}

        # Scan storage directories for actual files
        storage_dirs = self._get_storage_directories()
        actual_files = set()

        for storage_dir in storage_dirs:
            if storage_dir.exists():
                # Find all qcow2 and img files recursively
                actual_files.update(storage_dir.glob("**/*.qcow2"))
                actual_files.update(storage_dir.glob("**/*.img"))

        # Find orphans (files without registry entry)
        orphaned_paths = actual_files - registered_paths

        # Convert to StorageEntry objects
        orphaned_entries = []
        for path in orphaned_paths:
            try:
                size_bytes = path.stat().st_size
            except OSError as e:
                LOG.warning(f"Failed to get size for orphaned file {path}: {e}")
                size_bytes = None

            orphaned_entries.append(
                StorageEntry(
                    vm_name="unknown",
                    storage_path=path,
                    storage_type="disk",
                    size_bytes=size_bytes,
                )
            )

        LOG.info(f"Found {len(orphaned_entries)} orphaned storage files")
        return orphaned_entries

    def verify_storage_exists(self, vm_name: str) -> Dict[str, bool]:
        """
        Verify all registered storage for VM actually exists.

        Checks if each registered storage file for the VM exists on disk.
        Useful for detecting broken VM configurations where the database
        has entries but files are missing.

        Args:
            vm_name: Name of the VM to verify

        Returns:
            Dict mapping storage_path (str) -> exists (bool)
        """
        storage_entries = self.get_vm_storage(vm_name)

        verification_results = {
            str(entry.storage_path): entry.storage_path.exists()
            for entry in storage_entries
        }

        missing_count = sum(1 for exists in verification_results.values() if not exists)
        if missing_count > 0:
            LOG.warning(
                f"VM '{vm_name}' has {missing_count} missing storage file(s)"
            )
        else:
            LOG.debug(f"All storage verified for VM '{vm_name}'")

        return verification_results

    def _get_storage_directories(self) -> List[Path]:
        """
        Get all directories where storage might be located.

        Returns standard XDG data directory paths where maqet stores
        VM disk images and related files.

        Returns:
            List of Path objects for storage directories
        """
        # Use injected path resolver if available
        if self._path_resolver:
            runtime_parent = self._path_resolver.get_runtime_dir().parent
            return [
                runtime_parent / "disks",
                runtime_parent / "images",
                runtime_parent / "snapshots",
            ]
        # Use provided data_dir if available
        elif self._data_dir:
            return [
                self._data_dir / "disks",
                self._data_dir / "images",
                self._data_dir / "snapshots",
            ]
        else:
            # Fallback: inline import for backward compatibility only
            from .state import XDGDirectories

            xdg = XDGDirectories()
            data_dir = xdg.data_dir
            return [
                data_dir / "disks",
                data_dir / "images",
                data_dir / "snapshots",
            ]
