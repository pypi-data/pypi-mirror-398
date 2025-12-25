"""
State Manager

Manages VM instance state using SQLite backend with XDG directory compliance.
Provides persistent storage for VM definitions, process tracking, and session management.

"""

# NOTE: Current name vs id design is optimal: UUID primary keys for internal
# use,
# human-readable names for CLI. This provides both uniqueness and usability.
import os
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from .constants import Database as DBConstants
from .constants import Intervals, Retries, Timeouts
from .exceptions import MigrationError, StateError
from .logger import LOG
from .state.database_backup import DatabaseBackup
from .state.migration_runner import MigrationRunner
from .state.vm_repository import VMRepository
from .utils.paths import ensure_path
from .utils.process_validation import validate_pid_exists

# Optional dependency - imported inline with fallback
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # psutil is optional - only needed for enhanced process validation
    # Install with: pip install psutil
    # Without psutil, basic PID tracking still works but lacks ownership checks


# Database migrations - simple functions approach
# Each migration is a standalone function that performs schema changes.
# Migrations are registered in MIGRATIONS dict and applied sequentially.


def _get_existing_columns(conn: sqlite3.Connection) -> List[str]:
    """
    Get list of existing columns in vm_instances table.

    Helper function used by migrations to check column existence.

    Args:
        conn: SQLite database connection

    Returns:
        List of column names
    """
    cursor = conn.execute("PRAGMA table_info(vm_instances)")
    return [row[1] for row in cursor.fetchall()]


def migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """
    Migration v1 -> v2: Add runner_pid column.

    Adds runner_pid column for tracking per-VM process PIDs.
    Only adds column if it doesn't already exist (idempotent).

    Args:
        conn: SQLite database connection
    """
    existing_columns = _get_existing_columns(conn)

    if "runner_pid" not in existing_columns:
        LOG.info("Migration v1->v2: Adding runner_pid column")
        conn.execute("ALTER TABLE vm_instances ADD COLUMN runner_pid INTEGER")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vm_runner_pid ON vm_instances(runner_pid)")


def migrate_v2_to_v3(conn: sqlite3.Connection) -> None:
    """
    Migration v2 -> v3: Add auth_secret column.

    Adds auth_secret column for socket authentication and generates
    secrets for existing VMs. Only runs if column doesn't exist.

    Args:
        conn: SQLite database connection
    """
    existing_columns = _get_existing_columns(conn)

    if "auth_secret" not in existing_columns:
        import secrets

        LOG.info("Migration v2->v3: Adding auth_secret column")
        conn.execute("ALTER TABLE vm_instances ADD COLUMN auth_secret TEXT")

        # Generate secrets for existing VMs
        cursor = conn.execute("SELECT id FROM vm_instances")
        for (vm_id,) in cursor.fetchall():
            auth_secret = secrets.token_hex(32)  # 256-bit secret
            conn.execute(
                "UPDATE vm_instances SET auth_secret = ? WHERE id = ?",
                (auth_secret, vm_id)
            )

        LOG.info("Migration v2->v3: Generated secrets for existing VMs")


def migrate_v3_to_v4(conn: sqlite3.Connection) -> None:
    """
    Migration v3 -> v4: Remove auth_secret column.

    Removes auth_secret column as secrets are now ephemeral (file-based).
    SQLite doesn't support DROP COLUMN, so we recreate the table.
    Only runs if auth_secret column exists.

    Args:
        conn: SQLite database connection
    """
    existing_columns = _get_existing_columns(conn)

    if "auth_secret" not in existing_columns:
        return

    LOG.info("Migration v3->v4: Removing auth_secret column")

    has_runner_pid = "runner_pid" in existing_columns

    # SQLite doesn't support DROP COLUMN, so recreate table
    conn.execute("""
        CREATE TABLE vm_instances_new (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            config_path TEXT,
            config_data TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'created',
            pid INTEGER,
            runner_pid INTEGER,
            socket_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Copy data based on available columns
    if has_runner_pid:
        conn.execute("""
            INSERT INTO vm_instances_new
            SELECT id, name, config_path, config_data, status, pid, runner_pid, socket_path, created_at, updated_at
            FROM vm_instances
        """)
    else:
        conn.execute("""
            INSERT INTO vm_instances_new (id, name, config_path, config_data, status, pid, runner_pid, socket_path, created_at, updated_at)
            SELECT id, name, config_path, config_data, status, pid, NULL, socket_path, created_at, updated_at
            FROM vm_instances
        """)

    # Replace old table
    conn.execute("DROP TABLE vm_instances")
    conn.execute("ALTER TABLE vm_instances_new RENAME TO vm_instances")

    # Recreate indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vm_name ON vm_instances(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vm_status ON vm_instances(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vm_pid ON vm_instances(pid)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vm_runner_pid ON vm_instances(runner_pid)")

    # Recreate trigger
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS update_timestamp
            AFTER UPDATE ON vm_instances
        BEGIN
            UPDATE vm_instances SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
    """)

    LOG.info("Migration v3->v4: Removed auth_secret column (secrets now ephemeral)")


