# Quick Start Guide

Get started with MAQET in minutes. This guide walks you through creating and managing your first virtual machine.

## Table of Contents

- [Before You Begin](#before-you-begin)
- [Tutorial: Your First VM](#tutorial-your-first-vm)
- [Understanding the Output](#understanding-the-output)
- [Common Operations](#common-operations)
- [Example Workflows](#example-workflows)
- [Next Steps](#next-steps)

---

## Before You Begin

Ensure MAQET is installed and QEMU is available:

```bash
# Verify maqet is installed
maqet --version

# Verify QEMU is installed
qemu-system-x86_64 --version
```

If not installed, see the [Installation Guide](installation.md).

---

## Tutorial: Your First VM

### Step 1: Create a Configuration File

Create a file named `my-first-vm.yaml` with the following content:

```yaml
name: my-first-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "2G"              # 2GB of RAM
  - smp: 2               # 2 CPU cores
  - enable-kvm: null     # Enable KVM acceleration
  - cpu: "host"          # Use host CPU features
  - display: "gtk"       # GTK graphical window
  - vga: "std"           # Standard VGA adapter

storage:
  - name: hdd
    type: qcow2
    size: 20G
    interface: virtio
```

**Configuration Explanation:**

- **name**: Unique identifier for your VM
- **binary**: Path to QEMU executable
- **arguments**: QEMU command-line arguments
  - **m**: Memory allocation (2G = 2 gigabytes)
  - **smp**: Number of CPU cores
  - **enable-kvm**: Enable hardware virtualization (much faster)
  - **cpu**: CPU model (host = use host CPU features)
  - **display**: Display backend (gtk = graphical window)
  - **vga**: VGA device type (std = standard VGA)
- **storage**: Storage devices
  - **name**: Device identifier
  - **type**: qcow2 (QEMU copy-on-write format)
  - **size**: Virtual disk size
  - **interface**: Disk interface (virtio = paravirtualized)

### Step 2: Add the VM to MAQET

```bash
maqet add my-first-vm.yaml
```

**Expected Output:**

```
INFO: Creating VM 'my-first-vm'
INFO: Processing configuration from my-first-vm.yaml
INFO: Creating storage device 'hdd' (20G qcow2)
INFO: Storage file created: ~/.local/share/maqet/storage/my-first-vm/hdd.qcow2
INFO: VM 'my-first-vm' added successfully
```

**What happened:**

1. MAQET parsed your configuration file
2. Created a new VM entry in the database
3. Created storage directory: `~/.local/share/maqet/storage/my-first-vm/`
4. Created virtual disk file: `hdd.qcow2` (20GB capacity)
5. Saved VM configuration for future use

### Step 3: List Your VMs

```bash
maqet ls
```

**Expected Output:**

```
NAME           STATUS      PID      MEMORY    CPU
my-first-vm    stopped     -        2G        2
```

This confirms your VM is registered but not yet running.

### Step 4: Start the VM

```bash
maqet start my-first-vm
```

**Expected Output:**

```
INFO: Starting VM 'my-first-vm'
INFO: QMP socket: /run/user/1000/maqet/sockets/my-first-vm.sock
INFO: VM started with PID: 12345
```

**What happened:**

1. MAQET launched QEMU with your configuration
2. Created QMP socket for communication at `/run/user/1000/maqet/sockets/`
3. QEMU process started with PID 12345
4. A graphical window appeared showing the VM

**You should now see a QEMU window** with an empty disk (since we haven't installed an OS yet).

### Step 5: Check VM Status

```bash
maqet status my-first-vm
```

**Expected Output:**

```
VM: my-first-vm
Status: running
PID: 12345
Memory: 2G
CPU: 2
Binary: /usr/bin/qemu-system-x86_64
QMP Socket: /run/user/1000/maqet/sockets/my-first-vm.sock

Storage Devices:
  - hdd: ~/.local/share/maqet/storage/my-first-vm/hdd.qcow2 (qcow2, 20G)

QEMU Status:
  Status: running
  Running: true
```

### Step 6: Interact with the VM (QMP Commands)

MAQET provides QMP (QEMU Machine Protocol) commands to interact with running VMs:

#### Send Key Combinations

```bash
# Send Ctrl+Alt+F2
maqet qmp keys my-first-vm ctrl alt f2

# Send Ctrl+Alt+Delete
maqet qmp keys my-first-vm ctrl alt delete
```

#### Type Text into the VM

```bash
maqet qmp type my-first-vm "Hello from MAQET"
```

#### Take a Screenshot

```bash
maqet qmp screendump my-first-vm screenshot.ppm
```

This saves a screenshot to `screenshot.ppm` (PPM image format).

Convert to PNG using ImageMagick:

```bash
convert screenshot.ppm screenshot.png
```

#### Pause and Resume

```bash
# Pause VM
maqet qmp pause my-first-vm

# Resume VM
maqet qmp resume my-first-vm
```

#### Query VM Status via QMP

```bash
# Get detailed QEMU status
maqet qmp my-first-vm query-status

# Expected output:
# {"return": {"status": "running", "running": true}}
```

### Step 7: Stop the VM

```bash
maqet stop my-first-vm
```

**Expected Output:**

```
INFO: Stopping VM 'my-first-vm'
INFO: Sending shutdown signal to PID 12345
INFO: VM stopped successfully
```

**What happened:**

1. MAQET sent a graceful shutdown signal via QMP
2. QEMU process terminated
3. QMP socket cleaned up
4. VM status updated to "stopped"

Check status again:

```bash
maqet status my-first-vm
```

**Expected Output:**

```
VM: my-first-vm
Status: stopped
PID: None
...
```

### Step 8: Remove the VM

When you no longer need the VM:

```bash
maqet rm my-first-vm --force
```

**Expected Output:**

```
INFO: Removing VM 'my-first-vm'
INFO: Cleaning up storage files
INFO: Removed: ~/.local/share/maqet/storage/my-first-vm/hdd.qcow2
INFO: VM removed successfully
```

**Warning**: This deletes the VM definition and all storage files. The disk image is permanently deleted.

---

## Understanding the Output

### Verbosity Levels

Control how much information MAQET displays:

```bash
# Quiet mode (errors only - this is now the default)
maqet start my-first-vm

# Show warnings
maqet -v start my-first-vm

# Show info messages (old default behavior)
maqet -vv start my-first-vm

# Show debug information
maqet -vvv start my-first-vm
```

### Exit Codes

MAQET uses standard exit codes:

- **0**: Success
- **1**: General error
- **2**: Initialization error
- **5**: Execution error

Check exit code:

```bash
maqet start my-first-vm
echo $?  # Prints: 0 (success)
```

---

## Common Operations

### Starting a VM in Detached Mode

By default, MAQET runs QEMU in the foreground. Use detached mode to run in the background:

```bash
maqet start my-first-vm --detach
```

### Listing VMs with Filters

```bash
# List only running VMs
maqet ls --status running

# List only stopped VMs
maqet ls --status stopped
```

### Force Stopping a VM

If graceful shutdown doesn't work:

```bash
maqet stop my-first-vm --force
```

This sends SIGKILL to the QEMU process.

### Updating VM Configuration

After creating a VM, you can update its configuration:

```bash
maqet apply my-first-vm --memory 4G --cpu 4
```

**Note**: Changes take effect on next start (requires VM restart).

---

## Example Workflows

### Workflow 1: Creating a VM with ISO Boot

Create a VM that boots from an installation ISO:

```yaml
name: ubuntu-installer
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 2
  - enable-kvm: null
  - cpu: "host"
  - display: "gtk"
  - vga: "std"
  - boot: "order=dc"  # Try CD first, then disk

storage:
  - name: hdd
    type: qcow2
    size: 30G
    interface: virtio

  - name: cdrom
    type: raw
    file: /path/to/ubuntu-22.04.iso
    interface: sata
    media: cdrom
```

Save as `ubuntu-installer.yaml`, then:

```bash
maqet add ubuntu-installer.yaml
maqet start ubuntu-installer
```

The VM will boot from the ISO and you can install Ubuntu to the virtual disk.

### Workflow 2: Headless Server VM

Create a VM without a graphical display (for servers or CI):

```yaml
name: headless-server
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "2G"
  - smp: 2
  - enable-kvm: null
  - cpu: "host"
  - display: "none"  # No display
  # VGA automatically set to 'none'

storage:
  - name: disk
    type: qcow2
    size: 20G
    interface: virtio
```

```bash
maqet add headless-server.yaml
maqet start headless-server --detach
```

Access via serial console or SSH (requires network configuration).

### Workflow 3: Snapshot Management

Create snapshots of your VM's state:

```bash
# Start VM
maqet start my-first-vm

# Do some work in the VM...

# Create a snapshot
maqet snapshot my-first-vm create hdd snapshot1

# Continue working...

# List snapshots
maqet snapshot my-first-vm list hdd

# Restore to snapshot (VM must be stopped)
maqet stop my-first-vm
maqet snapshot my-first-vm load hdd snapshot1
maqet start my-first-vm

# Delete a snapshot
maqet snapshot my-first-vm delete hdd snapshot1
```

**Note**: Snapshots only work with qcow2 storage devices.

### Workflow 4: Shared Folder (VirtFS)

Share a host directory with the VM:

```yaml
name: dev-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 2
  - enable-kvm: null
  - display: "gtk"
  - vga: "std"

storage:
  - name: disk
    type: qcow2
    size: 20G
    interface: virtio

  - name: shared
    type: virtfs
    path: /home/user/projects
    mount_tag: hostshare
    security_model: mapped-xattr
```

Inside the VM (Linux guest):

```bash
# Mount the shared folder
sudo mkdir /mnt/shared
sudo mount -t 9p -o trans=virtio hostshare /mnt/shared

# Access host files
ls /mnt/shared
```

---

## Next Steps

### Learn More

- **[Configuration Guide](configuration.md)**: Detailed configuration options
- **[Argument Parsing](../ARGUMENT_PARSING.md)**: Advanced YAML argument syntax
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions

### Common Next Tasks

1. **Install an Operating System**
   - Download an ISO image
   - Create VM with cdrom configuration
   - Boot and install OS

2. **Configure Networking**
   - Add network devices
   - Set up port forwarding
   - Enable SSH access

3. **Optimize Performance**
   - Enable KVM acceleration
   - Adjust CPU topology
   - Configure VirtIO devices

4. **Automate VM Management**
   - Use MAQET's Python API
   - Create shell scripts for common tasks
   - Integrate with CI/CD pipelines

### Example: Installing Ubuntu

Complete workflow for installing Ubuntu:

```bash
# 1. Download Ubuntu ISO
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.3-desktop-amd64.iso

# 2. Create VM configuration
cat > ubuntu-vm.yaml << 'EOF'
name: ubuntu-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 4
  - enable-kvm: null
  - cpu: "host"
  - display: "gtk"
  - vga: "std"
  - boot: "order=dc"

storage:
  - name: system
    type: qcow2
    size: 50G
    interface: virtio

  - name: install
    type: raw
    file: ./ubuntu-22.04.3-desktop-amd64.iso
    interface: sata
    media: cdrom
EOF

# 3. Create and start VM
maqet add ubuntu-vm.yaml
maqet start ubuntu-vm

# 4. Install Ubuntu in the graphical window
# (Follow Ubuntu installer prompts)

# 5. After installation, remove ISO and reboot
maqet stop ubuntu-vm

# Edit config to remove cdrom section, then:
maqet start ubuntu-vm
```

### Python API Usage

Use MAQET programmatically:

```python
from maqet import Maqet

# Initialize MAQET
maqet = Maqet()

# Create VM
vm_id = maqet.add(
    name='my-vm',
    config_file='my-vm.yaml'
)

# Start VM
maqet.start(vm_id)

# Check status
status = maqet.status(vm_id)
print(f"VM Status: {status['status']}")

# Send QMP command
result = maqet.qmp(vm_id, 'query-status')
print(f"QEMU Status: {result}")

# Stop VM
maqet.stop(vm_id)

# Remove VM
maqet.rm(vm_id, force=True)
```

---

## Tips and Best Practices

### Tip 1: Use Descriptive VM Names

```bash
# Good
maqet add ubuntu-dev.yaml --name ubuntu-22-dev-env

# Avoid
maqet add config.yaml --name vm1
```

### Tip 2: Keep Configuration Files Organized

```
~/vms/
├── templates/
│   ├── desktop-vm.yaml
│   ├── server-vm.yaml
│   └── minimal-vm.yaml
├── production/
│   ├── web-server.yaml
│   └── database.yaml
└── development/
    ├── dev-env.yaml
    └── test-vm.yaml
```

### Tip 3: Always Enable KVM

For best performance, always use KVM acceleration:

```yaml
arguments:
  - enable-kvm: null
```

Check if KVM is available:

```bash
ls -la /dev/kvm
```

### Tip 4: Use VirtIO Devices

VirtIO provides better performance than emulated devices:

```yaml
storage:
  - name: disk
    type: qcow2
    interface: virtio  # Much faster than ide/sata
```

### Tip 5: Start Simple, Add Complexity

Begin with minimal configurations and add features as needed:

1. Start with basic VM (CPU, memory, disk)
2. Add display configuration
3. Add network devices
4. Add advanced features (snapshots, shared folders, etc.)

---

## Getting Help

If you get stuck:

1. Check command help: `maqet <command> --help`
2. Review [Troubleshooting Guide](troubleshooting.md)
3. Increase verbosity: `maqet -vv <command>`
4. Check logs: `maqet --log-file /tmp/maqet.log <command>`
5. Report issues: <https://gitlab.com/m4x0n_24/maqet/issues>

---

**Congratulations!** You've created and managed your first MAQET virtual machine. Continue to the [Configuration Guide](configuration.md) to learn about advanced options.

---

**Last Updated**: 2025-10-08
**MAQET Version**: 0.0.10
