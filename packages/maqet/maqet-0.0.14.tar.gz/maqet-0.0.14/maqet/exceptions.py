"""
Maqet Exception Hierarchy

This module defines the complete exception hierarchy for maqet. All exceptions
inherit from MaqetError, enabling blanket exception handling while preserving
specific exception types for targeted error handling.

Exception Hierarchy:
    MaqetError (base)
    +-- ConfigurationError
    |   +-- ConfigFileNotFoundError
    |   +-- ConfigValidationError
    |   +-- InvalidConfigurationError
    +-- VMLifecycleError
    |   +-- VMNotFoundError
    |   +-- VMAlreadyExistsError
    |   +-- VMAlreadyRunningError
    |   +-- VMNotRunningError
    |   +-- VMStartError
    |   |   +-- QEMUProcessError
    |   +-- VMStopError
    |   +-- VMRunningError
    +-- QMPError
    |   +-- QMPConnectionError
    |   +-- QMPCommandError
    |   +-- QMPTimeoutError
    +-- StorageError
    |   +-- StorageDeviceNotFoundError
    |   +-- StorageCreationError
    |   +-- StorageValidationError
    +-- SnapshotError
    |   +-- SnapshotNotFoundError
    |   +-- SnapshotCreationError
    |   +-- SnapshotLoadError
    |   +-- SnapshotDeleteError
    +-- StateError
    |   +-- DatabaseError
    |   |   +-- DatabaseLockError
    |   +-- MigrationError
    +-- SecurityError
    +-- ProcessError
    |   +-- RunnerProcessError
    |   +-- RunnerSpawnError
    |   +-- ProcessNotFoundError
    |   +-- VMRunnerError
    +-- IPCError
    |   +-- IPCConnectionError
    |   +-- IPCTimeoutError
    |   +-- IPCCommandError
    +-- WaitTimeout

Usage Patterns:
    # Catch all maqet errors
    try:
        maqet.start("my-vm")
    except MaqetError as e:
        print(f"Maqet operation failed: {e}")

    # Catch specific error category
    try:
        maqet.create_snapshot("my-vm", "snap1")
    except SnapshotError as e:
        print(f"Snapshot operation failed: {e}")

    # Catch specific error type
    try:
        maqet.start("nonexistent-vm")
    except VMNotFoundError as e:
        print(f"VM not found: {e}")

    # Multiple exception handlers
    try:
        maqet.start("my-vm")
    except VMAlreadyRunningError:
        print("VM already running, continuing...")
    except VMStartError as e:
        print(f"Failed to start VM: {e}")
        raise
"""


class MaqetError(Exception):
    """Base exception for all maqet errors.

    All maqet-specific exceptions inherit from this class, allowing
    blanket exception handling while preserving specific exception
    types for targeted error handling.

    This exception should be caught when you want to handle any
    maqet error uniformly, or when you need to distinguish maqet
    errors from other Python exceptions.

    Example:
        >>> try:
        ...     maqet.start("my-vm")
        ... except MaqetError as e:
        ...     logger.error(f"Maqet operation failed: {e}")
        ...     # Handle any maqet error
        ... except Exception as e:
        ...     logger.error(f"Unexpected error: {e}")
        ...     # Handle non-maqet errors
    """


# Configuration Errors
class ConfigurationError(MaqetError):
    """Base class for configuration-related errors.

    Raised when VM configuration is invalid or contains conflicts.
    This exception is raised during VM initialization when:
    - Duplicate single-instance QEMU arguments are detected
    - Invalid argument combinations are present
    - Semantic configuration errors are found
    - YAML configuration contains invalid syntax or structure

    Example:
        >>> machine.handle_arguments([
        ...     {'display': 'gtk'},
        ...     {'display': 'sdl'},  # Duplicate!
        ... ])
        ConfigurationError: Duplicate single-instance argument '-display' detected...

        >>> try:
        ...     maqet.add_vm("my-vm", config_file="invalid.yaml")
        ... except ConfigurationError as e:
        ...     print(f"Config error: {e}")
    """


