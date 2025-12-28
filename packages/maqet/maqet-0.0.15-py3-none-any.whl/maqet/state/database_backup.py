"""
Database Backup Module

Handles backup and restore operations for the MAQET state database.
Extracted from StateManager to separate concerns.
"""

import queue
import shutil
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable

from maqet.exceptions import StateError
from maqet.logger import LOG


class DatabaseBackup:
    """
    Manages database backup and restore operations.

    Handles:
    - Automatic timestamped backups using SQLite's backup API
    - Manual backups to specific paths
    - Database restoration from backups
    - Cleanup of old automatic backups
    - Proper connection pool management during operations
    """

    def __init__(
        self,
        db_path: Path,
        backup_dir: Path,
        pool_lock: threading.Lock,
        connection_pool: queue.Queue,
        reset_pool_initialized: Callable[[], None],
        get_schema_version: Callable[[], int],
        setup_database_optimizations: Callable[[], None],
    ) -> None:
        """
        Initialize DatabaseBackup.

        Args:
            db_path: Path to the database file
            backup_dir: Directory where backups are stored
            pool_lock: Lock for connection pool synchronization
            connection_pool: Queue containing pooled connections
            reset_pool_initialized: Callable to reset pool initialization flag
            get_schema_version: Callable to get current schema version
            setup_database_optimizations: Callable to reinitialize database after restore
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        self._pool_lock = pool_lock
        self._connection_pool = connection_pool
        self._reset_pool_initialized = reset_pool_initialized
        self._get_schema_version = get_schema_version
        self._setup_database_optimizations = setup_database_optimizations

    def create_auto_backup(self) -> Path:
        """
        Create timestamped database backup using SQLite's backup API.

        Internal method for automatic backups (e.g., before migrations).
        Uses SQLite's native backup() method which correctly handles WAL mode
        and allows safe concurrent writes during backup.

        Returns:
            Path to backup file

        Raises:
            StateError: If backup fails
        """
        try:
            # Create backups directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Generate timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            schema_version = self._get_schema_version()
            backup_filename = f"instances_v{schema_version}_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename

            # Use SQLite's backup API for safe, consistent backups
            # This method:
            # - Handles WAL mode correctly (no manual checkpoint needed)
            # - Allows concurrent writes during backup
            # - Ensures transactional consistency
            # - Is the recommended approach per SQLite documentation
            source = None
            dest = None

            try:
                source = sqlite3.connect(str(self.db_path))
                dest = sqlite3.connect(str(backup_path))

                # Perform the backup using SQLite's backup API
                source.backup(dest)
                dest.commit()
            finally:
                # Always close connections, even if backup fails
                if source:
                    source.close()
                if dest:
                    dest.close()

            LOG.info(f"Database backed up to {backup_path}")

            # Cleanup old backups after creating new one
            self._cleanup_old_backups()

            return backup_path

        except Exception as e:
            raise StateError(f"Failed to backup database: {e}")

    def backup(self, backup_path: Path) -> None:
        """
        Create database backup with schema to specified path.

        Purpose: Allow database restoration for disaster recovery.
        Edge case: Backup must include schema, not just data.

        Args:
            backup_path: Path where backup should be created

        Raises:
            StateError: If backup fails
        """
        try:
            # Close any open connections from pool
            with self._pool_lock:
                while not self._connection_pool.empty():
                    try:
                        conn = self._connection_pool.get_nowait()
                        conn.close()
                    except Exception:
                        pass
                self._reset_pool_initialized()

            # Copy database file (includes schema and data)
            shutil.copy2(str(self.db_path), str(backup_path))

            # If using WAL mode, also backup WAL file
            wal_path = Path(f"{self.db_path}-wal")
            if wal_path.exists():
                shutil.copy2(str(wal_path), f"{backup_path}-wal")

            LOG.info(f"Database backed up to {backup_path}")

        except Exception as e:
            raise StateError(f"Failed to backup database: {e}")

    def restore(self, backup_path: Path) -> None:
        """
        Restore database from backup.

        Purpose: Recover from database corruption or data loss.
        Can fail: Yes, if backup file is invalid.

        Args:
            backup_path: Path to backup file to restore from

        Raises:
            StateError: If backup file is invalid or restore fails
        """
        # Verify backup exists and is valid SQLite database
        if not backup_path.exists():
            raise StateError(f"Backup file not found: {backup_path}")

        # Verify it's a valid SQLite database
        try:
            conn = sqlite3.connect(str(backup_path))
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            conn.close()
        except sqlite3.DatabaseError as e:
            raise StateError(f"Invalid backup database: {e}")

        # Close all connections from pool
        with self._pool_lock:
            while not self._connection_pool.empty():
                try:
                    conn = self._connection_pool.get_nowait()
                    conn.close()
                except Exception:
                    pass
            self._reset_pool_initialized()

        # Restore backup
        shutil.copy2(str(backup_path), str(self.db_path))

        # Restore WAL file if exists
        backup_wal = backup_path.parent / f"{backup_path.name}-wal"
        if backup_wal.exists():
            shutil.copy2(str(backup_wal), f"{self.db_path}-wal")

        # Reinitialize connection pool
        self._setup_database_optimizations()

        LOG.info(f"Database restored from {backup_path}")

    def _cleanup_old_backups(self, keep: int = 5) -> None:
        """
        Remove old automatic backups, keeping only the most recent ones.

        Purpose: Prevent unlimited backup accumulation over time.

        Args:
            keep: Number of recent backups to keep (default: 5)
        """
        try:
            # Only cleanup auto-generated backups (instances_v*_*.db pattern)
            backup_files = sorted(
                self.backup_dir.glob("instances_v*_*.db"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            # Remove old backups beyond the keep limit
            for old_backup in backup_files[keep:]:
                try:
                    old_backup.unlink()
                    # Also remove associated WAL file if it exists
                    wal_file = Path(f"{old_backup}-wal")
                    if wal_file.exists():
                        wal_file.unlink()
                    LOG.debug(f"Removed old backup: {old_backup}")
                except Exception as e:
                    LOG.warning(f"Failed to remove old backup {old_backup}: {e}")

        except Exception as e:
            # Don't fail the backup operation if cleanup fails
            LOG.warning(f"Failed to cleanup old backups: {e}")
