"""
MAQET Core

Main MAQET class implementing unified API for VM management.
All methods are decorated with @api_method to enable automatic CLI
and Python API generation.
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from typing_extensions import Unpack

from .api import (
    API_REGISTRY,
    APIRegistry,
    AutoRegisterAPI,
    api_method,
)
from .config import ConfigMerger, ConfigParser  # noqa: F401 - ConfigMerger used by test mocking
from .constants import Timeouts
from .exceptions import (
    MaqetError,
    QMPError,
    SnapshotError,
)
from .generators import CLIGenerator, PythonAPIGenerator
from .logger import LOG
from .managers import ConfigManager, QMPManager, VMManager
from .state import StateManager, VMInstance
from .types import QMPParams, SnapshotParams, StartParams, VMConfigParams, validate_kwargs
from .vm_lifecycle import VMLifecycleManager


class CleanupStrategy:
    """Controls when automatic cleanup runs."""
    EAGER = "eager"      # Current behavior (every init)
    LAZY = "lazy"        # Only on mutation commands
    MANUAL = "manual"    # Never auto-cleanup


class Maqet(AutoRegisterAPI):
    """
    MAQET - M4x0n's QEMU Tool

    Unified VM management system that provides CLI commands, Python API,
    and configuration-based
    VM orchestration through a single decorated method interface.

    This class implements your vision of "write once, generate everywhere"
    - each @api_method
    decorated method automatically becomes available as:
    - CLI command (via maqet <command>)
    - Python API method (via maqet.method())
    - Configuration file key (via YAML parsing)

    # ARCHITECTURE: Facade Pattern with Managers
    # ===========================================
    # This class now serves as a facade delegating to specialized managers:
    # - ConfigManager: configuration precedence and directory resolution
    # - VMManager: VM lifecycle (add, start, stop, rm, ls) and snapshot operations
    # - QMPManager: QMP operations (qmp, keys, type, screendump, etc.)
    # - ConfigParser: configuration validation (used directly by VMManager)
    # - StateManager: database operations

    # ARCHITECTURAL DESIGN: In-memory Machine Instances
    # ================================================
    # Design Choice: Machine instances stored in memory dict (_machines)
    #   - Simple, fast, no serialization overhead
    #   - Perfect for Python API usage (long-running scripts)
    #   - Trade-off: Lost between CLI invocations
    #
    # Implications:
    #   - CLI Mode: Each command runs in fresh process
    #     * VM state persisted in SQLite (~/.local/share/maqet/instances.db)
    #     * Machine objects recreated on each CLI call
    #     * QMP connections NOT maintained across CLI calls
    #   - Python API Mode: Single process, instances persist
    # * maqet = Maqet(); maqet.start("vm1"); maqet.qmp("vm1", "query-status")
    #     * QMP works seamlessly within same process
    #
    # When to use each mode:
    #   - CLI Mode: Simple VM management (start, stop, status, info, inspect)
    #   - Python API: Automation scripts, CI/CD pipelines, persistent QMP
    #
    # QMP commands work in Python API mode where Machine instances persist
    # across method calls. For CLI workflows requiring QMP, use Python API.
    """

    def __init__(
        self,
        data_dir: Optional[Union[str, Path]] = None,
        config_dir: Optional[Union[str, Path]] = None,
        runtime_dir: Optional[Union[str, Path]] = None,
        register_signals: bool = True,
        auto_cleanup: bool = True,
        cleanup_strategy: Optional[str] = None,
        cleanup_interval_seconds: int = 300,
    ):
        """
        Initialize MAQET instance.

        This is the COMPOSITION ROOT for the entire application.
        All dependency wiring happens here, in one place.

        Layered architecture dependency flow:
        1. Infrastructure layer (no dependencies)
           - ConfigManager: directory resolution, XDG compliance
        2. State layer (depends on infrastructure)
           - StateManager: database, XDG directories, process tracking
        3. Domain services (depends on state)
           - QMPManager: QMP operations (needs StateManager)
           - ConfigParser: configuration validation
        4. Business logic layer (depends on domain services)
           - VMManager: VM lifecycle orchestration
           - VMLifecycleManager: transactional storage operations
        5. Application layer (this class)
           - Maqet: public API facade

        Args:
            data_dir: Override default XDG data directory
            config_dir: Override default XDG config directory
            runtime_dir: Override default XDG runtime directory
            register_signals: Register signal handlers for graceful shutdown (default: True)
            auto_cleanup: Run automatic cleanup before CLI commands (default: True, uses LAZY strategy)
            cleanup_strategy: Cleanup strategy: "eager", "lazy", or "manual" (defaults to LAZY if auto_cleanup=True)
            cleanup_interval_seconds: Minimum seconds between lazy cleanups (default: 300)
        """
        # === COMPOSITION ROOT ===
        # All dependency wiring happens here. This is the only place that knows
        # about concrete implementations. Upper layers receive dependencies via
        # constructor parameters (constructor injection pattern).

        # LAYER 1: Infrastructure - Directory resolution and configuration
        # No dependencies on other maqet components
        self.config_manager = ConfigManager(
            data_dir=data_dir,
            config_dir=config_dir,
            runtime_dir=runtime_dir,
        )

        # LAYER 2: State - Database and filesystem operations
        # Depends on: Infrastructure (directory paths from ConfigManager)
        self.state_manager = StateManager(
            data_dir=self.config_manager.get_data_dir(),
            config_dir=self.config_manager.get_config_dir(),
            runtime_dir=self.config_manager.get_runtime_dir(),
        )

        # LAYER 3: Domain Services - Configuration and QMP operations
        # ConfigParser needs Maqet reference for legacy reasons (to be refactored)
        # QMPManager depends on StateManager for VM lookups and socket paths
        self.config_parser = ConfigParser(self)
        self.qmp_manager = QMPManager(self.state_manager)

        # LAYER 4: Business Logic - VM lifecycle and storage management
        # VMManager depends on: StateManager, ConfigParser, QMPManager
        # VMLifecycleManager depends on: StateManager (creates StorageRegistry internally)
        self.vm_manager = VMManager(
            self.state_manager,
            self.config_parser,
            self.qmp_manager
        )
        self.lifecycle_manager = VMLifecycleManager(self.state_manager)

        # === APPLICATION CONFIGURATION ===
        # Runtime flags and instance-specific state
        self._signal_handlers_registered = False
        self.auto_cleanup = auto_cleanup

        # Determine cleanup strategy
        # Priority: auto_cleanup=False > cleanup_strategy param > env var > default (LAZY)
        if not auto_cleanup:
            # Explicit disable overrides everything
            self._cleanup_strategy = CleanupStrategy.MANUAL
        elif cleanup_strategy is not None:
            # Explicit strategy parameter
            self._cleanup_strategy = cleanup_strategy
        else:
            # Check environment variable, default to LAZY
            env_strategy = os.getenv("MAQET_CLEANUP_STRATEGY")
            self._cleanup_strategy = env_strategy if env_strategy else CleanupStrategy.LAZY

        self._cleanup_interval = cleanup_interval_seconds
        self._last_cleanup: Optional[float] = None

        # Create instance-specific API registry
        # This allows parallel test execution and multiple Maqet instances
        # with isolated registries (no cross-contamination)
        self._api_registry = APIRegistry()
        self._api_registry.register_from_instance(self)

        # === INITIALIZATION HOOKS ===
        # Optional runtime configuration
        if register_signals:
            self._register_signal_handlers()

        # Run automatic cleanup on initialization only if EAGER strategy
        if self._cleanup_strategy == CleanupStrategy.EAGER:
            self._cleanup_on_init()
            self._last_cleanup = time.time()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        return False  # Don't suppress exceptions

    def _cleanup_on_init(self) -> None:
        """
        Run automatic cleanup on initialization if enabled.

        This method calls vm_manager.cleanup_dead_processes() to detect
        and clean up VMs with dead processes. It does not fail initialization
        if cleanup encounters errors.
        """
        try:
            # Quick cleanup: Only check running VMs
            cleaned = self.vm_manager.cleanup_dead_processes()
            if cleaned:
                LOG.debug(f"Auto-cleanup: Fixed {len(cleaned)} corrupted VM(s)")
        except Exception as e:
            LOG.warning(f"Auto-cleanup failed: {e}")
            # Don't fail initialization due to cleanup errors

    def _maybe_cleanup(self) -> None:
        """
        Run cleanup if needed based on strategy and interval.

        Only runs cleanup for LAZY strategy when enough time has passed
        since last cleanup. MANUAL strategy never auto-cleans.
        """
        if self._cleanup_strategy == CleanupStrategy.MANUAL:
            return

        now = time.time()
        if self._last_cleanup is None or \
           (now - self._last_cleanup) > self._cleanup_interval:
            self._cleanup_on_init()
            self._last_cleanup = now

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        import signal

        def signal_handler(signum, frame):
            LOG.info(
                f"Received signal {signum}, initiating graceful shutdown..."
            )
            self.cleanup()
            sys.exit(0)

        # Register handlers for SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        self._signal_handlers_registered = True
        LOG.debug("Signal handlers registered for graceful shutdown")

    def get_api_registry(self) -> APIRegistry:
        """
        Get the instance-specific API registry.

        Returns:
            APIRegistry instance for this Maqet instance

        Example:
            maqet = Maqet()
            registry = maqet.get_api_registry()
            methods = registry.get_all_methods()
        """
        return self._api_registry

    def cleanup(self) -> None:
        """Clean up all resources (stop running VMs, close connections).

        Delegates to VMManager.cleanup_all() which handles parallel VM shutdown
        with proper timeout management. Also closes database connections.
        """
        LOG.debug("Cleaning up MAQET resources...")
        self.vm_manager.cleanup_all()

        # Close lifecycle manager database connection
        if hasattr(self, 'lifecycle_manager'):
            self.lifecycle_manager.close()

        LOG.debug("MAQET cleanup completed")

    @api_method(
        cli_name="add",
        description="Create a new VM from configuration",
        category="vm",
        examples=[
            "maqet add config.yaml",
            "maqet add config.yaml --name myvm",
            "maqet add --name testvm --memory 4G --cpu 2",
            "maqet add base.yaml custom.yaml --name myvm",
            "maqet add base.yaml --memory 8G",
            "maqet add --name empty-vm --empty",
        ],
    )
    def add(
        self,
        vm_config: Optional[Union[str, List[str]]] = None,
        name: Optional[str] = None,
        empty: bool = False,
        **kwargs: Unpack[VMConfigParams],
    ) -> str:
        """
        Create a new VM from configuration file(s) or parameters.

        Delegates to VMManager for actual VM creation logic.

        Args:
            vm_config: Path to YAML configuration file, or list of config
                files for deep-merge
            name: VM name (auto-generated if not provided)
            empty: Create empty VM without any configuration (won't be
                startable until configured)
            **kwargs: Additional VM configuration parameters (see VMConfigParams)

        Returns:
            VM instance ID

        Raises:
            MaqetError: If VM creation fails
            VMAlreadyExistsError: VM with this name already exists
            ConfigValidationError: Invalid configuration provided
            ConfigFileNotFoundError: Configuration file not found
            StorageCreationError: Failed to create storage files

        Examples:
            Single config: add(vm_config="vm.yaml", name="myvm")
            Multiple configs: add(
                vm_config=["base.yaml", "custom.yaml"], name="myvm"
            )
            Config + params: add(vm_config="base.yaml", memory="8G", cpus=4)
            Empty VM: add(name="placeholder-vm", empty=True)
        """
        validate_kwargs(kwargs, VMConfigParams)
        self._maybe_cleanup()
        return self.vm_manager.add(vm_config, name, empty, **kwargs)

    @api_method(
        cli_name="start",
        description="Start a virtual machine",
        category="vm",
        requires_vm=True,
        examples=[
            "maqet start myvm",
            "maqet start myvm --timeout 60",
            "maqet start myvm --no-wait",
        ],
    )
    def start(
        self,
        vm_id: str,
        wait: bool = True,
        wait_for: str = "process-started",
        timeout: Optional[float] = None,
        **kwargs: Unpack[StartParams],
    ) -> VMInstance:
        """
        Start a virtual machine by spawning a detached VM runner process.

        Delegates to VMManager for actual VM start logic.

        Args:
            vm_id: VM identifier (name or ID)
            wait: Wait for condition before returning (default True)
            wait_for: Wait condition: process-started, file-exists
            timeout: Maximum wait time in seconds (default 30s)
            **kwargs: Additional start parameters (see StartParams)

        Returns:
            VM instance information

        Raises:
            MaqetError: If VM start fails or timeout expires
            VMNotFoundError: VM does not exist
            VMAlreadyRunningError: VM is already running
            ProcessSpawnError: Failed to spawn VM runner process

        Examples:
            Basic start:
                maqet.start("myvm")

            Start without waiting:
                maqet.start("myvm", wait=False)

            Start with custom timeout:
                maqet.start("myvm", wait_timeout=180.0)
        """
        validate_kwargs(kwargs, StartParams)
        self._maybe_cleanup()
        # Extract StartParams - wait_timeout overrides timeout if provided
        effective_timeout = kwargs.get('wait_timeout', timeout)
        return self.vm_manager.start(
            vm_id,
            wait=wait,
            wait_for=wait_for,
            timeout=effective_timeout,
        )

    @api_method(
        cli_name="stop",
        description="Stop a virtual machine",
        category="vm",
        requires_vm=True,
        examples=["maqet stop myvm", "maqet stop myvm --force"],
    )
    def stop(
        self, vm_id: str, force: bool = False, timeout: int = Timeouts.VM_STOP
    ) -> VMInstance:
        """
        Stop a VM by sending stop command to VM runner or killing runner process.

        Delegates to VMManager for actual VM stop logic.

        Args:
            vm_id: VM identifier (name or ID)
            force: If True, kill runner immediately (SIGKILL).
                   If False, graceful shutdown (SIGTERM)
            timeout: Timeout for graceful shutdown

        Returns:
            VM instance information

        Raises:
            MaqetError: If VM stop fails
        """
        self._maybe_cleanup()
        return self.vm_manager.stop(vm_id, force, timeout)

    @api_method(
        cli_name="rm",
        description="Remove a virtual machine",
        category="vm",
        requires_vm=False,
        examples=[
            "maqet rm myvm",
            "maqet rm myvm --force",
            "maqet rm myvm --delete-storage",
            "maqet rm myvm --delete-storage --keep-snapshots",
            "maqet rm --all",
            "maqet rm --all --force",
        ],
    )
    def rm(
        self,
        vm_id: Optional[str] = None,
        force: bool = False,
        all: bool = False,
        clean_storage: bool = False,
        delete_storage: bool = False,
        keep_snapshots: bool = False,
    ) -> bool:
        """
        Remove a virtual machine completely.

        Delegates to VMManager for actual VM removal logic.

        Args:
            vm_id: VM identifier (name or ID)
            force: Force removal even if VM is running (skip confirmation)
            all: Remove all virtual machines
            clean_storage: (DEPRECATED) Use --delete-storage instead
            delete_storage: Delete storage files (default: keep storage)
            keep_snapshots: Keep snapshot files even if delete_storage=True

        Returns:
            True if removed successfully

        Raises:
            MaqetError: If VM removal fails
        """
        self._maybe_cleanup()
        # Handle deprecated clean_storage flag
        if clean_storage:
            LOG.warning("--clean-storage is deprecated, use --delete-storage instead")
            delete_storage = True

        result = self.vm_manager.remove(
            vm_id, force, all, delete_storage, keep_snapshots
        )
        # Clean up machine instances that were removed via VMManager
        if all:
            self.vm_manager.clear_machine_cache()
        elif vm_id:
            vm = self.state_manager.get_vm(vm_id)
            if vm:
                self.vm_manager.clear_machine_cache(vm.id)
        return result

    @api_method(
        cli_name="ls",
        description="List virtual machines in table format",
        category="vm",
        examples=["maqet ls", "maqet ls --status running"],
    )
    def ls(self, status: Optional[str] = None) -> str:
        """
        List virtual machines in readable table format.

        Delegates to VMManager for VM list retrieval. Shows status
        indicators for orphaned and corrupted VMs.

        Args:
            status: Filter by status ('running', 'stopped', 'created',
                'failed', 'orphaned', 'corrupted')

        Returns:
            Formatted table string
        """
        vms = self.vm_manager.list_vms(status, validate_status=True)

        if not vms:
            return "No virtual machines found."

        # Enhanced table with status indicators and notes
        header = f"{'NAME':<20} {'STATUS':<12} {'PID':<8} {'RUNNER':<8} {'NOTES':<20}"
        separator = "-" * 70
        rows = [header, separator]

        for vm in vms:
            pid_str = str(vm.pid) if vm.pid else "-"
            runner_str = str(vm.runner_pid) if vm.runner_pid else "-"

            # Status indicators
            status_display = vm.status
            notes = ""

            if vm.status == "orphaned":
                status_display = "orphaned"
                notes = "Runner crashed"
            elif vm.status == "corrupted":
                status_display = "corrupted"
                notes = "Needs cleanup"

            row = f"{vm.name:<20} {status_display:<12} {pid_str:<8} {runner_str:<8} {notes:<20}"
            rows.append(row)

        return "\n".join(rows)

    @api_method(
        cli_name="status",
        description="Show comprehensive VM status information",
        category="vm",
        requires_vm=True,
        examples=["maqet status myvm", "maqet status myvm --detailed"],
    )
    def status(self, vm_id: str, detailed: bool = False) -> Dict[str, Any]:
        """
        Get basic status information for a VM (delegates to VMManager).

        Args:
            vm_id: VM identifier (name or ID)
            detailed: (DEPRECATED) Use 'maqet inspect' instead for detailed information

        Returns:
            Dictionary with basic VM status information

        Raises:
            MaqetError: If VM not found
        """
        # Handle deprecated detailed flag - log warning and redirect to inspect
        if detailed:
            LOG.warning(
                "The --detailed flag for 'status' command is deprecated. "
                "Use 'maqet inspect %s' for detailed VM inspection instead.",
                vm_id
            )
            return self.inspect(vm_id)

        return self.vm_manager.status(vm_id, detailed)

    @api_method(
        cli_name="info",
        description="Show VM configuration details",
        category="vm",
        requires_vm=True,
        examples=["maqet info myvm"],
    )
    def info(self, vm_id: str) -> Dict[str, Any]:
        """
        Get VM configuration details (delegates to VMManager).

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            Dictionary with VM configuration details

        Raises:
            MaqetError: If VM not found
        """
        return self.vm_manager.info(vm_id)

    @api_method(
        cli_name="inspect",
        description="Inspect VM with detailed process and resource information",
        category="vm",
        requires_vm=True,
        examples=["maqet inspect myvm"],
    )
    def inspect(self, vm_id: str) -> Dict[str, Any]:
        """
        Get detailed inspection information for a VM (delegates to VMManager).

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            Dictionary with comprehensive VM inspection data

        Raises:
            MaqetError: If VM not found
        """
        return self.vm_manager.inspect(vm_id)

    @api_method(
        cli_name="storage-info",
        description="Show storage file locations and resolved paths",
        category="info",
        requires_vm=True,
        examples=["maqet storage-info myvm"],
    )
    def storage_info_cmd(self, vm_id: str) -> Dict[str, Any]:
        """
        Get detailed storage information including resolved file paths.

        This command helps debug storage-related issues by showing:
        - Configured paths (as specified in VM configuration)
        - Resolved absolute paths (after path resolution)
        - File existence status
        - File sizes
        - Storage registry tracking status

        Useful for understanding where storage files are actually located,
        especially when using relative paths.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            Dictionary with storage information

        Raises:
            MaqetError: If VM not found
        """
        return self.vm_manager.get_storage_info(vm_id)

    @api_method(
        cli_name="qmp",
        description="Execute QMP command on VM",
        category="qmp",
        requires_vm=True,
        hidden=True,
        examples=[
            "maqet qmp myvm system_powerdown",
            "maqet qmp myvm screendump --filename screenshot.ppm",
        ],
    )
    def qmp(
        self,
        vm_id: str,
        command: str,
        **kwargs: Unpack[QMPParams],
    ) -> Dict[str, Any]:
        """
        Execute QMP command (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            command: QMP command to execute
            **kwargs: Command parameters and QMP options (see QMPParams)

        Returns:
            QMP command result

        Raises:
            QMPError: If QMP connection fails or command execution fails
            VMNotFoundError: VM does not exist
            VMNotRunningError: VM is not running (QMP requires running VM)
            QMPTimeoutError: QMP command timed out
        """
        validate_kwargs(kwargs, QMPParams)
        return self.qmp_manager.execute_qmp(vm_id, command, **kwargs)

    @api_method(
        cli_name="keys",
        description="Send key combination to VM via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp keys myvm ctrl alt f2",
            "maqet qmp keys myvm --hold-time 200 ctrl c",
        ],
    )
    def qmp_key(
        self, vm_id: str, *keys: str, hold_time: int = 100
    ) -> Dict[str, Any]:
        """
        Send key combination to VM (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            *keys: Key names to press (e.g., 'ctrl', 'alt', 'f2')
            hold_time: How long to hold keys in milliseconds

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.send_keys(vm_id, *keys, hold_time=hold_time)
        except QMPError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="type",
        description="Type text string to VM via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp type myvm 'hello world'",
            "maqet qmp type myvm --hold-time 50 'slow typing'",
        ],
    )
    def qmp_type(
        self, vm_id: str, text: str, hold_time: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Type text string to VM (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            text: Text to type
            hold_time: How long to hold each key in milliseconds

        Returns:
            List of QMP command results

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.type_text(vm_id, text, hold_time=hold_time)
        except QMPError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="screendump",
        description="Take screenshot of VM screen",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp screendump myvm screenshot.ppm",
            "maqet qmp screendump myvm /tmp/vm_screen.ppm",
        ],
    )
    def screendump(self, vm_id: str, filename: str) -> Dict[str, Any]:
        """
        Take screenshot of VM screen (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            filename: Output filename for screenshot

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.take_screenshot(vm_id, filename)
        except QMPError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="pause",
        description="Pause VM execution via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=["maqet qmp pause myvm"],
    )
    def qmp_stop(self, vm_id: str) -> Dict[str, Any]:
        """
        Pause VM execution via QMP (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.pause(vm_id)
        except QMPError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="resume",
        description="Resume VM execution via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=["maqet qmp resume myvm"],
    )
    def qmp_cont(self, vm_id: str) -> Dict[str, Any]:
        """
        Resume VM execution via QMP (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.resume(vm_id)
        except QMPError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="device-add",
        description="Hot-plug device to VM via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp device-add myvm usb-storage --device-id usb1 "
            "--drive usb-drive",
            "maqet qmp device-add myvm e1000 --device-id net1 --netdev user1",
        ],
    )
    def device_add(
        self, vm_id: str, driver: str, device_id: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Hot-plug device to VM via QMP (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            driver: Device driver name (e.g., 'usb-storage', 'e1000')
            device_id: Unique device identifier
            **kwargs: Additional device properties

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.device_add(vm_id, driver, device_id, **kwargs)
        except QMPError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="device-del",
        description="Hot-unplug device from VM via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=["maqet qmp device-del myvm usb1"],
    )
    def device_del(self, vm_id: str, device_id: str) -> Dict[str, Any]:
        """
        Hot-unplug device from VM via QMP (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            device_id: Device identifier to remove

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.device_del(vm_id, device_id)
        except QMPError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="run",
        description="Execute raw QMP command on VM",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp run myvm query-status",
            "maqet qmp run myvm query-block",
            'maqet qmp run myvm human-monitor-command --command-line "info block"',
        ],
    )
    def qmp_run(
        self,
        vm_id: str,
        command: str,
        **kwargs: Unpack[QMPParams],
    ) -> Dict[str, Any]:
        """
        Execute arbitrary QMP command.

        This method exposes raw QMP execution to CLI users, allowing any
        valid QMP command to be executed on a running VM.

        Args:
            vm_id: VM identifier (name or ID)
            command: QMP command name (e.g., query-status, query-block)
            **kwargs: Command arguments and QMP options (see QMPParams)

        Returns:
            QMP command result as dict

        Raises:
            QMPError: If QMP connection fails or command execution fails
            VMNotFoundError: VM does not exist
            VMNotRunningError: VM is not running
            QMPTimeoutError: QMP command timed out
        """
        validate_kwargs(kwargs, QMPParams)
        try:
            return self.qmp_manager.execute_qmp(vm_id, command, **kwargs)
        except QMPError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="snapshot",
        description="Manage VM storage snapshots",
        category="storage",
        requires_vm=True,
        examples=[
            "maqet snapshot myvm create ssd backup_name",
            "maqet snapshot myvm create ssd backup_name --live",
            "maqet snapshot myvm create ssd backup_name --overwrite",
            "maqet snapshot myvm create ssd backup_name --live --overwrite",
            "maqet snapshot myvm load ssd backup_name",
            "maqet snapshot myvm list ssd",
        ],
    )
    def snapshot(
        self,
        vm_id: str,
        action: str,
        drive: str,
        name: Optional[str] = None,
        overwrite: bool = False,
        live: bool = False,
        **kwargs: Unpack[SnapshotParams],
    ) -> Union[Dict[str, Any], List[str]]:
        """
        Manage VM storage snapshots (delegates to VMManager).

        Args:
            vm_id: VM identifier (name or ID)
            action: Snapshot action ('create', 'load', 'list')
            drive: Storage drive name
            name: Snapshot name (required for create/load)
            overwrite: Overwrite existing snapshot (create only)
            live: Use live snapshot on running VM (create only)
            **kwargs: Additional snapshot parameters (see SnapshotParams)

        Returns:
            Operation result dictionary or list of snapshots

        Raises:
            SnapshotError: If snapshot operation fails
            VMNotFoundError: VM does not exist
            SnapshotNotFoundError: Snapshot does not exist (load action)
            SnapshotAlreadyExistsError: Snapshot exists and overwrite=False
            VMNotRunningError: VM must be running for live snapshots
        """
        validate_kwargs(kwargs, SnapshotParams)
        # Route to appropriate VMManager method based on action
        if action == "create":
            if not name:
                raise SnapshotError(
                    "Snapshot name required for create action"
                )
            return self.vm_manager.create_snapshot(vm_id, drive, name, overwrite, live)
        elif action == "load":
            if not name:
                raise SnapshotError(
                    "Snapshot name required for load action"
                )
            return self.vm_manager.load_snapshot(vm_id, drive, name)
        elif action == "list":
            return self.vm_manager.list_snapshots(vm_id, drive)
        else:
            raise SnapshotError(
                f"Invalid action '{action}'. "
                f"Available actions: create, load, list"
            )

    @api_method(
        cli_name="apply",
        description="Apply configuration to existing VM",
        category="vm",
        requires_vm=True,
        examples=[
            "maqet apply myvm config.yaml",
            "maqet apply myvm --memory 8G --cpu 4",
        ],
    )
    def apply(
        self,
        vm_id: str,
        vm_config: Optional[Union[str, List[str]]] = None,
        **kwargs: Unpack[VMConfigParams],
    ) -> VMInstance:
        """
        Apply configuration to existing VM (delegates to VMManager).

        Args:
            vm_id: VM identifier (name or ID)
            vm_config: Path to configuration file, or list of config
                files for deep-merge
            **kwargs: Configuration parameters to update (see VMConfigParams)

        Returns:
            VM instance (created or updated)

        Raises:
            MaqetError: If configuration is invalid or operation fails
            VMNotFoundError: VM does not exist
            ConfigValidationError: Invalid configuration provided
            ConfigFileNotFoundError: Configuration file not found
        """
        validate_kwargs(kwargs, VMConfigParams)
        self._maybe_cleanup()
        return self.vm_manager.apply(vm_id, vm_config, **kwargs)

    @api_method(
        cli_name="orphaned",
        description="List orphaned storage files without VM entries",
        category="storage",
        parent="storage",
        examples=["maqet storage orphaned"],
    )
    def storage_orphaned(self) -> List[Dict[str, Any]]:
        """
        List orphaned storage files.

        Scans storage directories for files that exist on disk but have no
        corresponding VM entry in the database. These files consume disk space
        and may indicate VMs that were deleted without removing storage.

        Returns:
            List of orphaned storage entries with path and size information

        Raises:
            MaqetError: If storage scan fails
        """
        try:
            orphans = self.lifecycle_manager.storage_registry.find_orphaned_storage()

            if not orphans:
                print("No orphaned storage found")
                return []

            print(f"Found {len(orphans)} orphaned storage file(s):\n")

            total_size = 0
            orphan_data = []

            for orphan in orphans:
                size_mb = orphan.size_bytes / (1024 * 1024) if orphan.size_bytes else 0
                total_size += orphan.size_bytes or 0
                print(f"  {orphan.storage_path} ({size_mb:.1f} MB)")

                orphan_data.append(
                    {
                        "path": str(orphan.storage_path),
                        "size_bytes": orphan.size_bytes,
                        "size_mb": size_mb,
                    }
                )

            total_mb = total_size / (1024 * 1024)
            print(f"\nTotal: {total_mb:.1f} MB")
            print("\nTo attach storage to a VM:")
            print("  maqet storage attach <vm-name> <storage-path> --vm-config <config>")
            print("\nTo delete orphaned storage manually:")
            print("  rm <storage-path>")

            return orphan_data

        except Exception as e:
            raise MaqetError(f"Failed to list orphaned storage: {e}")

    @api_method(
        cli_name="attach",
        description="Attach orphaned storage to a new VM",
        category="storage",
        parent="storage",
        examples=[
            "maqet storage attach myvm /path/to/disk.qcow2 --vm-config config.yaml"
        ],
    )
    def storage_attach(
        self, vm_name: str, storage_path: str, vm_config: str
    ) -> VMInstance:
        """
        Attach orphaned storage to a VM.

        Creates a new VM entry for existing orphaned storage. This is useful
        for recovering VMs that were deleted without removing storage, or for
        reusing disk images.

        Args:
            vm_name: New VM name to create
            storage_path: Path to orphaned storage file
            vm_config: Path to VM configuration YAML file

        Returns:
            Created VM instance

        Raises:
            MaqetError: If VM already exists, storage doesn't exist, or operation fails
        """
        import yaml

        try:

            # Convert path to Path object
            storage_path_obj = Path(storage_path)
            vm_config_path = Path(vm_config)

            # Validate files exist
            if not storage_path_obj.exists():
                raise ValueError(f"Storage file not found: {storage_path}")
            if not vm_config_path.exists():
                raise ValueError(f"Config file not found: {vm_config}")

            # Load VM config from YAML
            with open(vm_config_path) as f:
                config_data = yaml.safe_load(f)

            # Attach storage using lifecycle manager
            self.lifecycle_manager.attach_orphaned_storage(vm_name, storage_path_obj, config_data)

            print(f"Storage attached to VM '{vm_name}'")
            print(f"You can now start the VM: maqet start {vm_name}")

            # Return the created VM instance
            return self.state_manager.get_vm(vm_name)

        except ValueError as e:
            raise MaqetError(str(e))
        except Exception as e:
            raise MaqetError(f"Failed to attach storage: {e}")

    @api_method(
        cli_name="verify",
        description="Verify storage integrity for a VM",
        category="storage",
        parent="storage",
        requires_vm=True,
        examples=["maqet storage verify myvm"],
    )
    def storage_verify(self, vm_id: str) -> Dict[str, bool]:
        """
        Verify VM storage integrity.

        Checks that all storage files registered for a VM actually exist on disk.
        Reports any missing files that would prevent the VM from starting.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            Dict mapping storage paths to existence status (True if exists)

        Raises:
            MaqetError: If VM doesn't exist or verification fails
        """
        try:
            # Get VM to verify it exists
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise ValueError(f"VM '{vm_id}' not found")

            # Verify storage
            result = self.lifecycle_manager.storage_registry.verify_storage_exists(vm.name)

            print(f"Checking storage for VM '{vm.name}'...")

            all_exist = True
            for path, exists in result.items():
                status = "exists" if exists else "MISSING"
                symbol = "[+]" if exists else "[-]"
                print(f"  {symbol} {path} ({status})")
                if not exists:
                    all_exist = False

            print()
            if all_exist:
                print("All storage verified")
            else:
                print("WARNING: Some storage files are missing")
                print("VM may fail to start until storage is restored")

            return result

        except ValueError as e:
            raise MaqetError(str(e))
        except Exception as e:
            raise MaqetError(f"Failed to verify storage: {e}")

    @api_method(
        cli_name="cleanup",
        description="Clean up orphaned and corrupted VMs",
        category="vm",
        examples=[
            "maqet cleanup",
            "maqet cleanup --dry-run",
            "maqet cleanup --force",
        ],
    )
    def cleanup_vms(
        self,
        dry_run: bool = False,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Clean up VMs with dead processes and stale metadata.

        Note: Exposed as 'cleanup' CLI command via cli_name parameter.
        Internal name is cleanup_vms() to avoid collision with cleanup()
        context manager method.

        Finds VMs with status "corrupted" or "orphaned" and cleans them by:
        - Killing orphaned QEMU processes if alive
        - Updating database to stopped status
        - Clearing PIDs and socket paths
        - Removing stale socket files

        Args:
            dry_run: Show what would be cleaned without making changes
            force: Clean up without confirmation

        Returns:
            Dict with cleanup statistics

        Examples:
            cleanup()  # Interactive cleanup
            cleanup(dry_run=True)  # Preview what would be cleaned
            cleanup(force=True)  # Skip confirmation
        """
        # Find problematic VMs
        all_vms = self.vm_manager.list_vms(validate_status=True)

        corrupted = [vm for vm in all_vms if vm.status in ("corrupted", "orphaned")]

        if not corrupted:
            return {
                "message": "No cleanup needed - all VMs are healthy",
                "cleaned": 0,
            }

        print(f"Found {len(corrupted)} VM(s) requiring cleanup:")
        print()

        for vm in corrupted:
            print(f"  - {vm.name} ({vm.status})")
            if vm.pid:
                alive = "alive" if self.state_manager._is_process_alive(vm.pid) else "dead"
                print(f"    QEMU PID: {vm.pid} ({alive})")
            if vm.runner_pid:
                alive = "alive" if self.state_manager._is_process_alive(vm.runner_pid) else "dead"
                print(f"    Runner PID: {vm.runner_pid} ({alive})")

        print()

        if dry_run:
            print("Dry-run mode: No changes made")
            return {"cleaned": 0, "dry_run": True}

        # Confirmation
        if not force:
            try:
                confirm = input("Clean up these VMs? [y/N]: ")
                if confirm.lower() != "y":
                    return {"message": "Cancelled", "cleaned": 0}
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled")
                return {"message": "Cancelled", "cleaned": 0}

        # Perform cleanup
        cleaned_count = 0
        for vm in corrupted:
            try:
                # Kill orphaned QEMU if needed
                if vm.pid and self.state_manager._is_process_alive(vm.pid):
                    self.vm_manager._terminate_orphaned_qemu(
                        vm.pid, vm.id, vm.name, force=True
                    )

                # Update database to stopped
                self.state_manager.update_vm_status(
                    vm.name,
                    "stopped",
                    pid=None,
                    runner_pid=None,
                    socket_path=None,
                    qmp_socket_path=None,
                )

                # Remove stale socket files
                if vm.socket_path:
                    socket_file = Path(vm.socket_path)
                    if socket_file.exists():
                        socket_file.unlink()

                print(f"  Cleaned: {vm.name}")
                cleaned_count += 1

            except Exception as e:
                print(f"  Failed to clean {vm.name}: {e}")

        return {
            "message": f"Cleaned {cleaned_count} VM(s)",
            "cleaned": cleaned_count,
        }

    @api_method(
        cli_name="doctor",
        description="Run health checks and diagnostics",
        category="vm",
        examples=[
            "maqet doctor",
            "maqet doctor --fix",
        ],
    )
    def doctor(self, fix: bool = False) -> Dict[str, Any]:
        """
        Run comprehensive health checks on maqet installation and VMs.

        Checks:
        - Database connectivity
        - Ghost VMs (corrupted/orphaned)
        - Stale socket files
        - QEMU binary availability

        Args:
            fix: Attempt to fix issues automatically (runs cleanup)

        Returns:
            Dict with diagnostic results

        Examples:
            doctor()  # Run checks only
            doctor(fix=True)  # Run checks and fix issues
        """
        print("Running maqet health checks...\n")

        results = {
            "checks": [],
            "errors": [],
            "warnings": [],
            "info": [],
        }

        # Check 1: Database connectivity
        print("Database: Checking connectivity...")
        try:
            self.state_manager.list_vms()
            results["checks"].append("database_ok")
            print("  Database accessible")
        except Exception as e:
            results["errors"].append(f"Database error: {e}")
            print(f"  Database error: {e}")

        # Check 2: Ghost VMs
        print("\nVMs: Checking for corrupted entries...")
        all_vms = self.vm_manager.list_vms(validate_status=True)
        corrupted = [vm for vm in all_vms if vm.status in ("corrupted", "orphaned")]

        if corrupted:
            results["warnings"].append(f"{len(corrupted)} corrupted VM(s) found")
            print(f"  Found {len(corrupted)} corrupted VM(s):")
            for vm in corrupted:
                print(f"    - {vm.name} ({vm.status})")

            if fix:
                print("\n  Attempting automatic fix...")
                cleanup_result = self.cleanup_vms(force=True)
                results["info"].append(f"Cleaned {cleanup_result['cleaned']} VM(s)")
        else:
            results["checks"].append("vms_ok")
            print("  No corrupted VMs found")

        # Check 3: Stale socket files
        print("\nFiles: Checking for stale sockets...")
        socket_dir = self.state_manager.xdg.sockets_dir
        if socket_dir.exists():
            stale_sockets = []
            for sock_file in socket_dir.glob("*.sock"):
                # Check if any VM references this socket
                vm_using = any(
                    vm.socket_path == str(sock_file)
                    for vm in all_vms
                    if vm.socket_path
                )
                if not vm_using:
                    stale_sockets.append(sock_file)

            if stale_sockets:
                results["warnings"].append(f"{len(stale_sockets)} stale socket(s)")
                print(f"  Found {len(stale_sockets)} stale socket file(s)")
                if fix:
                    for sock in stale_sockets:
                        sock.unlink()
                    results["info"].append(f"Removed {len(stale_sockets)} stale socket(s)")
            else:
                results["checks"].append("sockets_ok")
                print("  No stale sockets")

        # Check 4: QEMU binary availability
        print("\nQEMU: Checking binary availability...")
        try:
            import shutil
            qemu_bin = shutil.which("qemu-system-x86_64")
            if qemu_bin:
                results["checks"].append("qemu_found")
                results["info"].append(f"QEMU binary: {qemu_bin}")
                print(f"  QEMU found: {qemu_bin}")
            else:
                results["warnings"].append("QEMU binary not in PATH")
                print("  QEMU not found in PATH")
        except Exception as e:
            results["errors"].append(f"QEMU check failed: {e}")

        # Summary
        print("\n" + "=" * 60)
        if results["errors"]:
            print(f"{len(results['errors'])} error(s) found")
        elif results["warnings"]:
            print(f"{len(results['warnings'])} warning(s), but system functional")
        else:
            print("All checks passed - system healthy")
        print("=" * 60)

        return results

    def cli(self, args: Optional[List[str]] = None) -> Any:
        """
        Run CLI interface using CLIGenerator.

        Uses instance-specific API registry for isolated command generation.

        Args:
            args: Command line arguments (defaults to sys.argv[1:])

        Returns:
            Result of CLI command execution
        """
        # Use instance-specific registry (falls back to global if not available)
        registry = getattr(self, '_api_registry', API_REGISTRY)
        generator = CLIGenerator(self, registry)
        return generator.run(args)

    def __call__(self, method_name: str, **kwargs) -> Any:
        """
        Direct Python API access.

        Args:
            method_name: Method to execute
            **kwargs: Method parameters

        Returns:
            Method execution result
        """
        generator = PythonAPIGenerator(self, API_REGISTRY)
        return generator.execute_method(method_name, **kwargs)

    def python_api(self):
        """
        Get Python API interface.

        Returns:
            PythonAPIInterface for direct method access
        """
        generator = PythonAPIGenerator(self, API_REGISTRY)
        return generator.generate()

    # Backward compatibility: delegate private helper methods to VMManager
    # These are kept for existing tests that access private methods

    def _check_process_alive(self, vm_id: str, vm: VMInstance) -> bool:
        """Delegate to VMManager (backward compatibility)."""
        return self.vm_manager._check_process_alive(vm_id, vm)

    def _get_config_summary(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to VMManager (backward compatibility)."""
        return self.vm_manager._get_config_summary(config_data)

    def _get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Delegate to VMManager (backward compatibility)."""
        return self.vm_manager._get_process_info(pid)

    @property
    def _machines(self) -> Dict[str, Any]:
        """
        Backward compatibility property for tests.

        Returns VMManager's machine cache.
        Direct modification is discouraged - use VMManager methods instead.
        """
        return self.vm_manager.get_machine_cache()


# NOTE: API methods are automatically registered via AutoRegisterAPI
# inheritance
# No manual register_class_methods() call needed!

# NOTE: Line length compliance is now enforced by black formatter
