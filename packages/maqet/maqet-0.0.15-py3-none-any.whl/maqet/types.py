"""
Type definitions for MAQET VM automation framework.

Provides TypedDict classes for type-safe configuration and parameter passing.
All fields are optional (total=False) to allow partial configuration.
"""

from typing import Any, Dict, List, Literal
from typing_extensions import NotRequired, TypedDict


class VMConfigParams(TypedDict, total=False):
    """
    Parameters for VM configuration.

    Used when creating or configuring VMs via add() method or YAML config files.
    All fields are optional to support flexible configuration composition.

    These fields match the actual config keys used by maqet's config_handlers.

    Examples:
        Basic VM:
            config = VMConfigParams(
                memory='2G',
                cpu=2,
                storage=[{'name': 'disk', 'size': '20G', 'type': 'qcow2'}]
            )

        Advanced VM with custom binary:
            config = VMConfigParams(
                binary='/usr/bin/qemu-system-x86_64',
                memory='8G',
                cpu=4,
                display='none',
                storage=[{'name': 'hdd', 'size': '50G', 'type': 'qcow2'}],
                arguments=[{'enable-kvm': None}, {'m': '8G'}]
            )
    """

    # Core VM settings
    binary: NotRequired[str]
    """Path to QEMU binary (e.g., '/usr/bin/qemu-system-x86_64')"""

    memory: NotRequired[str]
    """Memory size like '2G', '512M', '4096M'"""

    cpu: NotRequired[int]
    """Number of CPU cores (config key name, maps to -smp)"""

    display: NotRequired[str]
    """Display backend (gtk, sdl, vnc, none, etc.)"""

    vga: NotRequired[str]
    """VGA adapter type (std, virtio, qxl, etc.)"""

    # Storage configuration
    storage: NotRequired[List[Dict[str, Any]]]
    """Storage device configurations (list of storage specs)"""

    # QEMU arguments
    args: NotRequired[List[str]]
    """Additional QEMU arguments (simple list format)"""

    arguments: NotRequired[List[Any]]
    """Structured QEMU arguments (dict/string format)"""

    # Legacy/convenience fields (for backward compatibility)
    cpus: NotRequired[int]
    """Alias for cpu (deprecated, use 'cpu' instead)"""

    cpu_model: NotRequired[str]
    """CPU model like 'host', 'qemu64', 'max'"""

    machine_type: NotRequired[str]
    """Machine type like 'q35', 'pc', 'virt' (ARM)"""

    disk_size: NotRequired[str]
    """Disk size (convenience, use 'storage' for full control)"""

    storage_format: NotRequired[Literal['qcow2', 'raw']]
    """Storage format (convenience, use 'storage' for full control)"""

    boot_order: NotRequired[str]
    """Boot order like 'cdn' (cdrom, disk, network)"""

    cdrom: NotRequired[str]
    """Path to ISO image for CD-ROM"""

    network: NotRequired[str]
    """Network configuration (user, bridge, none, or complex)"""

    ssh_port: NotRequired[int]
    """Host port for SSH forwarding (user mode networking)"""

    vnc_port: NotRequired[int]
    """VNC display port number"""

    enable_kvm: NotRequired[bool]
    """Enable KVM hardware acceleration"""

    extra_args: NotRequired[List[str]]
    """Alias for args (deprecated, use 'args' instead)"""


class StartParams(TypedDict, total=False):
    """
    Parameters for VM start operation.

    Controls start behavior including wait conditions.
    Used by VMManager.start() and related methods.

    Note: SSH readiness checking was removed in v0.1.0.
    See docs/MIGRATION_v0.1.0.md for alternatives.

    Examples:
        Start with custom timeout:
            params = StartParams(
                wait_timeout=120.0
            )

        Background start (no wait):
            params = StartParams()  # All fields optional
    """

    wait_timeout: NotRequired[float]
    """Timeout in seconds for wait condition (overrides timeout parameter)"""


class QMPParams(TypedDict, total=False):
    """
    Parameters for QMP operations.

    Controls QMP command execution behavior including timeouts and blocking mode.
    Used by QMPManager and Machine QMP operations.

    Examples:
        Quick query:
            params = QMPParams(
                timeout=5.0,
                blocking=False
            )

        Long-running command:
            params = QMPParams(
                timeout=60.0,
                blocking=True
            )
    """

    timeout: NotRequired[float]
    """Command timeout in seconds"""

    blocking: NotRequired[bool]
    """Wait for command completion (default: True)"""


class SnapshotParams(TypedDict, total=False):
    """
    Parameters for snapshot operations.

    Controls snapshot creation including metadata and RAM state.
    Used by SnapshotManager and VMManager snapshot methods.

    Examples:
        Basic offline snapshot:
            params = SnapshotParams(
                name='backup-2025-12-15',
                description='Before system upgrade'
            )

        Live snapshot with RAM:
            params = SnapshotParams(
                name='running-state',
                description='VM in running state',
                include_ram=True
            )
    """

    name: NotRequired[str]
    """Snapshot name identifier"""

    description: NotRequired[str]
    """Human-readable snapshot description"""

    include_ram: NotRequired[bool]
    """Include RAM state in snapshot (live snapshots only)"""


def validate_kwargs(kwargs: dict, schema: type) -> None:
    """
    Validate kwargs against a TypedDict schema at runtime.

    Args:
        kwargs: Dictionary of keyword arguments to validate
        schema: TypedDict class to validate against

    Raises:
        ValueError: If kwargs contains keys not in schema

    Example:
        >>> validate_kwargs({'memory': '2G'}, VMConfigParams)  # OK
        >>> validate_kwargs({'invalid': True}, VMConfigParams)  # Raises ValueError
    """
    from typing import get_type_hints

    valid_keys = set(get_type_hints(schema).keys())
    actual_keys = set(kwargs.keys())

    invalid = actual_keys - valid_keys
    if invalid:
        raise ValueError(
            f"Invalid parameters: {sorted(invalid)}. "
            f"Valid parameters: {sorted(valid_keys)}"
        )