def migrate_v4_to_v5(conn: sqlite3.Connection) -> None:
    """
    Migration v4 -> v5: Add qmp_socket_path column.

    Adds qmp_socket_path column for cross-process QMP communication.
    Only adds column if it doesn't already exist (idempotent).

    Args:
        conn: SQLite database connection
    """
    existing_columns = _get_existing_columns(conn)

    if "qmp_socket_path" not in existing_columns:
        LOG.info("Migration v4->v5: Adding qmp_socket_path column")
        # Add qmp_socket_path column (nullable for backward compatibility)
        conn.execute("ALTER TABLE vm_instances ADD COLUMN qmp_socket_path TEXT")

        # Create index for fast lookups by QMP socket path
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vms_qmp_socket ON vm_instances(qmp_socket_path)")


def migrate_v5_to_v6(conn: sqlite3.Connection) -> None:
    """
    Migration v5 -> v6: Add storage_registry table.

    Creates storage_registry table for tracking VM storage files.
    This enables transactional storage management and prevents orphaned disk images.

    Args:
        conn: SQLite database connection
    """
    LOG.info("Migration v5->v6: Adding storage_registry table")

    # Check if table already exists (idempotent)
    cursor = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='storage_registry'
    """)

    if cursor.fetchone() is not None:
        LOG.info("Migration v5->v6: storage_registry table already exists, skipping")
        return

    # Create storage_registry table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS storage_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vm_name TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            storage_type TEXT NOT NULL,
            size_bytes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified TIMESTAMP,
            FOREIGN KEY (vm_name) REFERENCES vm_instances(name) ON DELETE CASCADE,
            UNIQUE(vm_name, storage_path)
        )
    """)

    # Create indexes for fast lookups
    conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_vm ON storage_registry(vm_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_path ON storage_registry(storage_path)")

    LOG.info("Migration v5->v6: storage_registry table created successfully")


MIGRATIONS: Dict[int, callable] = {
    2: migrate_v1_to_v2,
    3: migrate_v2_to_v3,
    4: migrate_v3_to_v4,
    5: migrate_v4_to_v5,
    6: migrate_v5_to_v6,
}


@dataclass
class VMInstance:
    """Represents a VM instance in the state database."""

    id: str
    name: str
    config_path: Optional[str]
    config_data: Dict[str, Any]
    status: str  # 'created', 'running', 'stopped', 'failed'
    pid: Optional[int]  # QEMU process PID
    runner_pid: Optional[int] = None  # VM runner process PID (per-VM architecture)
    socket_path: Optional[str] = None
    qmp_socket_path: Optional[str] = None  # QMP socket path for cross-process communication
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    auth_secret: Optional[str] = None  # DEPRECATED: Now ephemeral (file-based), for backward compat only


class XDGDirectories:
    """
    XDG Base Directory Specification compliance for MAQET directories.

    Provides proper directory structure following Linux standards.

    Supports directory overrides with proper precedence:
    1. CLI flags (highest priority) - passed as custom_*_dir parameters
    2. Environment variables (XDG_DATA_HOME, XDG_CONFIG_HOME, XDG_RUNTIME_DIR)
    3. XDG defaults (lowest priority)
    """

    def __init__(
        self,
        custom_data_dir: Optional[Path] = None,
        custom_config_dir: Optional[Path] = None,
        custom_runtime_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize XDG directories.

        Args:
            custom_data_dir: Override default data directory
            custom_config_dir: Override default config directory
            custom_runtime_dir: Override default runtime directory
        """
        self._custom_data_dir = custom_data_dir
        self._custom_config_dir = custom_config_dir
        self._custom_runtime_dir = custom_runtime_dir
        self._ensure_directories()

    @property
    def data_dir(self) -> Path:
        """
        Get XDG data directory (~/.local/share/maqet/).

        Precedence: custom_data_dir > XDG_DATA_HOME > ~/.local/share/maqet
        """
        if self._custom_data_dir:
            return self._custom_data_dir
        base = os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        return Path(base) / "maqet"

    @property
    def runtime_dir(self) -> Path:
        """
        Get XDG runtime directory (/run/user/1000/maqet/).

        Precedence: custom_runtime_dir > XDG_RUNTIME_DIR > /tmp/maqet-{uid}
        """
        if self._custom_runtime_dir:
            return self._custom_runtime_dir
        base = os.getenv("XDG_RUNTIME_DIR", f"/tmp/maqet-{os.getuid()}")
        return Path(base) / "maqet"

    @property
    def config_dir(self) -> Path:
        """
        Get XDG config directory (~/.config/maqet/).

        Precedence: custom_config_dir > XDG_CONFIG_HOME > ~/.config/maqet
        """
        if self._custom_config_dir:
            return self._custom_config_dir
        base = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(base) / "maqet"

    @property
    def database_path(self) -> Path:
        """Get database file path."""
        return self.data_dir / "instances.db"

    @property
    def vm_definitions_dir(self) -> Path:
        """Get VM definitions directory."""
        return self.data_dir / "vm-definitions"

    @property
    def sockets_dir(self) -> Path:
        """Get QMP sockets directory."""
        return self.runtime_dir / "sockets"

    @property
    def pids_dir(self) -> Path:
        """Get PID files directory."""
        return self.runtime_dir / "pids"

    @property
    def locks_dir(self) -> Path:
        """Get lock files directory for VM start operations."""
        return self.runtime_dir / "locks"

    @property
    def templates_dir(self) -> Path:
        """Get VM templates directory."""
        return self.config_dir / "templates"

    def _ensure_directories(self) -> None:
        """Create XDG-compliant directory structure."""
        dirs = [
            self.data_dir,
            self.vm_definitions_dir,
            self.runtime_dir,
            self.sockets_dir,
            self.pids_dir,
            self.locks_dir,
            self.config_dir,
            self.templates_dir,
        ]

        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)


class StateManager:
    """
    Manages VM instance state with SQLite backend.

    Provides persistent storage for VM definitions, process tracking,
    and session management following XDG directory standards.

    # NOTE: Good - XDG compliance ensures proper file locations across
    # different
    # Linux distributions and user configurations. Respects user preferences.
    # NOTE: Cleanup of stale socket/PID files IS implemented in
    # cleanup_dead_processes(),
    #       which runs on startup and cleans orphaned processes.

    # ARCHITECTURAL DECISION: Database Migration Strategy
    # ================================================
    # Current: No migration system - schema changes require manual database
    # deletion
    # Impact: Users must delete ~/.local/share/maqet/instances.db after
    # upgrades that change schema
    #
    # Future Migration Strategy (when needed):
    #   1. Version table to track schema version (e.g., schema_version INTEGER)
    #   2. Migration scripts for each schema change:
    #      - Option A: Embedded Python migrations (simple, no dependencies)
    #      - Option B: alembic/yoyo-migrations (robust, industry-standard)
    # 3. Automatic backup before migration
    # (~/.local/share/maqet/backups/instances.db.YYYYMMDD)
    #   4. Rollback capability for failed migrations
    #   5. Migration status logging (success/failure/skipped)
    #
    # Decision: Deferred until schema stabilizes (currently in rapid
    # development)
    # Workaround: Document breaking changes in release notes, instruct users to
    # delete DB
    # Timeline: Implement before 1.0 release when API/schema stabilizes
    """

    def __init__(
        self,
        data_dir: Optional[Union[str, Path]] = None,
        config_dir: Optional[Union[str, Path]] = None,
        runtime_dir: Optional[Union[str, Path]] = None,
        auto_migrate: bool = True,
    ):
        """
        Initialize state manager.

        Args:
            data_dir: Override default data directory
            config_dir: Override default config directory
            runtime_dir: Override default runtime directory
            auto_migrate: Automatically apply pending migrations (default: True)
        """
        # Convert string paths to Path objects for XDGDirectories
        custom_data_path = ensure_path(data_dir) if data_dir else None
        custom_config_path = ensure_path(config_dir) if config_dir else None
        custom_runtime_path = ensure_path(runtime_dir) if runtime_dir else None

        self.xdg = XDGDirectories(
            custom_data_dir=custom_data_path,
            custom_config_dir=custom_config_path,
            custom_runtime_dir=custom_runtime_path,
        )

        # Connection pool for read operations
        self._pool_size = 5
        self._connection_pool: Queue = Queue(maxsize=self._pool_size)
        self._pool_lock = threading.Lock()
        self._pool_initialized = False

        # Connection lock for thread-safe database access
        self._connection_lock = threading.Lock()

        # Initialize database tables first (uses direct DB access for schema version)
        self._init_database()

        # Setup database optimizations for concurrent access
        self._setup_database_optimizations()

        # Initialize extracted components AFTER database is ready
        self._vm_repository = VMRepository(self._get_connection, self._get_pooled_connection)

        # Initialize migration runner first (needed by database backup)
        self._migration_runner = MigrationRunner(
            get_connection=self._get_connection,
            get_pooled_connection=self._get_pooled_connection,
            backup=None,  # Will be set after DatabaseBackup is created
            migrations=MIGRATIONS,
        )

        # Initialize database backup (needs migration runner for schema version)
        self._database_backup = DatabaseBackup(
            db_path=self.xdg.database_path,
            backup_dir=self.xdg.data_dir / "backups",
            pool_lock=self._pool_lock,
            connection_pool=self._connection_pool,
            reset_pool_initialized=lambda: setattr(self, '_pool_initialized', False),
            get_schema_version=self._migration_runner.get_version,
            setup_database_optimizations=self._setup_database_optimizations,
        )

        # Now set the backup reference in migration runner
        self._migration_runner._backup = self._database_backup

        # Automatically apply pending migrations if enabled
        if auto_migrate:
            self._auto_migrate()

        # Automatically clean up dead processes and stale files on startup
        cleaned = self.cleanup_dead_processes()
        if cleaned:
            LOG.debug(f"Startup cleanup completed: {len(cleaned)} VMs cleaned")

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS vm_instances (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    config_path TEXT,
                    config_data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'created',
                    pid INTEGER,
                    socket_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_vm_name ON vm_instances(name);
                CREATE INDEX IF NOT EXISTS idx_vm_status ON vm_instances(status);
                CREATE INDEX IF NOT EXISTS idx_vm_pid ON vm_instances(pid);

                CREATE TRIGGER IF NOT EXISTS update_timestamp
                    AFTER UPDATE ON vm_instances
                BEGIN
                    UPDATE vm_instances SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = NEW.id;
                END;

                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                );
            """
            )

            # Initialize schema version if this is a new database
            current_version = self.get_schema_version()
            if current_version == 0:
                self._set_schema_version(1, "Initial schema")

    def _setup_database_optimizations(self) -> None:
        """
        Configure SQLite for concurrent access.

        Purpose: Prevent database corruption under high concurrency loads.

        Optimizations:
        - WAL mode: Write-Ahead Logging for better concurrency
        - NORMAL synchronous: Balance between safety and performance
        - Busy timeout: Retry on lock contention instead of failing immediately
        - Cache size: Larger cache for better performance

        Edge cases:
        - WAL mode requires SQLite 3.7.0+ (widely available)
        - NORMAL synchronous is safe with WAL mode
        - Busy timeout helps with transient lock contention
        """
        with self._get_connection() as conn:
            # Enable Write-Ahead Logging for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")

            # Set synchronous mode (NORMAL is safe with WAL mode)
            conn.execute("PRAGMA synchronous=NORMAL")

            # Set busy timeout (wait up to 5 seconds for locks)
            conn.execute("PRAGMA busy_timeout=5000")

            # Increase cache size for better performance
            conn.execute("PRAGMA cache_size=-64000")  # 64MB

    def _create_connection(self) -> sqlite3.Connection:
        """Create new database connection with proper settings."""
        conn = sqlite3.connect(
            str(self.xdg.database_path),
            check_same_thread=False,  # Thread-safe with WAL mode
            timeout=Timeouts.DB_LOCK,
        )
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA journal_mode={DBConstants.JOURNAL_MODE}")
        conn.execute(f"PRAGMA synchronous={DBConstants.SYNCHRONOUS}")
        conn.execute(f"PRAGMA foreign_keys={DBConstants.FOREIGN_KEYS}")
        return conn

    def _initialize_pool(self) -> None:
        """Pre-create connection pool for read operations."""
        with self._pool_lock:
            if self._pool_initialized:
                return

            for _ in range(self._pool_size):
                conn = self._create_connection()
                self._connection_pool.put(conn)

            self._pool_initialized = True

    @contextmanager
    def _get_pooled_connection(self, readonly: bool = True) -> Generator[sqlite3.Connection, None, None]:
        """
        Get connection from pool for read operations.

        For write operations, creates new connection to avoid lock contention.

        Args:
            readonly: If True, use pooled connection; if False, create dedicated connection

        Yields:
            sqlite3.Connection: Database connection
        """
        if not readonly:
            # Write operations: use dedicated connection
            conn = self._create_connection()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            return

        # Read operations: use pooled connection
        if not self._pool_initialized:
            self._initialize_pool()

        try:
            # Get connection from pool (non-blocking with timeout)
            conn = self._connection_pool.get(timeout=1.0)
            temp_conn = False
        except Empty:
            # Pool exhausted - create temporary connection
            conn = self._create_connection()
            temp_conn = True

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if temp_conn:
                conn.close()
            else:
                # Return to pool
                self._connection_pool.put(conn)

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get database connection with proper locking.

        Purpose: Ensure thread-safe database access.
        Can fail: Yes, if database is locked beyond busy_timeout.

        Uses connection lock to serialize database access and prevent
        concurrent write conflicts. Works with WAL mode for better concurrency.

        Yields:
            sqlite3.Connection: Database connection

        Raises:
            DatabaseError: If connection fails
            DatabaseLockError: If database remains locked
        """
        with self._connection_lock:
            conn = sqlite3.connect(
                str(self.xdg.database_path),
                timeout=5.0,  # Wait up to 5 seconds for lock
                isolation_level="DEFERRED",  # Don't lock until write
            )
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def create_vm(
        self,
        name: str,
        config_data: Dict[str, Any],
        config_path: Optional[str] = None,
    ) -> str:
        """
        Create a new VM instance.

        Args:
            name: VM name (must be unique)
            config_data: VM configuration dictionary
            config_path: Optional path to config file

        Returns:
            VM instance ID

        Raises:
            StateError: If validation fails or DB operation fails
        """
        return self._vm_repository.create_vm(name, config_data, config_path, get_vm_callback=self.get_vm)

    def get_vm(self, identifier: str) -> Optional[VMInstance]:
        """
        Get VM instance by ID or name.

        Optimized to use indexes by trying ID lookup first (PRIMARY KEY),
        then name lookup (idx_vm_name index) if not found.

        Args:
            identifier: VM ID or name

        Returns:
            VM instance or None if not found
        """
        return self._vm_repository.get_vm(identifier)

    def list_vms(
        self, status_filter: Optional[str] = None
    ) -> List[VMInstance]:
        """
        List all VM instances.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of VM instances
        """
        return self._vm_repository.list_vms(status_filter)

    def _validate_pid_ownership(self, pid: int) -> None:
        """
        Validate that PID belongs to current user and is a QEMU process.

        Args:
            pid: Process ID to validate

        Raises:
            ValueError: If PID is invalid, not owned by user, or not a QEMU process
        """
        # psutil is optional - skip PID validation if not available
        if not PSUTIL_AVAILABLE:
            LOG.debug(
                "psutil not available, skipping PID ownership validation. "
                "Install psutil for enhanced security checks."
            )
            return

        try:
            process = psutil.Process(pid)

            # Check if process is owned by current user (Unix only)
            if hasattr(os, "getuid"):
                current_uid = os.getuid()
                process_uid = process.uids().real

                if process_uid != current_uid:
                    raise ValueError(
                        f"PID {pid} is owned by UID {
                            process_uid}, not current user (UID {current_uid}). "
                        f"Refusing to manage process owned by another user for security reasons."
                    )

            # Verify it's a QEMU process
            cmdline = process.cmdline()
            if not cmdline:
                raise ValueError(
                    f"PID {
                        pid} has no command line. Cannot verify it's a QEMU process."
                )

            # Check if command contains 'qemu' (case insensitive)
            is_qemu = any("qemu" in arg.lower() for arg in cmdline)
            if not is_qemu:
                LOG.warning(
                    f"PID {pid} does not appear to be a QEMU process. "
                    f"Command: {' '.join(cmdline[:3])}..."
                )
                # We warn but don't block, as the binary might be renamed

        except psutil.NoSuchProcess:
            raise ValueError(f"PID {pid} does not exist")
        except psutil.AccessDenied:
            raise ValueError(
                f"Access denied when checking PID {
                    pid}. Cannot verify ownership."
            )

    def update_vm_status(
        self,
        identifier: str,
        status: str,
        pid: Optional[int] = None,
        runner_pid: Optional[int] = None,
        socket_path: Optional[str] = None,
        qmp_socket_path: Optional[str] = None,
    ) -> bool:
        """
        Update VM status and process information.

        Optimized to use indexes by trying ID lookup first (PRIMARY KEY),
        then name lookup (idx_vm_name index) if not found.

        Args:
            identifier: VM ID or name
            status: New status
            pid: QEMU process ID (if running)
            runner_pid: VM runner process ID (if running)
            socket_path: QMP socket path (if running)
            qmp_socket_path: QMP socket path for cross-process communication

        Returns:
            True if updated, False if VM not found

        Raises:
            ValueError: If PID ownership validation fails
        """
        return self._vm_repository.update_vm_status(
            identifier=identifier,
            status=status,
            pid=pid,
            runner_pid=runner_pid,
            socket_path=socket_path,
            qmp_socket_path=qmp_socket_path,
            validate_pid_callback=self._validate_pid_ownership,
        )

    def batch_update_vm_statuses(
        self,
        updates: Dict[str, Tuple[str, Optional[int], Optional[int], Optional[str]]]
    ) -> int:
        """Update multiple VM statuses in a single transaction.

        Efficiently updates status, pid, runner_pid, and socket_path for multiple VMs
        in one database transaction, avoiding N+1 query pattern.

        Args:
            updates: Dict mapping VM name to tuple of (status, pid, runner_pid, socket_path)

        Returns:
            Number of rows updated

        Raises:
            StateError: If database operation fails
        """
        return self._vm_repository.batch_update_vm_statuses(updates)

    def remove_vm(self, identifier: str) -> bool:
        """
        Remove VM instance from database.

        Optimized to use indexes by trying ID lookup first (PRIMARY KEY),
        then name lookup (idx_vm_name index) if not found.

        Args:
            identifier: VM ID or name

        Returns:
            True if removed, False if VM not found
        """
        return self._vm_repository.remove_vm(identifier)

    def cleanup_dead_processes(self) -> List[str]:
        """
        Clean up VMs with dead processes and stale files.

        This method:
        - Checks all VMs marked as 'running' in database
        - Verifies their processes are actually alive
        - Updates status to 'stopped' for dead processes
        - Removes stale socket and PID files

        Returns:
            List of VM IDs that were cleaned up
        """
        cleaned_up = []
        running_vms = self.list_vms(status_filter="running")

        for vm in running_vms:
            if vm.pid and not self._is_process_alive(vm.pid):
                LOG.info(
                    f"Cleaning up dead VM {
                        vm.name} (ID: {vm.id}, PID: {vm.pid})"
                )

                # Update database status
                self.update_vm_status(
                    vm.id, "stopped", pid=None, socket_path=None
                )

                # Clean up stale socket file
                socket_path = self.get_socket_path(vm.id)
                if socket_path.exists():
                    try:
                        socket_path.unlink()
                        LOG.debug(f"Removed stale socket: {socket_path}")
                    except OSError as e:
                        LOG.warning(
                            f"Failed to remove stale socket {socket_path}: {e}"
                        )

                # Clean up stale PID file
                pid_path = self.get_pid_path(vm.id)
                if pid_path.exists():
                    try:
                        pid_path.unlink()
                        LOG.debug(f"Removed stale PID file: {pid_path}")
                    except OSError as e:
                        LOG.warning(
                            f"Failed to remove stale PID file {pid_path}: {e}"
                        )

                cleaned_up.append(vm.id)

        if cleaned_up:
            LOG.info(
                f"Cleaned up {len(cleaned_up)} dead VM(s): {
                    ', '.join(cleaned_up)}"
            )

        return cleaned_up

    def _is_process_alive(self, pid: int) -> bool:
        """Check if process is still running."""
        return validate_pid_exists(pid, process_name="process", log_permission_warning=False)

    def get_socket_path(self, vm_id: str) -> Path:
        """Get QMP socket path for VM."""
        return self.xdg.sockets_dir / f"{vm_id}.sock"

    def get_pid_path(self, vm_id: str) -> Path:
        """Get PID file path for VM."""
        return self.xdg.pids_dir / f"{vm_id}.pid"

    def get_lock_path(self, vm_id: str) -> Path:
        """Get lock file path for VM start operations."""
        return self.xdg.locks_dir / f"{vm_id}.lock"

    def update_vm_config(
        self, identifier: str, new_config: Dict[str, Any]
    ) -> bool:
        """
        Update VM configuration in database.

        Optimized to use indexes by trying ID lookup first (PRIMARY KEY),
        then name lookup (idx_vm_name index) if not found.

        Args:
            identifier: VM name or ID
            new_config: New configuration data

        Returns:
            True if update successful, False if VM not found

        Raises:
            StateError: If database operation fails
        """
        return self._vm_repository.update_vm_config(identifier, new_config)

    def get_schema_version(self) -> int:
        """
        Get current database schema version.

        Returns:
            Current schema version, or 0 if schema_version table doesn't exist
        """
        # Check if migration_runner is initialized (may be called during __init__)
        if hasattr(self, '_migration_runner') and self._migration_runner is not None:
            return self._migration_runner.get_version()

        # Fallback to direct DB access during initialization
        try:
            with self._get_pooled_connection(readonly=True) as conn:
                result = conn.execute(
                    "SELECT MAX(version) FROM schema_version"
                ).fetchone()
                return result[0] if result[0] is not None else 0
        except Exception:
            # schema_version table doesn't exist (pre-migration database)
            return 0

    def _set_schema_version(self, version: int, description: str = "") -> None:
        """
        Set database schema version.

        Args:
            version: Schema version number
            description: Optional description of the schema version
        """
        # Check if migration_runner is initialized (may be called during __init__)
        if hasattr(self, '_migration_runner') and self._migration_runner is not None:
            self._migration_runner._set_version(version, description)
            return

        # Fallback to direct DB access during initialization
        with self._get_pooled_connection(readonly=False) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO schema_version (version, description, applied_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (version, description),
            )

    def _backup_database_auto(self) -> Path:
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
        return self._database_backup.create_auto_backup()

    def backup_database(self, backup_path: Union[str, Path]) -> None:
        """
        Create database backup with schema to specified path.

        Purpose: Allow database restoration for disaster recovery.
        Edge case: Backup must include schema, not just data.

        Args:
            backup_path: Path where backup should be created

        Raises:
            StateError: If backup fails
        """
        backup_path = ensure_path(backup_path)  # Convert to Path at boundary
        self._database_backup.backup(backup_path)

    def restore_database(self, backup_path: Union[str, Path]) -> None:
        """
        Restore database from backup.

        Purpose: Recover from database corruption or data loss.
        Can fail: Yes, if backup file is invalid.

        Args:
            backup_path: Path to backup file to restore from

        Raises:
            StateError: If backup file is invalid or restore fails
        """
        backup_path = ensure_path(backup_path)  # Convert to Path at boundary
        self._database_backup.restore(backup_path)

    def run_migrations(self) -> None:
        """
        Run all pending database migrations.

        Migrations are applied sequentially from current version to target version.
        Database is automatically backed up before applying migrations.

        Raises:
            StateError: If migration fails
        """
        self._migration_runner.run_migrations()

    def _apply_migration(self, version: int, migration_func: callable) -> None:
        """
        Apply a single database migration.

        Args:
            version: Target schema version
            migration_func: Migration function to execute

        Raises:
            StateError: If migration fails
        """
        self._migration_runner._apply_migration(version, migration_func)

    def _needs_migration(self) -> bool:
        """
        Check if database needs migration.

        Returns:
            True if there are pending migrations, False otherwise
        """
        return self._migration_runner.needs_migration()

    def _apply_migrations(self) -> None:
        """
        Apply all pending migrations.

        This is a simplified wrapper around run_migrations() for auto-migration.

        Raises:
            MigrationError: If migration fails
        """
        self._migration_runner._apply_migrations()

    def _auto_migrate(self) -> None:
        """
        Automatically apply pending migrations on startup.

        This method is called during StateManager initialization to ensure
        the database schema is up to date. If migration fails, it exits
        with a user-friendly error message.

        Raises:
            MigrationError: If migration fails (caught and handled with sys.exit)
        """
        self._migration_runner.auto_migrate()

    def close(self) -> None:
        """
        Close all database connections in the connection pool.

        Purpose: Properly clean up database resources to prevent ResourceWarnings.
        This method should be called when the StateManager instance is no longer needed,
        especially in test environments.

        Process:
        1. Acquire pool lock to prevent concurrent access
        2. Initialize pool if needed (to force connection creation)
        3. Close all connections in the pool
        4. Mark pool as uninitialized
        5. Connections are garbage collected after close

        Thread-safe: Uses _pool_lock to ensure no connections are being used during cleanup.

        Example:
            state_manager = StateManager()
            try:
                # Use state_manager
                state_manager.create_vm(...)
            finally:
                state_manager.close()

        Note: After calling close(), the StateManager instance can still be used.
              The connection pool will be re-initialized on next database access.
        """
        with self._pool_lock:
            # Initialize pool first if not already initialized
            # This ensures we close any connections that might have been created
            if not self._pool_initialized:
                # No pool to close
                LOG.debug("StateManager pool not initialized, nothing to close")
                return

            # Close all connections in the pool
            closed_count = 0
            while not self._connection_pool.empty():
                try:
                    conn = self._connection_pool.get_nowait()
                    conn.close()
                    closed_count += 1
                except Exception as e:
                    # Log but don't fail - best effort cleanup
                    LOG.debug(f"Error closing pooled connection: {e}")

            # Mark pool as uninitialized
            self._pool_initialized = False
            LOG.debug(f"StateManager closed {closed_count} database connection(s)")

    def __del__(self) -> None:
        """
        Destructor to ensure database connections are closed.

        Purpose: Clean up resources when StateManager instance is garbage collected.
        This is a safety net for cases where close() is not explicitly called.

        Note: Relying on __del__ for cleanup is not ideal. Prefer explicit close() calls.
              This is mainly for test environments and unexpected shutdowns.
        """
        try:
            self.close()
        except Exception:
            # Ignore errors during cleanup - best effort only
            # Don't log here as logging might not be available during shutdown
            pass