class ConfigFileNotFoundError(ConfigurationError):
    """Configuration file does not exist at specified path.

    Raised when attempting to load a VM configuration from a YAML
    file that cannot be found on the filesystem.

    Example:
        >>> maqet.add_vm("my-vm", config_file="/nonexistent/config.yaml")
        ConfigFileNotFoundError: Configuration file not found: /nonexistent/config.yaml

        >>> try:
        ...     maqet.add_vm("vm", config_file=missing_path)
        ... except ConfigFileNotFoundError:
        ...     print("Creating default config...")
        ...     maqet.add_vm("vm", config={})
    """


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed against schema or rules.

    Raised when configuration content is syntactically valid YAML
    but fails semantic validation (e.g., missing required fields,
    invalid values, type mismatches).

    Example:
        >>> maqet.add_vm("my-vm", config={'memory': 'invalid'})
        ConfigValidationError: memory must be an integer

        >>> config = {'machine': {'cpus': -1}}
        >>> maqet.add_vm("vm", config=config)
        ConfigValidationError: cpus must be positive integer
    """


class InvalidConfigurationError(ConfigurationError):
    """Configuration is malformed or contains invalid structure.

    Raised when configuration cannot be parsed or contains
    fundamentally invalid structure (e.g., malformed YAML,
    conflicting directives).

    Example:
        >>> maqet.add_vm("vm", config_file="malformed.yaml")
        InvalidConfigurationError: Invalid YAML syntax at line 5

        >>> config = {'qemu_args': 'should-be-list'}
        >>> maqet.add_vm("vm", config=config)
        InvalidConfigurationError: qemu_args must be a list
    """


# VM Lifecycle Errors
class VMLifecycleError(MaqetError):
    """Base class for VM lifecycle operation errors.

    Raised during VM lifecycle operations including creation,
    starting, stopping, and state transitions. Catch this exception
    to handle any VM lifecycle error uniformly.

    Example:
        >>> try:
        ...     maqet.start("my-vm")
        ... except VMLifecycleError as e:
        ...     print(f"VM lifecycle error: {e}")
    """


class VMNotFoundError(VMLifecycleError):
    """VM does not exist in the maqet database.

    Raised when attempting to operate on a VM that has not been
    added to maqet. The VM name may be misspelled or the VM
    may have been removed.

    Example:
        >>> maqet.start("nonexistent-vm")
        VMNotFoundError: VM 'nonexistent-vm' not found

        >>> try:
        ...     maqet.get_info("typo-vm")
        ... except VMNotFoundError:
        ...     print("VM not found, creating...")
        ...     maqet.add_vm("typo-vm", config={})
    """


class VMAlreadyExistsError(VMLifecycleError):
    """VM with this name already exists in the database.

    Raised when attempting to add a VM with a name that is
    already registered. VM names must be unique within maqet.

    Example:
        >>> maqet.add_vm("my-vm", config={})
        >>> maqet.add_vm("my-vm", config={})  # Duplicate!
        VMAlreadyExistsError: VM 'my-vm' already exists

        >>> try:
        ...     maqet.add_vm(vm_name, config)
        ... except VMAlreadyExistsError:
        ...     print(f"VM {vm_name} exists, removing first...")
        ...     maqet.remove_vm(vm_name)
        ...     maqet.add_vm(vm_name, config)
    """


class VMAlreadyRunningError(VMLifecycleError):
    """VM is already running.

    Raised when attempting to start a VM that is already in
    running state. This prevents duplicate VM instances.

    Example:
        >>> maqet.start("my-vm")
        >>> maqet.start("my-vm")  # Already running!
        VMAlreadyRunningError: VM 'my-vm' is already running

        >>> try:
        ...     maqet.start("my-vm")
        ... except VMAlreadyRunningError:
        ...     print("VM already running, continuing...")
    """


class VMNotRunningError(VMLifecycleError):
    """VM is not currently running.

    Raised when attempting an operation that requires the VM
    to be running (e.g., QMP commands, live snapshots) on a
    VM that is stopped.

    Example:
        >>> maqet.qmp_command("my-vm", "query-status")
        VMNotRunningError: VM 'my-vm' is not running

        >>> try:
        ...     maqet.create_live_snapshot("vm", "snap1")
        ... except VMNotRunningError:
        ...     print("Starting VM first...")
        ...     maqet.start("vm")
        ...     maqet.create_live_snapshot("vm", "snap1")
    """


class VMStartError(VMLifecycleError):
    """Failed to start VM.

    Raised when VM start operation fails. This can be due to
    various reasons including invalid configuration, QEMU
    binary issues, or resource constraints.

    Example:
        >>> maqet.start("my-vm")
        VMStartError: Failed to start VM 'my-vm': QEMU binary not found

        >>> try:
        ...     maqet.start("my-vm")
        ... except VMStartError as e:
        ...     logger.error(f"Start failed: {e}")
        ...     maqet.remove_vm("my-vm")
    """


class VMStopError(VMLifecycleError):
    """Failed to stop VM gracefully.

    Raised when VM stop operation fails. This typically occurs
    when the VM process cannot be terminated cleanly or when
    QMP shutdown command fails.

    Example:
        >>> maqet.stop("my-vm")
        VMStopError: Failed to stop VM 'my-vm': Process not responding

        >>> try:
        ...     maqet.stop("my-vm", timeout=30)
        ... except VMStopError:
        ...     print("Forcing shutdown...")
        ...     maqet.force_stop("my-vm")
    """


class VMRunningError(VMLifecycleError):
    """VM is running when it should be stopped.

    Raised when attempting an operation that requires the VM
    to be stopped (e.g., offline snapshots, disk modifications)
    on a running VM.

    Example:
        >>> maqet.create_offline_snapshot("my-vm", "snap1")
        VMRunningError: Cannot create offline snapshot: VM 'my-vm' is running

        >>> try:
        ...     maqet.create_offline_snapshot("vm", "snap")
        ... except VMRunningError:
        ...     maqet.stop("vm")
        ...     maqet.create_offline_snapshot("vm", "snap")
    """


# QMP Errors
class QMPError(MaqetError):
    """Base class for QEMU Machine Protocol (QMP) errors.

    Raised when QMP operations fail, including connection
    establishment, command execution, and communication timeouts.
    QMP is used for all VM runtime control and monitoring.

    Example:
        >>> try:
        ...     maqet.qmp_command("my-vm", "query-status")
        ... except QMPError as e:
        ...     print(f"QMP operation failed: {e}")
    """


class QMPConnectionError(QMPError):
    """Failed to establish connection to QMP socket.

    Raised when maqet cannot connect to the VM's QMP socket.
    This typically occurs when:
    - VM is not running
    - QMP socket file does not exist
    - Insufficient permissions to access socket
    - VM crashed before QMP socket was created

    Example:
        >>> maqet.qmp_command("my-vm", "query-cpus")
        QMPConnectionError: Failed to connect to QMP socket: /path/to/qmp.sock

        >>> try:
        ...     result = maqet.qmp_command("vm", "query-status")
        ... except QMPConnectionError:
        ...     print("VM may have crashed, checking...")
        ...     if not maqet.is_running("vm"):
        ...         maqet.start("vm")
    """


class QMPCommandError(QMPError):
    """QMP command execution failed.

    Raised when a QMP command is sent successfully but QEMU
    returns an error response. This indicates the command was
    invalid, malformed, or cannot be executed in the current
    VM state.

    Example:
        >>> maqet.qmp_command("my-vm", "invalid-command")
        QMPCommandError: QMP command failed: CommandNotFound

        >>> try:
        ...     maqet.qmp_command("vm", "cont")
        ... except QMPCommandError as e:
        ...     print(f"Cannot continue VM: {e}")
    """


class QMPTimeoutError(QMPError):
    """QMP command timed out waiting for response.

    Raised when a QMP command does not complete within the
    specified timeout period. This may indicate the VM is
    hung, overloaded, or the command is taking unexpectedly
    long to complete.

    Example:
        >>> maqet.qmp_command("my-vm", "migrate", timeout=5)
        QMPTimeoutError: QMP command timed out after 5 seconds

        >>> try:
        ...     result = maqet.qmp_command("vm", "savevm", timeout=10)
        ... except QMPTimeoutError:
        ...     print("Snapshot taking too long, increasing timeout...")
        ...     result = maqet.qmp_command("vm", "savevm", timeout=60)
    """


# Storage Errors
class StorageError(MaqetError):
    """Base class for storage operation errors.

    Raised when storage-related operations fail, including
    disk image creation, device attachment, and storage
    configuration validation.

    Example:
        >>> try:
        ...     maqet.create_disk("my-vm", "disk1", size="10G")
        ... except StorageError as e:
        ...     print(f"Storage operation failed: {e}")
    """


class StorageDeviceNotFoundError(StorageError):
    """Storage device does not exist or is not attached.

    Raised when attempting to operate on a storage device
    that is not registered or attached to the VM.

    Example:
        >>> maqet.detach_disk("my-vm", "nonexistent-disk")
        StorageDeviceNotFoundError: Storage device 'nonexistent-disk' not found

        >>> try:
        ...     maqet.snapshot_disk("vm", "disk2")
        ... except StorageDeviceNotFoundError:
        ...     print("Disk not found, attaching first...")
        ...     maqet.attach_disk("vm", "disk2", "/path/to/disk.qcow2")
    """


class StorageCreationError(StorageError):
    """Failed to create storage device or disk image.

    Raised when disk image creation fails due to filesystem
    issues, insufficient space, invalid parameters, or
    qemu-img command failures.

    Example:
        >>> maqet.create_disk("my-vm", "disk1", size="1000T")
        StorageCreationError: Insufficient space to create disk

        >>> try:
        ...     maqet.create_disk("vm", "disk", size="10G", format="qcow2")
        ... except StorageCreationError as e:
        ...     logger.error(f"Disk creation failed: {e}")
    """


class StorageValidationError(StorageError):
    """Storage configuration validation failed.

    Raised when storage configuration is invalid, including
    unsupported disk formats, invalid size specifications,
    or conflicting storage parameters.

    Example:
        >>> maqet.attach_disk("vm", "disk1", "/path/disk.img", format="invalid")
        StorageValidationError: Unsupported disk format: invalid

        >>> config = {'storage': [{'size': '-10G'}]}
        >>> maqet.add_vm("vm", config=config)
        StorageValidationError: Invalid disk size: -10G
    """


# Snapshot Errors
class SnapshotError(MaqetError):
    """Base class for snapshot operation errors.

    Raised when snapshot operations fail, including creation,
    loading, deletion, and listing. Snapshots can be live
    (VM running) or offline (VM stopped).

    Example:
        >>> try:
        ...     maqet.create_snapshot("my-vm", "snap1")
        ... except SnapshotError as e:
        ...     print(f"Snapshot operation failed: {e}")
    """


class SnapshotNotFoundError(SnapshotError):
    """Snapshot does not exist.

    Raised when attempting to operate on a snapshot that
    does not exist in the VM's snapshot tree.

    Example:
        >>> maqet.load_snapshot("my-vm", "nonexistent-snap")
        SnapshotNotFoundError: Snapshot 'nonexistent-snap' not found

        >>> try:
        ...     maqet.delete_snapshot("vm", "old-snap")
        ... except SnapshotNotFoundError:
        ...     print("Snapshot already deleted")
    """


class SnapshotCreationError(SnapshotError):
    """Failed to create snapshot.

    Raised when snapshot creation fails due to disk format
    limitations (e.g., raw disks), insufficient space, QMP
    command failures, or invalid snapshot parameters.

    Example:
        >>> maqet.create_snapshot("my-vm", "snap1")
        SnapshotCreationError: Cannot snapshot raw disk format

        >>> try:
        ...     maqet.create_live_snapshot("vm", "snap1")
        ... except SnapshotCreationError as e:
        ...     logger.error(f"Live snapshot failed: {e}")
        ...     print("Falling back to offline snapshot...")
        ...     maqet.stop("vm")
        ...     maqet.create_snapshot("vm", "snap1")
    """


class SnapshotLoadError(SnapshotError):
    """Failed to load or restore snapshot.

    Raised when snapshot restoration fails. This can occur
    due to corrupted snapshots, disk format changes, or
    QMP command failures.

    Example:
        >>> maqet.load_snapshot("my-vm", "corrupted-snap")
        SnapshotLoadError: Failed to load snapshot: corrupted data

        >>> try:
        ...     maqet.load_snapshot("vm", "snap1")
        ... except SnapshotLoadError as e:
        ...     print(f"Cannot restore snapshot: {e}")
        ...     print("Available snapshots:")
        ...     print(maqet.list_snapshots("vm"))
    """


class SnapshotDeleteError(SnapshotError):
    """Failed to delete snapshot.

    Raised when snapshot deletion fails due to QMP command
    errors, disk access issues, or snapshot dependencies.

    Example:
        >>> maqet.delete_snapshot("my-vm", "snap1")
        SnapshotDeleteError: Cannot delete snapshot with children

        >>> try:
        ...     maqet.delete_snapshot("vm", "snap1")
        ... except SnapshotDeleteError as e:
        ...     logger.warning(f"Snapshot deletion failed: {e}")
    """


# State Management Errors
class StateError(MaqetError):
    """Base class for state management errors.

    Raised when state database operations fail, including
    VM state tracking, database access, and schema migrations.
    The state database stores VM configurations, runtime state,
    and metadata.

    Example:
        >>> try:
        ...     maqet.get_vm_state("my-vm")
        ... except StateError as e:
        ...     print(f"State operation failed: {e}")
    """


class DatabaseError(StateError):
    """Database operation failed.

    Raised when SQLite database operations fail due to
    corruption, access errors, or query failures.

    Example:
        >>> maqet.add_vm("my-vm", config={})
        DatabaseError: Unable to write to database: disk full

        >>> try:
        ...     vms = maqet.list_vms()
        ... except DatabaseError as e:
        ...     logger.error(f"Database error: {e}")
        ...     print("Database may be corrupted")
    """


class DatabaseLockError(DatabaseError):
    """Database is locked and timeout expired.

    Raised when attempting to access the database while
    another process holds a write lock, and the lock
    timeout expires before the lock is released.

    Example:
        >>> maqet.add_vm("my-vm", config={})
        DatabaseLockError: Database locked: timeout after 5 seconds

        >>> try:
        ...     maqet.update_vm("vm", config)
        ... except DatabaseLockError:
        ...     import time
        ...     time.sleep(1)
        ...     maqet.update_vm("vm", config)
    """


class MigrationError(StateError):
    """Database schema migration failed.

    Raised when database schema migration or upgrade fails.
    This typically occurs during maqet version upgrades when
    the database schema needs to be updated.

    Example:
        >>> maqet.migrate_database()
        MigrationError: Failed to migrate from v1 to v2: column conflict

        >>> try:
        ...     maqet.initialize()
        ... except MigrationError as e:
        ...     logger.error(f"Migration failed: {e}")
        ...     print("Backup database and retry")
    """


# Security Errors
class SecurityError(MaqetError):
    """Security-related errors.

    Raised when security violations or policy failures occur,
    including:
    - File permission issues
    - Authentication failures
    - Resource limit violations
    - Subprocess output size limits exceeded
    - Path traversal attempts

    Example:
        >>> maqet.create_disk("vm", "../../../etc/passwd")
        SecurityError: Path traversal attempt detected

        >>> try:
        ...     maqet.execute_command("vm", dangerous_cmd)
        ... except SecurityError as e:
        ...     logger.warning(f"Security violation: {e}")
    """


# Process Management Errors
class ProcessError(MaqetError):
    """Base class for process management errors.

    Raised when VM runner process operations fail, including
    spawning, monitoring, and terminating processes. The VM
    runner is the intermediary process that manages QEMU.

    Example:
        >>> try:
        ...     maqet.start("my-vm")
        ... except ProcessError as e:
        ...     print(f"Process error: {e}")
    """


class RunnerProcessError(ProcessError):
    """VM runner process encountered an error.

    Raised when the VM runner process reports an error
    condition or fails during normal operation.

    Example:
        >>> maqet.start("my-vm")
        RunnerProcessError: VM runner failed: socket creation error

        >>> try:
        ...     maqet.start("vm")
        ... except RunnerProcessError as e:
        ...     logger.error(f"Runner error: {e}")
        ...     maqet.cleanup_runner("vm")
    """


class RunnerSpawnError(ProcessError):
    """Failed to spawn VM runner process.

    Raised when the VM runner process cannot be spawned,
    typically due to:
    - Missing Python executable
    - Insufficient permissions
    - Resource limits (process limit, file descriptors)
    - Invalid runner command

    Example:
        >>> maqet.start("my-vm")
        RunnerSpawnError: Failed to spawn runner: permission denied

        >>> try:
        ...     maqet.start("vm")
        ... except RunnerSpawnError as e:
        ...     print(f"Cannot spawn runner: {e}")
        ...     print("Check permissions and resource limits")
    """


class ProcessNotFoundError(ProcessError):
    """Process not found or already terminated.

    Raised when attempting to operate on a process (VM runner
    or QEMU) that does not exist or has already terminated.

    Example:
        >>> maqet.stop("my-vm")
        ProcessNotFoundError: VM runner process not found

        >>> try:
        ...     maqet.get_process_info("vm")
        ... except ProcessNotFoundError:
        ...     print("Process already terminated")
        ...     maqet.cleanup_state("vm")
    """


class VMRunnerError(ProcessError):
    """VM runner process encountered an error during execution.

    Raised when the VM runner process fails during VM
    execution, distinct from spawn failures. This indicates
    the runner started successfully but encountered an
    error while managing the VM.

    Example:
        >>> maqet.start("my-vm")
        VMRunnerError: Runner crashed during VM initialization

        >>> try:
        ...     maqet.monitor_vm("vm")
        ... except VMRunnerError as e:
        ...     logger.error(f"Runner execution error: {e}")
        ...     maqet.restart_runner("vm")
    """


class QEMUProcessError(VMStartError):
    """QEMU process failed to start or crashed immediately.

    Raised when the QEMU process itself fails to start or
    crashes immediately after starting. This is distinct from
    VM runner errors - the runner started successfully but
    QEMU failed.

    Example:
        >>> maqet.start("my-vm")
        QEMUProcessError: QEMU crashed: invalid machine type

        >>> try:
        ...     maqet.start("vm")
        ... except QEMUProcessError as e:
        ...     print(f"QEMU failed: {e}")
        ...     print("Check QEMU configuration and logs")
    """


# IPC Errors
class IPCError(MaqetError):
    """Base class for inter-process communication errors.

    Raised when IPC operations fail between the maqet client
    and VM runner process. IPC is used for sending commands
    and receiving status from the runner.

    Example:
        >>> try:
        ...     maqet.send_command("my-vm", "status")
        ... except IPCError as e:
        ...     print(f"IPC error: {e}")
    """


class IPCConnectionError(IPCError):
    """Failed to establish IPC connection.

    Raised when maqet cannot connect to the VM runner's IPC
    socket. This typically occurs when:
    - VM runner is not running
    - IPC socket file does not exist
    - Insufficient permissions to access socket
    - Socket path is incorrect

    Example:
        >>> maqet.send_command("my-vm", "status")
        IPCConnectionError: Failed to connect to IPC socket

        >>> try:
        ...     maqet.query_runner("vm")
        ... except IPCConnectionError:
        ...     print("Runner not responding, restarting...")
        ...     maqet.restart_runner("vm")
    """


class IPCTimeoutError(IPCError):
    """IPC communication timed out.

    Raised when an IPC command does not receive a response
    within the specified timeout period. This may indicate
    the runner is hung or processing a long-running operation.

    Example:
        >>> maqet.send_command("my-vm", "start", timeout=5)
        IPCTimeoutError: IPC command timed out after 5 seconds

        >>> try:
        ...     response = maqet.query_runner("vm", timeout=10)
        ... except IPCTimeoutError:
        ...     print("Runner not responding, may be hung")
    """


class IPCCommandError(IPCError):
    """IPC command execution failed.

    Raised when an IPC command is sent successfully but the
    VM runner returns an error response. This indicates the
    command was invalid or cannot be executed.

    Example:
        >>> maqet.send_command("my-vm", "invalid-command")
        IPCCommandError: Unknown command: invalid-command

        >>> try:
        ...     maqet.runner_command("vm", "shutdown")
        ... except IPCCommandError as e:
        ...     logger.error(f"Runner command failed: {e}")
    """


# Wait/Timeout Errors
class WaitTimeout(MaqetError):
    """Wait operation timed out.

    Raised when a high-level wait condition does not complete
    within the specified timeout period. This is used for
    operations like waiting for VM to start, SSH to become
    ready, or specific VM states to be reached.

    This is distinct from QMPTimeoutError and IPCTimeoutError
    which are protocol-specific timeouts. WaitTimeout is for
    higher-level operational timeouts.

    Example:
        >>> maqet.wait_for_ssh("my-vm", timeout=30)
        WaitTimeout: SSH not ready after 30 seconds

        >>> try:
        ...     maqet.wait_for_vm_ready("vm", timeout=60)
        ... except WaitTimeout:
        ...     print("VM taking too long to start")
        ...     print("Checking VM logs...")
        ...     print(maqet.get_logs("vm"))

        >>> try:
        ...     maqet.start("vm")
        ...     maqet.wait_for_boot("vm", timeout=120)
        ... except WaitTimeout as e:
        ...     logger.warning(f"Boot timeout: {e}")
        ...     maqet.stop("vm", force=True)
    """
