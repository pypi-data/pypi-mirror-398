# CLI Reference

Complete command-line interface reference for MAQET (M4x0n's QEMU Tool).

## Table of Contents

- [Global Options](#global-options)
- [Command Categories](#command-categories)
  - [VM Management](#vm-management)
  - [QMP Commands](#qmp-commands)
  - [Storage & Snapshots](#storage--snapshots)
- [Exit Codes](#exit-codes)
- [Shell Integration](#shell-integration)

## Global Options

Global options can be used with any command.

### `-v, --verbose`

Increase verbosity level. Can be specified multiple times for progressively more output.

```bash
maqet start myvm           # Default: errors only
maqet -v start myvm        # Show warnings
maqet -vv start myvm       # Show info messages
maqet -vvv start myvm      # Show debug output
```

**Verbosity levels:**

- Default (no `-v`): Shows errors and critical messages only (silent on success)
- `-v`: Shows warnings + errors
- `-vv`: Shows info + warnings + errors
- `-vvv` or more: Shows debug + info + warnings + errors

Note: The `-q/--quiet` flag has been removed in favor of the quiet-by-default behavior (no `-v` flag).

### `--maqet-data-dir PATH`

Override default XDG data directory.

```bash
maqet --maqet-data-dir /tmp/maqet-data add vm.yaml
```

**Default:** `~/.local/share/maqet/`

### `--migrate-force`

Force database migration without automatic detection.

```bash
maqet --migrate-force
```

**Usage**: Run this when you want to force database schema migration manually, bypassing the automatic migration system.

**Deprecated Alias**: `--force-migrate` (will be removed in v1.0.0)

**Note**: This flag was renamed from `--force-migrate` to `--migrate-force` in v0.1.0 to avoid conflicts with subcommand `--force` flags.

### `--log-file PATH`

Enable file logging. Logs are always at DEBUG level.

```bash
maqet --log-file /tmp/maqet.log start myvm
tail -f /tmp/maqet.log
```

### `--version, -V`

Display MAQET version and exit.

```bash
maqet --version
# Output: MAQET version 0.1.0
```

### `--debug`

Enable debug mode with full tracebacks on errors.

```bash
maqet --debug start myvm
# Shows full Python traceback on error
```

### `--format FORMAT`

Specify output format. Available formats: `auto`, `json`, `yaml`, `plain`, `table`.

```bash
maqet --format json status myvm
maqet --format table ls
```

## Command Categories

### VM Management

#### `add` - Create a new VM

Create a new virtual machine from configuration file(s) or parameters.

**Syntax:**

```bash
maqet add [OPTIONS] [CONFIG_FILES...]
```

**Options:**

- `--vm-config PATH`: Path to YAML configuration file (can specify multiple for merge)
- `--name NAME`: VM name (auto-generated if not provided)
- `--empty`: Create empty VM without any configuration
- `--memory SIZE`: Memory size (e.g., "4G", "2048M")
- `--cpu COUNT`: Number of CPU cores
- Any other config parameter as `--key value`

**Examples:**

```bash
# Create VM from config file (positional - preferred)
maqet add config.yaml --name myvm

# Create VM from config file (flag form)
maqet add --vm-config config.yaml --name myvm

# Create VM from multiple configs (deep-merge)
maqet add --vm-config base.yaml --vm-config custom.yaml --name myvm

# Create VM with parameters only
maqet add --name testvm --memory 4G --cpu 2

# Combine config with parameter overrides
maqet add base.yaml --memory 8G

# Create empty placeholder VM
maqet add --name empty-vm --empty
```

**Exit codes:**

- `0`: VM created successfully
- `1`: Creation failed (invalid config, missing file, etc.)

---

#### `start` - Start a VM

Start a virtual machine and wait for it to be ready.

**Syntax:**

```bash
maqet start VM_ID
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)

**Examples:**

```bash
# Start VM by name
maqet start myvm

# Start VM by UUID
maqet start 550e8400-e29b-41d4-a716-446655440000
```

**Exit codes:**

- `0`: VM started successfully
- `1`: VM not found or start failed

---

#### `stop` - Stop a VM

Stop a virtual machine gracefully or forcefully.

**Syntax:**

```bash
maqet stop [OPTIONS] VM_ID
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)

**Options:**

- `--force`: Force kill if graceful shutdown fails
- `--timeout SECONDS`: Timeout for graceful shutdown (default: 30)

**Examples:**

```bash
# Graceful shutdown
maqet stop myvm

# Force kill immediately
maqet stop myvm --force

# Custom timeout
maqet stop myvm --timeout 60
```

**Exit codes:**

- `0`: VM stopped successfully
- `1`: VM not found or stop failed

---

#### `rm` - Remove a VM

Remove a virtual machine completely.

**Syntax:**

```bash
maqet rm [OPTIONS] [VM_ID]
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID), optional if `--all` is used

**Options:**

- `--force`: Force removal even if VM is running
- `--all`: Remove all virtual machines
- `--clean-storage`: Also delete associated storage files

**Examples:**

```bash
# Remove stopped VM
maqet rm myvm

# Force remove running VM
maqet rm myvm --force

# Remove VM and delete storage
maqet rm myvm --force --clean-storage

# Remove all VMs (with confirmation)
maqet rm --all

# Force remove all VMs
maqet rm --all --force
```

**Exit codes:**

- `0`: VM(s) removed successfully
- `1`: Removal failed
- `2`: User cancelled operation

---

#### `ls` - List VMs

List virtual machines in table format.

**Syntax:**

```bash
maqet ls [OPTIONS]
```

**Options:**

- `--status STATUS`: Filter by status (running, stopped, created, failed)

**Examples:**

```bash
# List all VMs
maqet ls

# List only running VMs
maqet ls --status running

# List stopped VMs
maqet ls --status stopped
```

**Output:**

```
NAME                 STATUS     PID
----------------------------------------
myvm                 running    12345
testvm               stopped    -
production-vm        running    12346
```

**Exit codes:**

- `0`: Success (even if no VMs found)

---

#### `status` - Show VM status

Get comprehensive status information for a VM.

**Syntax:**

```bash
maqet status [OPTIONS] VM_ID
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)

**Options:**

- `--detailed`: Include detailed process and resource information

**Examples:**

```bash
# Basic status
maqet status myvm

# Detailed status with process info
maqet status myvm --detailed
```

**Output (basic):**

```json
{
  "vm_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "myvm",
  "status": "running",
  "is_running": true,
  "pid": 12345,
  "created_at": "2024-10-08T10:00:00",
  "configuration": {
    "binary": "/usr/bin/qemu-system-x86_64",
    "memory": "4G",
    "cpu": 2,
    "storage_count": 1
  }
}
```

**Exit codes:**

- `0`: Status retrieved successfully
- `1`: VM not found

**Note:** The `--detailed` flag is deprecated. Use `inspect` command instead for detailed information.

---

#### `info` - Show VM configuration

Display VM configuration details including resources and storage.

**Syntax:**

```bash
maqet info VM_ID
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)

**Examples:**

```bash
# Show VM configuration
maqet info myvm
```

**Output:**

```json
{
  "vm_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "myvm",
  "binary": "/usr/bin/qemu-system-x86_64",
  "memory": "4G",
  "cpu": 2,
  "storage_count": 1,
  "storage_devices": [
    {
      "name": "hdd",
      "type": "qcow2",
      "file": "/path/to/disk.qcow2",
      "size": "20G",
      "interface": "virtio"
    }
  ],
  "display": "gtk",
  "vga": "std"
}
```

**Exit codes:**

- `0`: Configuration retrieved successfully
- `1`: VM not found

---

#### `inspect` - Detailed VM inspection

Perform comprehensive inspection of a running VM including process information, resource usage, QMP connectivity, and available snapshots. This command provides detailed runtime information beyond basic status.

**Syntax:**

```bash
maqet inspect VM_ID
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)

**Examples:**

```bash
# Inspect running VM
maqet inspect myvm
```

**Output:**

```json
{
  "vm_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "myvm",
  "status": "running",
  "runner_pid": 12340,
  "qemu_pid": 12345,
  "socket_path": "/run/user/1000/maqet/sockets/myvm.sock",
  "process_info": {
    "cpu_percent": 2.5,
    "memory_mb": 4096,
    "memory_percent": 12.3,
    "uptime_seconds": 3600,
    "threads": 8
  },
  "configuration": {
    "binary": "/usr/bin/qemu-system-x86_64",
    "memory": "4G",
    "cpu": 2
  },
  "storage": [
    {
      "name": "hdd",
      "snapshots": ["snapshot1", "snapshot2"]
    }
  ],
  "qmp_connectivity": "connected"
}
```

**Exit codes:**

- `0`: Inspection successful
- `1`: VM not found or not running

**Note:** This command replaces the deprecated `status --detailed` option. Use `status` for basic information and `inspect` for comprehensive details.

---

#### `apply` - Apply configuration

Apply configuration to existing VM, or create it if it doesn't exist.

**Syntax:**

```bash
maqet apply [OPTIONS] VM_ID [CONFIG_FILES...]
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)

**Options:**

- `--vm-config PATH`: Path to configuration file (can specify multiple)
- `--memory SIZE`: Update memory size
- `--cpu COUNT`: Update CPU count
- Any other config parameter as `--key value`

**Examples:**

```bash
# Apply config file (positional - preferred)
maqet apply myvm updated.yaml

# Apply config file (flag form)
maqet apply myvm --vm-config updated.yaml

# Update specific parameters
maqet apply myvm --memory 8G --cpu 4

# Merge multiple configs
maqet apply myvm --vm-config base.yaml --vm-config prod.yaml

# Create VM if it doesn't exist
maqet apply newvm config.yaml
```

**Exit codes:**

- `0`: Configuration applied successfully
- `1`: Operation failed

---

### QMP Commands

QMP commands require the VM to be running. Commands are sent via IPC to the VM runner process, which maintains the QMP connection.

**How it works:**

- Each running VM has its own runner process
- Runner maintains persistent QMP connection to QEMU
- CLI commands communicate with runner via Unix socket
- No daemon required - each VM is self-managing

#### `qmp` - Execute QMP command

Execute raw QMP command on a running VM.

**Syntax:**

```bash
maqet qmp VM_ID COMMAND [ARGS...]
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)
- `COMMAND`: QMP command to execute
- `ARGS`: Command-specific arguments as `--key value`

**Examples:**

```bash
# Power down VM
maqet qmp myvm system_powerdown

# Query VM status
maqet qmp myvm query-status

# Query block devices
maqet qmp myvm query-block
```

**Exit codes:**

- `0`: Command executed successfully
- `1`: Command failed or VM not running

---

#### `qmp keys` - Send key combination

Send key combination to VM via QMP.

**Syntax:**

```bash
maqet qmp keys [OPTIONS] VM_ID KEY [KEY...]
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)
- `KEY`: Key names (e.g., ctrl, alt, f2)

**Options:**

- `--hold-time MS`: How long to hold keys in milliseconds (default: 100)

**Examples:**

```bash
# Switch to TTY2
maqet qmp keys myvm ctrl alt f2

# Send Ctrl+C
maqet qmp keys myvm ctrl c

# Custom hold time
maqet qmp keys myvm --hold-time 200 ctrl alt delete

# Function keys
maqet qmp keys myvm f1
maqet qmp keys myvm shift f10
```

**Available keys:** See [QMP Commands Guide](../user-guide/qmp-commands.md) for complete list.

**Exit codes:**

- `0`: Keys sent successfully
- `1`: Command failed

---

#### `qmp type` - Type text

Type text string to VM via QMP.

**Syntax:**

```bash
maqet qmp type [OPTIONS] VM_ID TEXT
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)
- `TEXT`: Text to type (quote if contains spaces)

**Options:**

- `--hold-time MS`: How long to hold each key in milliseconds (default: 100)

**Examples:**

```bash
# Type username
maqet qmp type myvm root

# Type command with spaces
maqet qmp type myvm "ls -la /home"

# Type with custom hold time
maqet qmp type myvm --hold-time 150 "sensitive-command"
```

**Exit codes:**

- `0`: Text typed successfully
- `1`: Command failed

---

#### `qmp screendump` - Take screenshot

Take screenshot of VM screen.

**Syntax:**

```bash
maqet qmp screendump VM_ID FILENAME
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)
- `FILENAME`: Output filename (PPM format)

**Examples:**

```bash
# Take screenshot
maqet qmp screendump myvm screenshot.ppm

# Timestamped screenshot
maqet qmp screendump myvm "screen_$(date +%Y%m%d_%H%M%S).ppm"
```

**Exit codes:**

- `0`: Screenshot saved successfully
- `1`: Command failed

**Note:** Output is in PPM format. Convert to PNG using ImageMagick:

```bash
maqet qmp screendump myvm screen.ppm
convert screen.ppm screen.png
```

---

#### `qmp pause` / `qmp resume` - Pause/resume VM

Pause and resume VM execution via QMP.

**Syntax:**

```bash
maqet qmp pause VM_ID
maqet qmp resume VM_ID
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)

**Examples:**

```bash
# Pause VM
maqet qmp pause myvm

# Resume VM
maqet qmp resume myvm
```

**Exit codes:**

- `0`: Operation successful
- `1`: Command failed

---

#### `qmp device-add` / `qmp device-del` - Hot-plug devices

Hot-plug and hot-unplug devices.

**Syntax:**

```bash
maqet qmp device-add VM_ID DRIVER --device-id ID [OPTIONS...]
maqet qmp device-del VM_ID DEVICE_ID
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)
- `DRIVER`: Device driver name (e.g., usb-storage, e1000)
- `DEVICE_ID`: Unique device identifier

**Examples:**

```bash
# Add USB storage
maqet qmp device-add myvm usb-storage --device-id usb1 --drive usb-drive

# Add network device
maqet qmp device-add myvm e1000 --device-id net1 --netdev user1

# Remove device
maqet qmp device-del myvm usb1
```

**Exit codes:**

- `0`: Operation successful
- `1`: Command failed

---

### Storage & Snapshots

#### `snapshot` - Manage snapshots

Manage VM storage snapshots.

**Syntax:**

```bash
maqet snapshot VM_ID ACTION DRIVE [NAME] [OPTIONS]
```

**Arguments:**

- `VM_ID`: VM identifier (name or UUID)
- `ACTION`: Snapshot action (create, load, list)
- `DRIVE`: Storage drive name
- `NAME`: Snapshot name (required for create/load)

**Options:**

- `--overwrite`: Overwrite existing snapshot (create only)

**Examples:**

```bash
# Create snapshot
maqet snapshot myvm create hdd backup1

# Overwrite existing snapshot
maqet snapshot myvm create hdd backup1 --overwrite

# Load snapshot
maqet snapshot myvm load hdd backup1

# List snapshots
maqet snapshot myvm list hdd
```

**Output (list):**

```
backup1
backup2
pre-update
```

**Exit codes:**

- `0`: Operation successful
- `1`: Operation failed

**Note:** Only QCOW2 drives support snapshots.

---

## Exit Codes

MAQET uses the following exit codes:

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error |
| `2` | User interrupted (Ctrl+C) or cancelled |
| `3` | Invalid configuration |

**Example usage in scripts:**

```bash
#!/bin/bash
maqet start myvm
if [ $? -eq 0 ]; then
    echo "VM started successfully"
    maqet status myvm
else
    echo "Failed to start VM"
    exit 1
fi
```

## Shell Integration

### Bash Completion

Enable command completion for bash (future feature):

```bash
# Add to ~/.bashrc
eval "$(maqet --bash-completion)"
```

### Command Chaining

```bash
# Chain commands with && for error handling
maqet add vm.yaml --name myvm && \
maqet start myvm && \
maqet status myvm

# Cleanup on error
maqet start myvm || maqet rm myvm --force
```

### Scripting Examples

**Parallel VM startup:**

```bash
#!/bin/bash
# start-cluster.sh - Start multiple VMs in parallel

VMS=("vm1" "vm2" "vm3")

for vm in "${VMS[@]}"; do
    maqet start "$vm" &
done

# Wait for all background jobs
wait

echo "All VMs started"
maqet ls --status running
```

**Automated testing:**

```bash
#!/bin/bash
# test-vm.sh - Test VM with snapshots

VM="test-vm"
DRIVE="hdd"

# Create base snapshot
maqet snapshot "$VM" create "$DRIVE" base-state

# Run tests
for test in test1 test2 test3; do
    echo "Running $test..."

    # Start VM
    maqet start "$VM"

    # Run test commands via QMP
    maqet qmp type "$VM" "run-test-$test.sh"
    maqet qmp keys "$VM" ret

    # Take screenshot
    maqet qmp screendump "$VM" "$test-result.ppm"

    # Stop VM
    maqet stop "$VM"

    # Rollback to base
    maqet snapshot "$VM" load "$DRIVE" base-state
done
```

**Monitoring script:**

```bash
#!/bin/bash
# monitor-vms.sh - Monitor running VMs

while true; do
    clear
    echo "=== MAQET VM Status ==="
    date
    echo ""
    maqet ls --status running
    echo ""
    echo "Refreshing in 5 seconds..."
    sleep 5
done
```

### Environment Variables

**Override XDG directories:**

```bash
export XDG_DATA_HOME=/custom/data
export XDG_RUNTIME_DIR=/custom/runtime
maqet ls
```

**Enable debug logging:**

```bash
export MAQET_LOG_LEVEL=DEBUG
maqet start myvm
```

## Common Workflows

### Create and Start VM

```bash
# Basic workflow
maqet add config.yaml --name myvm
maqet start myvm
maqet status myvm

# One-liner with error handling
maqet add config.yaml --name myvm && maqet start myvm && maqet status myvm
```

### QMP Automation Workflow

```bash
# Start VM
maqet start myvm

# Automated configuration via QMP
maqet qmp keys myvm ctrl alt f2         # Switch to TTY2
maqet qmp type myvm root                # Login
maqet qmp keys myvm ret
maqet qmp type myvm password
maqet qmp keys myvm ret
maqet qmp type myvm "systemctl status"  # Run command
maqet qmp keys myvm ret
maqet qmp screendump myvm status.ppm    # Capture result

# Cleanup
maqet stop myvm
```

### Snapshot-Based Testing

```bash
# Setup
maqet start myvm
maqet snapshot myvm create hdd clean-state

# Test iteration
for config in config1.yaml config2.yaml config3.yaml; do
    # Apply config
    maqet apply myvm "$config"
    maqet start myvm

    # Run tests
    ./run-tests.sh myvm

    # Rollback
    maqet stop myvm
    maqet snapshot myvm load hdd clean-state
done
```

### Bulk Operations

```bash
# Create multiple VMs
for i in {1..5}; do
    maqet add base.yaml --name "vm$i" --memory "${i}G"
done

# Start all VMs
maqet ls --status stopped | awk '{print $1}' | xargs -I {} maqet start {}

# Stop all running VMs
maqet ls --status running | awk '{print $1}' | xargs -I {} maqet stop {}

# Clean up all VMs
maqet rm --all --force
```

## See Also

- [Python API Reference](python-api.md) - Python API documentation
- [Examples](examples.md) - Practical code examples
- [QMP Commands](../user-guide/qmp-commands.md) - QMP command reference
- [Configuration Guide](../user-guide/configuration.md) - YAML configuration details
