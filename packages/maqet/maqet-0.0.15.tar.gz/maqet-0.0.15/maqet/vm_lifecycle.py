"""
VM Lifecycle Manager

Manages VM lifecycle with transactional storage operations.
Provides atomic operations for VM creation, deletion, and storage management
to prevent orphaned storage and inconsistent state between database and filesystem.

Part of the Transactional Storage Management feature (Phase 2).
"""

from pathlib import Path
from typing import Dict, List

from .exceptions import StateError
from .logger import LOG
from .state import StateManager
from .storage_registry import StorageRegistry


class VMLifecycleManager:
    """
    Manages VM lifecycle with transactional storage.

    Provides atomic operations that ensure VM entries and storage files
    are always in sync. If any operation fails, all changes are rolled back
    to maintain consistency.

    Key features:
    - Atomic VM + storage creation
    - Explicit storage control on deletion
    - Orphaned storage reattachment
    - Transactional safety with rollback

    Integrates with:
    - StateManager for VM database operations
    - StorageRegistry for storage tracking

    Note: This implementation uses a compensating transaction pattern where
    if storage registration fails after VM creation, the VM is deleted to
    maintain consistency. This is simpler than trying to wrap StateManager's
    internal connection management.
    """

    def __init__(self, state_manager: StateManager):
        """
        Initialize VM lifecycle manager.

        Args:
            state_manager: StateManager instance for VM database operations
        """
        self.state_manager = state_manager

        # Create a separate connection for storage registry operations
        # This is safe because storage registry only reads/writes the storage_registry table
        # while StateManager operations work on vm_instances table
        self._db_conn = self.state_manager._create_connection()

        # Initialize storage registry with its own connection and data dir
        self.storage_registry = StorageRegistry(
            self._db_conn, data_dir=self.state_manager.xdg.data_dir
        )

    def create_vm_with_storage(
        self,
        vm_name: str,
        vm_config: Dict,
        disk_paths: List[Path],
    ) -> str:
        """
        Create VM and register its storage atomically.

        This method ensures that either both the VM entry and storage registrations
        succeed, or neither happens (atomic operation). If any disk path doesn't exist
        or registration fails, the entire operation is rolled back.

        Uses a compensating transaction pattern: if storage registration fails after
        VM creation, the VM is deleted to maintain consistency.

        Args:
            vm_name: VM name (must be unique)
            vm_config: VM configuration dictionary
            disk_paths: List of disk image paths to register with the VM

        Returns:
            VM instance ID

        Raises:
            ValueError: If any disk path doesn't exist
            StateError: If VM creation fails (name conflict, etc.)
            Exception: If database operation fails
        """
        # Validate all disk paths exist BEFORE starting operations
        for disk_path in disk_paths:
            if not disk_path.exists():
                raise ValueError(f"Disk image not found: {disk_path}")

        vm_id = None
        try:
            # Step 1: Create VM entry in database
            vm_id = self.state_manager.create_vm(vm_name, vm_config)
            LOG.debug(f"Created VM '{vm_name}' with ID {vm_id}")

            # Step 2: Register all storage files
            for disk_path in disk_paths:
                self.storage_registry.register_storage(
                    vm_name,
                    disk_path,
                    storage_type="disk",
                )
                LOG.debug(f"Registered storage for VM '{vm_name}': {disk_path}")

            LOG.info(
                f"Successfully created VM '{vm_name}' with {len(disk_paths)} storage file(s)"
            )
            return vm_id

        except Exception as e:
            # Compensating transaction: if storage registration failed after VM creation,
            # delete the VM to maintain consistency
            if vm_id is not None:
                LOG.warning(
                    f"Storage registration failed for VM '{vm_name}', rolling back VM creation"
                )
                try:
                    self.state_manager.remove_vm(vm_name)
                    LOG.debug(f"Rolled back VM creation: '{vm_name}'")
                except Exception as rollback_error:
                    LOG.error(
                        f"Failed to rollback VM creation for '{vm_name}': {rollback_error}"
                    )
            raise

    def delete_vm(
        self,
        vm_name: str,
        delete_storage: bool = False,
        keep_snapshots: bool = False,
    ) -> None:
        """
        Delete VM with explicit storage handling.

        Provides fine-grained control over what happens to storage files when
        a VM is deleted. By default, storage is kept to prevent accidental data loss.

        Safety checks:
        - Verifies VM is stopped before deletion
        - Atomic operation (VM + storage registry changes via CASCADE DELETE)
        - Optional storage file deletion with snapshot preservation

        Args:
            vm_name: VM name to delete
            delete_storage: If True, delete storage files from disk (default: False)
            keep_snapshots: If True, keep snapshot files even if delete_storage=True

        Raises:
            ValueError: If VM is running (must stop first for safety)
            StateError: If VM doesn't exist or database operation fails
        """
        # Get VM instance to check status
        vm_instance = self.state_manager.get_vm(vm_name)
        if not vm_instance:
            raise StateError(f"VM '{vm_name}' not found")

        # Safety check: Verify VM is stopped
        if vm_instance.status == "running":
            raise ValueError(
                f"Cannot delete running VM '{vm_name}'. Stop it first with: maqet stop {vm_name}"
            )

        # Get all storage for VM BEFORE deletion (CASCADE will remove registry entries)
        storage_entries = self.storage_registry.get_vm_storage(vm_name)
        LOG.debug(f"Found {len(storage_entries)} storage entries for VM '{vm_name}'")

        # Delete VM entry (CASCADE DELETE will automatically remove storage registry entries)
        success = self.state_manager.remove_vm(vm_name)
        if not success:
            raise StateError(f"Failed to delete VM '{vm_name}' from database")

        LOG.debug(f"Deleted VM '{vm_name}' from database")

        # Handle storage files if requested
        if delete_storage:
            deleted_count = 0
            skipped_count = 0

            for entry in storage_entries:
                # Skip snapshots if keep_snapshots is True
                if keep_snapshots and entry.storage_type == "snapshot":
                    LOG.debug(f"Keeping snapshot: {entry.storage_path}")
                    skipped_count += 1
                    continue

                # Delete the file if it exists
                if entry.storage_path.exists():
                    try:
                        entry.storage_path.unlink()
                        LOG.debug(f"Deleted storage file: {entry.storage_path}")
                        deleted_count += 1
                    except OSError as e:
                        LOG.warning(
                            f"Failed to delete storage file {entry.storage_path}: {e}"
                        )
                else:
                    LOG.debug(f"Storage file already gone: {entry.storage_path}")

            LOG.info(
                f"VM '{vm_name}' deleted with {deleted_count} storage file(s) removed"
                + (f", {skipped_count} snapshot(s) kept" if skipped_count > 0 else "")
            )
        else:
            LOG.info(
                f"VM '{vm_name}' deleted, {len(storage_entries)} storage file(s) kept"
            )

    def attach_orphaned_storage(
        self,
        vm_name: str,
        storage_path: Path,
        vm_config: Dict,
    ) -> str:
        """
        Create VM entry for existing orphaned storage.

        Allows reattaching storage files that exist on disk but have no VM entry.
        This is useful for recovering from manual deletions or database issues.

        Uses the same compensating transaction pattern as create_vm_with_storage.

        Args:
            vm_name: New VM name to create
            storage_path: Path to orphaned storage file
            vm_config: VM configuration dictionary

        Returns:
            VM instance ID

        Raises:
            ValueError: If storage doesn't exist or VM name already exists
            StateError: If VM creation fails
        """
        # Validate storage exists
        if not storage_path.exists():
            raise ValueError(f"Storage file not found: {storage_path}")

        # Validate VM doesn't already exist
        existing_vm = self.state_manager.get_vm(vm_name)
        if existing_vm:
            raise ValueError(
                f"VM '{vm_name}' already exists. "
                f"Use a different name or delete the existing VM first."
            )

        vm_id = None
        try:
            # Create VM entry
            vm_id = self.state_manager.create_vm(vm_name, vm_config)
            LOG.debug(f"Created VM '{vm_name}' for orphaned storage")

            # Register existing storage
            self.storage_registry.register_storage(
                vm_name,
                storage_path,
                storage_type="disk",
            )

            LOG.info(
                f"Successfully attached orphaned storage to VM '{vm_name}': {storage_path}"
            )
            return vm_id

        except Exception as e:
            # Compensating transaction: rollback VM creation if storage registration failed
            if vm_id is not None:
                LOG.warning(
                    f"Storage registration failed for VM '{vm_name}', rolling back VM creation"
                )
                try:
                    self.state_manager.remove_vm(vm_name)
                    LOG.debug(f"Rolled back VM creation: '{vm_name}'")
                except Exception as rollback_error:
                    LOG.error(
                        f"Failed to rollback VM creation for '{vm_name}': {rollback_error}"
                    )
            raise

    def close(self) -> None:
        """
        Close database connection used by storage registry.

        Purpose: Clean up database resources to prevent ResourceWarnings.
        This should be called when the VMLifecycleManager is no longer needed.

        Note: The connection is created in __init__ and stored in self._db_conn.
        """
        if hasattr(self, '_db_conn') and self._db_conn:
            try:
                self._db_conn.close()
                LOG.debug("VMLifecycleManager database connection closed")
            except Exception as e:
                LOG.debug(f"Error closing VMLifecycleManager connection: {e}")

    def __del__(self) -> None:
        """
        Destructor to ensure database connection is closed.

        Purpose: Safety net for resource cleanup during garbage collection.
        Prefer explicit close() calls over relying on __del__.
        """
        try:
            self.close()
        except Exception:
            # Ignore errors during cleanup
            pass
