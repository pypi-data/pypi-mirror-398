# Python API Reference

Complete Python API documentation for MAQET (M4x0n's QEMU Tool).

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [API Methods by Category](#api-methods-by-category)
  - [VM Management](#vm-management)
  - [QMP Commands](#qmp-commands)
  - [Storage & Snapshots](#storage--snapshots)
- [Advanced Usage](#advanced-usage)
- [Error Handling](#error-handling)

## Installation

```bash
# Install from PyPI
pip install maqet

# Install from source
git clone https://gitlab.com/m4x0n_24/maqet.git
cd maqet
pip install -e .

# With optional dependencies
pip install maqet  # QEMU bindings are vendored (included by default)
pip install maqet[dev]   # Development dependencies

# Note: Prior to v0.0.8, QEMU bindings required `pip install maqet[qemu]`.
# Since v0.0.8, QEMU bindings are vendored in `maqet/vendor/` and included
# automatically. No additional installation step is needed.
```

## Quick Start

```python
from maqet import Maqet

# Create MAQET instance
maqet = Maqet()

# Create VM from config file
vm_id = maqet.add(vm_config="config.yaml", name="myvm")

# Start the VM
maqet.start(vm_id)

# Get VM status
status = maqet.status(vm_id)
print(f"VM {status['name']} is {status['status']}")

# Stop the VM
maqet.stop(vm_id)

# Remove the VM
maqet.rm(vm_id, force=True)
```

## Core Concepts

### Unified API Pattern

Every MAQET method decorated with `@api_method` is available as:

- **Python API method**: `maqet.start("myvm")`
- **CLI command**: `maqet start myvm`
- **Configuration option**: Via YAML config files

### Data Directory Management

MAQET follows XDG Base Directory specification:

```python
# Use default XDG directories
maqet = Maqet()  # Data in ~/.local/share/maqet/

# Override data directory
maqet = Maqet(data_dir="/custom/path")
```

### Context Manager Support

```python
# Automatic cleanup on exit
with Maqet() as maqet:
    vm_id = maqet.add(vm_config="config.yaml")
    maqet.start(vm_id)
    # VM automatically stopped on exit
```

## API Methods by Category

### VM Management

#### `add()`

Create a new virtual machine from configuration file(s) or parameters.

```python
def add(
    self,
    vm_config: Optional[Union[str, List[str]]] = None,
    name: Optional[str] = None,
    empty: bool = False,
    **kwargs
) -> str
```

**Parameters:**

- `vm_config` (str or list, optional): Path to YAML configuration file, or list of config files for deep-merge
- `name` (str, optional): VM name (auto-generated if not provided)
- `empty` (bool, default=False): Create empty VM without any configuration
- `**kwargs`: Additional VM configuration parameters (memory, cpu, etc.)

**Returns:**

- `str`: VM instance ID

**Raises:**

- `MaqetError`: If VM creation fails or configuration is invalid

**Examples:**

```python
# Create VM from single config file
vm_id = maqet.add(vm_config="vm.yaml", name="myvm")

# Deep-merge multiple config files
vm_id = maqet.add(vm_config=["base.yaml", "custom.yaml"], name="production-vm")

# Create VM with parameters
vm_id = maqet.add(name="test-vm", memory="4G", cpu=2)

# Combine config file with parameter overrides
vm_id = maqet.add(vm_config="base.yaml", memory="8G", cpu=4)

# Create empty placeholder VM
vm_id = maqet.add(name="placeholder", empty=True)
```

**When to use:**

- Creating new VMs from configuration templates
- Setting up multiple VMs with similar configurations (using config merge)
- Creating placeholder VMs to configure later (with `empty=True`)

---

#### `start()`

Start a virtual machine and wait for it to be ready.

```python
def start(self, vm_id: str) -> VMInstance
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)

**Returns:**

- `VMInstance`: VM instance information with updated status

**Raises:**

- `MaqetError`: If VM not found, already running, or start fails

**Examples:**

```python
# Start VM by name
vm = maqet.start("myvm")
print(f"VM started with PID {vm.pid}")

# Start VM by ID
vm = maqet.start("550e8400-e29b-41d4-a716-446655440000")
```

**When to use:**

- Starting VMs created with `add()`
- Restarting stopped VMs
- Python API automation (for CLI, use daemon mode for QMP support)

---

#### `stop()`

Stop a virtual machine gracefully or forcefully.

```python
def stop(
    self,
    vm_id: str,
    force: bool = False,
    timeout: int = 30
) -> VMInstance
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `force` (bool, default=False): Force kill if graceful shutdown fails
- `timeout` (int, default=30): Timeout for graceful shutdown in seconds

**Returns:**

- `VMInstance`: VM instance information with updated status

**Raises:**

- `MaqetError`: If VM not found, not running, or stop fails

**Examples:**

```python
# Graceful shutdown (default)
maqet.stop("myvm")

# Force kill immediately
maqet.stop("myvm", force=True)

# Custom timeout for graceful shutdown
maqet.stop("myvm", timeout=60)
```

**When to use:**

- Gracefully shutting down VMs (without `force`)
- Emergency VM termination (with `force=True`)
- Cleanup in exception handlers

---

#### `rm()`

Remove a virtual machine completely from the system.

```python
def rm(
    self,
    vm_id: Optional[str] = None,
    force: bool = False,
    all: bool = False,
    clean_storage: bool = False
) -> bool
```

**Parameters:**

- `vm_id` (str, optional): VM identifier (name or ID), required unless `all=True`
- `force` (bool, default=False): Force removal even if VM is running
- `all` (bool, default=False): Remove all virtual machines
- `clean_storage` (bool, default=False): Also delete associated storage files

**Returns:**

- `bool`: True if removed successfully

**Raises:**

- `MaqetError`: If VM not found, removal fails, or invalid arguments

**Examples:**

```python
# Remove stopped VM
maqet.rm("myvm")

# Force remove running VM
maqet.rm("myvm", force=True)

# Remove VM and delete storage files
maqet.rm("myvm", force=True, clean_storage=True)

# Remove all VMs (with confirmation prompt)
maqet.rm(all=True)

# Force remove all VMs without confirmation
maqet.rm(all=True, force=True)
```

**When to use:**

- Cleaning up test VMs
- Removing VMs completely (with `clean_storage=True`)
- Bulk cleanup operations (with `all=True`)

---

#### `ls()`

List virtual machines in table format.

```python
def ls(self, status: Optional[str] = None) -> str
```

**Parameters:**

- `status` (str, optional): Filter by status ('running', 'stopped', 'created', 'failed')

**Returns:**

- `str`: Formatted table string

**Examples:**

```python
# List all VMs
print(maqet.ls())

# List only running VMs
print(maqet.ls(status="running"))

# List stopped VMs
print(maqet.ls(status="stopped"))
```

**Output:**

```
NAME                 STATUS     PID
----------------------------------------
myvm                 running    12345
testvm               stopped    -
```

**When to use:**

- Viewing all managed VMs
- Filtering VMs by status
- Generating reports

---

#### `status()`

Get comprehensive status information for a VM.

```python
def status(self, vm_id: str, detailed: bool = False) -> Dict[str, Any]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `detailed` (bool, default=False): Include detailed process and resource information

**Returns:**

- `dict`: Dictionary with comprehensive VM status information

**Raises:**

- `MaqetError`: If VM not found

**Examples:**

```python
# Basic status
status = maqet.status("myvm")
print(f"VM: {status['name']}")
print(f"Status: {status['status']}")
print(f"PID: {status['pid']}")

# Detailed status (requires psutil)
status = maqet.status("myvm", detailed=True)
if 'process' in status:
    print(f"CPU: {status['process']['cpu_percent']}%")
    print(f"Memory: {status['process']['memory_info']['rss']} bytes")
```

**Response structure:**

```python
{
    'vm_id': 'uuid-string',
    'name': 'myvm',
    'status': 'running',
    'is_running': True,
    'is_empty': False,
    'pid': 12345,
    'created_at': '2024-10-08T10:00:00',
    'updated_at': '2024-10-08T10:05:00',
    'config_path': '/path/to/config.yaml',
    'socket_path': '/run/user/1000/maqet/sockets/myvm.sock',
    'configuration': {
        'binary': '/usr/bin/qemu-system-x86_64',
        'memory': '4G',
        'cpu': 2,
        'display': 'gtk',
        'storage_count': 2,
        'storage_devices': [
            {'name': 'hdd', 'type': 'qcow2', 'size': '20G'},
            {'name': 'cdrom', 'type': 'raw', 'size': 'unknown'}
        ]
    },
    'qmp_socket': {
        'path': '/run/user/1000/maqet/sockets/myvm.sock',
        'exists': True
    },
    'snapshots': {  # Only in detailed mode
        'hdd': {
            'snapshot_count': 2,
            'snapshots': ['backup1', 'backup2']
        }
    },
    'process': {  # Only in detailed mode with psutil
        'cpu_percent': 5.2,
        'memory_info': {'rss': 1048576, 'vms': 2097152},
        'create_time': 1696766400.0,
        'cmdline': ['/usr/bin/qemu-system-x86_64', '-m', '4G', ...],
        'status': 'running'
    }
}
```

**When to use:**

- Getting basic VM status (running/stopped, PID, timestamps)
- Quick status checks in automation scripts
- Checking if VM is empty (created with `--empty` flag)

**Deprecation Notice:**

- The `detailed=True` parameter is DEPRECATED and will be removed in a future version
- For configuration details, use `info()` method instead
- For detailed inspection with process info, use `inspect()` method instead

**See Also:** `info()` for configuration details, `inspect()` for comprehensive inspection

---

#### `info()`

Get VM configuration details without runtime process information.

```python
def info(self, vm_id: str) -> Dict[str, Any]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)

**Returns:**

- `dict`: VM configuration summary including:
  - `vm_id`: VM unique identifier
  - `name`: VM name
  - `config_path`: Path to configuration file (if any)
  - `config_data`: Full configuration dictionary
  - `configuration`: Parsed configuration summary (binary, memory, CPU, storage)

**Raises:**

- `MaqetError`: If VM not found

**Examples:**

```python
# Get VM configuration
config = maqet.info("myvm")
print(f"Binary: {config['configuration']['binary']}")
print(f"Memory: {config['configuration']['memory']}")
print(f"CPU: {config['configuration']['cpu']}")
print(f"Storage devices: {config['configuration']['storage_count']}")

# Inspect storage devices
for device in config['configuration']['storage_devices']:
    print(f"Device: {device['name']} ({device['type']})")
    print(f"  Size: {device['size']}")
    print(f"  Interface: {device['interface']}")

# Access raw config data
if 'arguments' in config['config_data']:
    print(f"QEMU arguments: {config['config_data']['arguments']}")
```

**Response structure:**

```python
{
    'vm_id': 'uuid-string',
    'name': 'myvm',
    'config_path': '/path/to/config.yaml',
    'config_data': {
        'binary': '/usr/bin/qemu-system-x86_64',
        'memory': '4G',
        'cpu': 2,
        'arguments': [...],
        'storage': [...]
    },
    'configuration': {
        'binary': '/usr/bin/qemu-system-x86_64',
        'memory': '4G',
        'cpu': 2,
        'display': 'gtk',
        'storage_count': 2,
        'storage_devices': [
            {
                'name': 'hdd',
                'type': 'qcow2',
                'size': '20G',
                'interface': 'virtio',
                'file': '/path/to/disk.qcow2'
            },
            {
                'name': 'cdrom',
                'type': 'raw',
                'size': 'unknown',
                'interface': 'sata',
                'file': '/path/to/install.iso'
            }
        ]
    }
}
```

**When to use:**

- Getting VM configuration details (binary, memory, CPU, storage)
- Checking resource allocation before starting VM
- Inspecting storage device configuration
- Validating VM configuration after creation
- When you don't need runtime process information

**See Also:** `inspect()` for detailed runtime information, `status()` for basic status

---

#### `inspect()`

Perform comprehensive inspection of a VM including configuration, process details, and resource usage.

```python
def inspect(self, vm_id: str) -> Dict[str, Any]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)

**Returns:**

- `dict`: Comprehensive VM inspection data including:
  - Basic status information (VM ID, name, status, PID)
  - Configuration summary (binary, memory, CPU, storage)
  - Process details (CPU usage, memory, uptime) if VM is running
  - QMP socket status and path
  - Timestamps (created_at, updated_at)

**Raises:**

- `MaqetError`: If VM not found

**Examples:**

```python
# Comprehensive VM inspection
details = maqet.inspect("myvm")
print(f"VM: {details['name']} ({details['status']})")
print(f"PID: {details['pid']}")
print(f"Binary: {details['configuration']['binary']}")
print(f"Memory: {details['configuration']['memory']}")

# Check process details (only if running)
if 'process' in details:
    proc = details['process']
    print(f"CPU: {proc['cpu_percent']}%")
    print(f"Memory: {proc['memory_info']['rss']} bytes")
    print(f"Uptime: {proc['create_time']}")
    print(f"Threads: {proc['num_threads']}")
    print(f"Command: {' '.join(proc['cmdline'])}")

# Check QMP socket status
qmp = details['qmp_socket']
print(f"QMP socket: {qmp['path']}")
print(f"Socket exists: {qmp['exists']}")

# Monitor resource usage
import time
while True:
    details = maqet.inspect("myvm")
    if 'process' in details:
        print(f"CPU: {details['process']['cpu_percent']}%")
    time.sleep(5)
```

**Response structure:**

```python
{
    'vm_id': 'uuid-string',
    'name': 'myvm',
    'status': 'running',
    'is_running': True,
    'pid': 12345,
    'socket_path': '/run/user/1000/maqet/sockets/myvm.sock',
    'config_path': '/path/to/config.yaml',
    'created_at': '2024-10-08T10:00:00',
    'updated_at': '2024-10-08T10:05:00',
    'configuration': {
        'binary': '/usr/bin/qemu-system-x86_64',
        'memory': '4G',
        'cpu': 2,
        'display': 'gtk',
        'storage_count': 2,
        'storage_devices': [...]
    },
    'process': {  # Only present if VM is running and psutil available
        'cpu_percent': 5.2,
        'memory_info': {
            'rss': 1048576,      # Resident Set Size
            'vms': 2097152       # Virtual Memory Size
        },
        'create_time': 1696766400.0,
        'num_threads': 8,
        'cmdline': ['/usr/bin/qemu-system-x86_64', '-m', '4G', ...],
        'status': 'running'
    },
    'qmp_socket': {
        'path': '/run/user/1000/maqet/sockets/myvm.sock',
        'exists': True
    }
}
```

**When to use:**

- Monitoring VM resource usage (CPU, memory)
- Debugging VM issues with full process details
- Checking QMP socket connectivity
- Validating VM is running correctly
- Performance monitoring and troubleshooting
- Comprehensive health checks

**Note:**

- Process details require VM to be running
- Process information requires `psutil` package (optional dependency)
- If VM status is "running" but process doesn't exist, status is auto-corrected to "stopped"

**See Also:** `status()` for basic status, `info()` for configuration-only details

---

#### `apply()`

Apply configuration to existing VM, or create it if it doesn't exist.

```python
def apply(
    self,
    vm_id: str,
    vm_config: Optional[Union[str, List[str]]] = None,
    **kwargs
) -> VMInstance
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `vm_config` (str or list, optional): Path to configuration file, or list of config files for deep-merge
- `**kwargs`: Configuration parameters to update

**Returns:**

- `VMInstance`: VM instance (created or updated)

**Raises:**

- `MaqetError`: If configuration is invalid or operation fails

**Examples:**

```python
# Apply config file to existing VM
vm = maqet.apply("myvm", vm_config="updated.yaml")

# Update specific parameters
vm = maqet.apply("myvm", memory="8G", cpu=4)

# Merge multiple configs and parameters
vm = maqet.apply("myvm", vm_config=["base.yaml", "prod.yaml"], memory="16G")

# Create VM if it doesn't exist
vm = maqet.apply("newvm", vm_config="config.yaml")
```

**When to use:**

- Updating VM configuration without recreating
- Applying configuration changes to existing VMs
- Merging multiple configuration sources
- Idempotent VM creation (creates if missing, updates if exists)

---

### QMP Commands

#### `qmp()`

Execute raw QMP command on a running VM.

```python
def qmp(self, vm_id: str, command: str, **kwargs) -> Dict[str, Any]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `command` (str): QMP command to execute (e.g., 'system_powerdown')
- `**kwargs`: Command parameters

**Returns:**

- `dict`: QMP command result

**Raises:**

- `MaqetError`: If VM not found, not running, or command fails

**Examples:**

```python
# Power down VM
result = maqet.qmp("myvm", "system_powerdown")

# Query VM status
result = maqet.qmp("myvm", "query-status")
print(result)  # {'status': 'running', 'running': True}

# Query block devices
result = maqet.qmp("myvm", "query-block")
```

**When to use:**

- Executing custom QMP commands not wrapped by MAQET
- Direct QEMU control via QMP protocol
- Advanced automation requiring QMP access

**Note:** QMP only works within the same Python process. For CLI usage, use daemon mode.

---

#### `qmp_key()`

Send key combination to VM via QMP.

```python
def qmp_key(
    self,
    vm_id: str,
    *keys: str,
    hold_time: int = 100
) -> Dict[str, Any]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `*keys` (str): Key names to press (e.g., 'ctrl', 'alt', 'f2')
- `hold_time` (int, default=100): How long to hold keys in milliseconds

**Returns:**

- `dict`: QMP command result

**Raises:**

- `MaqetError`: If VM not found or command fails

**Examples:**

```python
# Switch to TTY2
maqet.qmp_key("myvm", "ctrl", "alt", "f2")

# Send Ctrl+C
maqet.qmp_key("myvm", "ctrl", "c")

# Custom hold time
maqet.qmp_key("myvm", "ctrl", "alt", "delete", hold_time=200)

# Function keys
maqet.qmp_key("myvm", "f1")
maqet.qmp_key("myvm", "shift", "f10")
```

**Available keys:** See [QMP Commands Guide](../user-guide/qmp-commands.md) for complete key list.

**When to use:**

- VM automation requiring keyboard input
- Switching TTYs in VMs
- Sending keyboard shortcuts
- Testing keyboard handling in guests

---

#### `qmp_type()`

Type text string to VM via QMP.

```python
def qmp_type(
    self,
    vm_id: str,
    text: str,
    hold_time: int = 100
) -> List[Dict[str, Any]]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `text` (str): Text to type
- `hold_time` (int, default=100): How long to hold each key in milliseconds

**Returns:**

- `list`: List of QMP command results (one per character)

**Raises:**

- `MaqetError`: If VM not found or command fails

**Examples:**

```python
# Type username and password
maqet.qmp_type("myvm", "root")
maqet.qmp_key("myvm", "ret")
maqet.qmp_type("myvm", "mypassword")
maqet.qmp_key("myvm", "ret")

# Type command
maqet.qmp_type("myvm", "ls -la /home")
maqet.qmp_key("myvm", "ret")

# Slower typing for compatibility
maqet.qmp_type("myvm", "sensitive-command", hold_time=150)
```

**When to use:**

- Automated VM configuration via shell
- Testing input handling
- Scripting guest OS operations
- Automated installations

---

#### `screendump()`

Take screenshot of VM screen.

```python
def screendump(self, vm_id: str, filename: str) -> Dict[str, Any]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `filename` (str): Output filename for screenshot (PPM format)

**Returns:**

- `dict`: QMP command result

**Raises:**

- `MaqetError`: If VM not found or command fails

**Examples:**

```python
# Take screenshot
maqet.screendump("myvm", "screenshot.ppm")

# Sequential screenshots
import time
for i in range(5):
    maqet.screendump("myvm", f"screen_{i:03d}.ppm")
    time.sleep(2)

# Convert to PNG using PIL
from PIL import Image
maqet.screendump("myvm", "temp.ppm")
img = Image.open("temp.ppm")
img.save("screenshot.png")
```

**When to use:**

- Visual VM monitoring
- Automated testing with screenshot validation
- Debugging display issues
- Creating VM usage documentation

---

#### `qmp_stop()` / `qmp_cont()`

Pause and resume VM execution via QMP.

```python
def qmp_stop(self, vm_id: str) -> Dict[str, Any]
def qmp_cont(self, vm_id: str) -> Dict[str, Any]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)

**Returns:**

- `dict`: QMP command result

**Examples:**

```python
# Pause VM execution
maqet.qmp_stop("myvm")

# Resume VM execution
maqet.qmp_cont("myvm")

# Pause, take snapshot, resume
maqet.qmp_stop("myvm")
maqet.snapshot("myvm", "create", "hdd", "paused-state")
maqet.qmp_cont("myvm")
```

**When to use:**

- Taking consistent snapshots
- Freezing VM state for inspection
- Debugging guest OS issues

---

#### `device_add()` / `device_del()`

Hot-plug and hot-unplug devices to/from VM.

```python
def device_add(
    self,
    vm_id: str,
    driver: str,
    device_id: str,
    **kwargs
) -> Dict[str, Any]

def device_del(self, vm_id: str, device_id: str) -> Dict[str, Any]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `driver` (str): Device driver name (e.g., 'usb-storage', 'e1000')
- `device_id` (str): Unique device identifier
- `**kwargs`: Additional device properties

**Returns:**

- `dict`: QMP command result

**Examples:**

```python
# Add USB storage device
maqet.device_add("myvm", driver="usb-storage", device_id="usb1", drive="usb-drive")

# Add network device
maqet.device_add("myvm", driver="e1000", device_id="net1", netdev="user1")

# Remove device
maqet.device_del("myvm", "usb1")
```

**When to use:**

- Adding storage devices without restarting VM
- Network device hot-plugging
- Testing device driver behavior

---

### Storage & Snapshots

#### `snapshot()`

Manage VM storage snapshots with subcommand interface.

```python
def snapshot(
    self,
    vm_id: str,
    action: str,
    drive: str,
    name: Optional[str] = None,
    overwrite: bool = False
) -> Union[Dict[str, Any], List[str]]
```

**Parameters:**

- `vm_id` (str): VM identifier (name or ID)
- `action` (str): Snapshot action ('create', 'load', 'list')
- `drive` (str): Storage drive name
- `name` (str, optional): Snapshot name (required for create/load)
- `overwrite` (bool, default=False): Overwrite existing snapshot (create only)

**Returns:**

- `dict`: Operation result (for create/load)
- `list`: Snapshot names (for list)

**Raises:**

- `MaqetError`: If VM not found or snapshot operation fails

**Examples:**

```python
# Create snapshot
result = maqet.snapshot("myvm", "create", "hdd", "backup1")
print(result)
# {'status': 'success', 'operation': 'create', 'vm_id': '...',
#  'drive': 'hdd', 'snapshot': 'backup1', 'overwrite': False}

# Overwrite existing snapshot
maqet.snapshot("myvm", "create", "hdd", "backup1", overwrite=True)

# Load snapshot
maqet.snapshot("myvm", "load", "hdd", "backup1")

# List snapshots
snapshots = maqet.snapshot("myvm", "list", "hdd")
print(snapshots)  # ['backup1', 'backup2', 'pre-update']
```

**When to use:**

- Creating backups before risky operations
- Testing configurations with easy rollback
- Maintaining multiple VM states
- Automation workflows requiring state preservation

**Note:** Only QCOW2 storage devices support snapshots.

---

## Advanced Usage

### Multiple VM Orchestration

```python
from maqet import Maqet

with Maqet() as maqet:
    # Create multiple VMs
    vms = []
    for i in range(3):
        vm_id = maqet.add(
            vm_config="base.yaml",
            name=f"cluster-{i}",
            memory=f"{4 + i}G"
        )
        vms.append(vm_id)

    # Start all VMs
    for vm_id in vms:
        maqet.start(vm_id)

    # Perform operations
    for vm_id in vms:
        status = maqet.status(vm_id)
        print(f"{status['name']}: {status['status']}")

    # Cleanup happens automatically on exit
```

### Automated VM Configuration

```python
def configure_vm(maqet, vm_id):
    """Configure VM via QMP keyboard automation."""
    # Wait for boot
    import time
    time.sleep(10)

    # Login
    maqet.qmp_type(vm_id, "root")
    maqet.qmp_key(vm_id, "ret")
    maqet.qmp_type(vm_id, "password")
    maqet.qmp_key(vm_id, "ret")

    # Run commands
    commands = [
        "ip addr show",
        "systemctl status",
        "poweroff"
    ]

    for cmd in commands:
        maqet.qmp_type(vm_id, cmd)
        maqet.qmp_key(vm_id, "ret")
        time.sleep(2)

        # Take screenshot
        maqet.screendump(vm_id, f"cmd_{cmd.replace(' ', '_')}.ppm")

# Usage
with Maqet() as maqet:
    vm_id = maqet.add(vm_config="test.yaml", name="automation-test")
    maqet.start(vm_id)
    configure_vm(maqet, vm_id)
```

### Snapshot-Based Testing

```python
def test_with_snapshots(maqet, vm_id):
    """Test multiple configurations with snapshot rollback."""
    # Create base snapshot
    maqet.snapshot(vm_id, "create", "hdd", "base-state")

    configs = [
        {"memory": "4G", "cpu": 2},
        {"memory": "8G", "cpu": 4},
        {"memory": "16G", "cpu": 8}
    ]

    results = []
    for config in configs:
        # Apply configuration
        maqet.apply(vm_id, **config)
        maqet.start(vm_id)

        # Run tests
        result = run_performance_test(maqet, vm_id)
        results.append(result)

        # Stop and rollback
        maqet.stop(vm_id)
        maqet.snapshot(vm_id, "load", "hdd", "base-state")

    return results
```

### Configuration Deep-Merge

```python
# Create VM with merged configurations
vm_id = maqet.add(
    vm_config=["base.yaml", "environment/production.yaml", "overrides.yaml"],
    name="prod-server",
    memory="32G"  # Final override via parameter
)
```

Merge order (later overrides earlier):

1. base.yaml
2. environment/production.yaml
3. overrides.yaml
4. Keyword arguments (memory="32G")

## Error Handling

### Exception Hierarchy

```python
MaqetError                    # Base exception
├── StateManagerError         # Database/state errors
├── ConfigError              # Configuration errors
├── SnapshotError            # Snapshot operation errors
└── StorageError             # Storage operation errors
```

### Best Practices

```python
from maqet import Maqet, MaqetError

try:
    with Maqet() as maqet:
        vm_id = maqet.add(vm_config="config.yaml", name="myvm")
        maqet.start(vm_id)

        # ... operations ...

except MaqetError as e:
    print(f"MAQET error: {e}")
    # Handle gracefully
except Exception as e:
    print(f"Unexpected error: {e}")
    # Log and exit
```

### Graceful Cleanup

```python
maqet = Maqet()
vm_id = None

try:
    vm_id = maqet.add(vm_config="config.yaml")
    maqet.start(vm_id)
    # ... operations ...
except Exception as e:
    print(f"Error: {e}")
finally:
    if vm_id:
        try:
            maqet.stop(vm_id, force=True)
            maqet.rm(vm_id, force=True)
        except:
            pass  # Best effort cleanup
```

### Retry Logic

```python
import time
from maqet import Maqet, MaqetError

def start_with_retry(maqet, vm_id, max_retries=3):
    """Start VM with retry on failure."""
    for attempt in range(max_retries):
        try:
            return maqet.start(vm_id)
        except MaqetError as e:
            if attempt < max_retries - 1:
                print(f"Start failed (attempt {attempt + 1}), retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface documentation
- [Examples](examples.md) - Practical code examples
- [QMP Commands](../user-guide/qmp-commands.md) - QMP command reference
- [Configuration Guide](../user-guide/configuration.md) - YAML configuration details
