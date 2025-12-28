# Storage Management Guide

This guide covers MAQET's storage system for managing VM disks and shared folders.

## Table of Contents

- [Overview](#overview)
- [Storage Device Types](#storage-device-types)
- [Configuration](#configuration)
- [Auto-Creation](#auto-creation)
- [Snapshot Management](#snapshot-management)
- [Performance Considerations](#performance-considerations)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Overview

MAQET provides a unified storage management system that supports multiple storage device types:

- **QCOW2**: Copy-on-write disk images with snapshot support
- **Raw**: Raw disk images for better performance
- **VirtFS**: Shared folders between host and guest

Each storage type has different characteristics and use cases. This guide will help you choose the right storage type and configure it correctly.

### Key Features

- Automatic storage file creation
- Snapshot support for QCOW2
- Multiple interface types (VirtIO, SATA, IDE, SCSI)
- Flexible configuration via YAML
- Disk space validation before creation
- Concurrent creation protection

## Storage Device Types

### QCOW2 (Recommended for Most Use Cases)

**QCOW2** (QEMU Copy-On-Write version 2) is the default and most feature-rich storage format.

#### Features

- **Snapshots**: Create, load, and manage snapshots
- **Thin provisioning**: File grows as data is written
- **Compression**: Optional compression support
- **Encryption**: Optional encryption support
- **Base images**: Support for backing files

#### When to Use

- Development and testing VMs
- VMs that need snapshot functionality
- When disk space efficiency is important
- When you need incremental backups

#### Pros

- Snapshots for easy rollback
- Smaller initial file size (thin provisioned)
- Flexible and feature-rich

#### Cons

- Slightly slower than raw (5-10% overhead)
- More complex file format

#### Example Configuration

```yaml
storage:
  - name: hdd
    type: qcow2
    file: /path/to/disk.qcow2
    size: 20G
    interface: virtio
```

### Raw (Best for Performance)

**Raw** format stores disk data directly without any metadata or special features.

#### Features

- **High performance**: No overhead, direct I/O
- **Simple format**: Just raw disk data
- **Wide compatibility**: Works everywhere

#### When to Use

- Production VMs with high I/O requirements
- Database servers
- When maximum performance is critical
- When snapshot functionality is not needed

#### Pros

- Best performance (no overhead)
- Simple and reliable
- Lower CPU usage

#### Cons

- No snapshot support
- No thin provisioning (full size immediately)
- Larger file size

#### Example Configuration

```yaml
storage:
  - name: hdd
    type: raw
    file: /path/to/disk.raw
    size: 20G
    interface: virtio
```

### VirtFS (Shared Folders)

**VirtFS** (9p filesystem) enables folder sharing between host and guest.

#### Features

- **Folder sharing**: Share host directories with guest
- **Security models**: Multiple security models for permissions
- **Read-only option**: Prevent guest modifications
- **Live sharing**: Changes visible immediately

#### When to Use

- Development environments
- Sharing code/data with VMs
- Build systems that need host access
- Testing and debugging

#### Pros

- Easy data exchange
- No disk image needed
- Changes visible immediately
- Multiple security models

#### Cons

- No snapshot support
- Performance overhead for many small files
- Requires guest 9p driver support
- Security considerations for production

#### Example Configuration

```yaml
storage:
  - name: shared
    type: virtfs
    path: /opt/shared
    mount_tag: hostshare
    security_model: mapped-xattr
    readonly: true
```

#### Security Models

VirtFS supports different security models for handling file permissions:

**mapped-xattr** (Recommended for Production):

- Maps file ownership to extended attributes
- Most secure option
- Requires filesystem with xattr support

```yaml
security_model: mapped-xattr
```

**mapped-file**:

- Stores permissions in .virtfs files
- Portable across filesystems
- Good for development

```yaml
security_model: mapped-file
```

**passthrough**:

- Direct host permissions
- Requires root or matching UIDs
- Not recommended for production

```yaml
security_model: passthrough
```

**none**:

- No security mapping
- Recommended with readonly: true
- Simplest option

```yaml
security_model: none
readonly: true
```

## Configuration

### Basic Storage Configuration

Storage devices are defined in the `storage` list in your VM configuration:

```yaml
name: myvm
binary: /usr/bin/qemu-system-x86_64

storage:
  - name: hdd           # Storage device name
    type: qcow2         # Storage type (qcow2, raw, virtfs)
    file: /path/to/disk # File path (optional, auto-generated if omitted)
    size: 20G           # Size (required for qcow2/raw)
    interface: virtio   # Interface type (virtio, sata, ide, scsi, none)
```

### Interface Types

MAQET supports multiple storage interfaces:

| Interface | Description | Performance | Use Case |
|-----------|-------------|-------------|----------|
| `virtio` | Paravirtualized (default) | Best | Modern Linux VMs |
| `sata` | SATA/AHCI controller | Good | General purpose, CD/DVD |
| `ide` | Legacy IDE controller | Fair | Old OS compatibility |
| `scsi` | SCSI controller | Good | Enterprise, many disks |
| `none` | No interface | N/A | Special cases |

**Recommendation**: Use `virtio` for best performance on modern Linux guests.

### Complete Example

```yaml
name: development-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 2
  - enable-kvm: null

storage:
  # System disk (QCOW2 with snapshots)
  - name: system
    type: qcow2
    file: /vms/dev-system.qcow2
    size: 50G
    interface: virtio

  # Data disk (Raw for performance)
  - name: data
    type: raw
    file: /vms/dev-data.raw
    size: 100G
    interface: virtio

  # Installation media (ISO)
  - name: cdrom
    type: raw
    file: /iso/ubuntu-22.04.iso
    interface: sata
    media: cdrom

  # Shared folder (VirtFS)
  - name: workspace
    type: virtfs
    path: /home/user/workspace
    mount_tag: workspace
    security_model: mapped-xattr
    readonly: false
```

### Minimal Configuration

If you omit the `file` path, MAQET auto-generates a path in `/tmp`:

```yaml
storage:
  - name: hdd
    type: qcow2
    size: 20G
    # file: auto-generated as /tmp/maqet-<vm_id>-hdd.qcow2
```

### Media Types

For CD/DVD drives, add `media: cdrom`:

```yaml
storage:
  - name: install
    type: raw
    file: /iso/install.iso
    interface: sata
    media: cdrom
```

## Auto-Creation

MAQET automatically creates missing storage files when starting a VM.

### How It Works

1. Check if storage file exists
2. Validate parent directory is writable
3. Check available disk space
4. Use file locking to prevent concurrent creation
5. Create file using `qemu-img create`
6. Log creation details

### Auto-Creation Rules

Storage files are auto-created if:

- File does not exist
- Parent directory is writable
- Not in system directories (/etc, /usr, /boot, etc.)
- Sufficient disk space available

### Example

```yaml
storage:
  - name: hdd
    type: qcow2
    size: 20G
    # No 'file' specified, will auto-create in /tmp
```

When you start the VM:

```bash
maqet start myvm
# Output:
# INFO: Creating qcow2 storage file: /tmp/maqet-myvm-hdd.qcow2 (20G)
# INFO: Successfully created storage file: /tmp/maqet-myvm-hdd.qcow2
```

### Disk Space Validation

MAQET checks available disk space before creating files:

```bash
# If insufficient space:
# ERROR: Insufficient disk space for /vms/disk.qcow2.
# Required: 20.0GB, Available: 15.0GB.
# Free up disk space and try again.
```

### Manual Creation

You can also create storage files manually:

```bash
# Create QCOW2 disk
qemu-img create -f qcow2 /vms/disk.qcow2 20G

# Create QCOW2 with options
qemu-img create -f qcow2 \
    -o cluster_size=2M,lazy_refcounts=on \
    /vms/disk.qcow2 20G

# Create raw disk
qemu-img create -f raw /vms/disk.raw 20G
```

## Snapshot Management

Snapshots allow you to save and restore VM disk state. **Only QCOW2 storage supports snapshots.**

### Creating Snapshots

```bash
# Create snapshot
maqet snapshot <vm_id> create <drive_name> <snapshot_name>

# Example
maqet snapshot myvm create hdd backup-20240101

# With overwrite option
maqet snapshot myvm create hdd backup-20240101 --overwrite
```

### Listing Snapshots

```bash
# List snapshots for a drive
maqet snapshot <vm_id> list <drive_name>

# Example
maqet snapshot myvm list hdd

# Output:
# Snapshots for drive 'hdd' on VM 'myvm':
# - backup-20240101 (512MB, 2024-01-01 12:00:00)
# - before-upgrade (1.2GB, 2024-01-15 09:30:00)
```

### Loading Snapshots

```bash
# Load (revert to) a snapshot
maqet snapshot <vm_id> load <drive_name> <snapshot_name>

# Example
maqet snapshot myvm load hdd backup-20240101
```

**Warning**: Loading a snapshot discards all changes made after the snapshot was created.

### Deleting Snapshots

```bash
# Delete a snapshot
maqet snapshot <vm_id> delete <drive_name> <snapshot_name>

# Example
maqet snapshot myvm delete hdd backup-20240101
```

### Live Snapshots

**New in v0.1**: Create snapshots on running VMs without shutdown/restart overhead.

Live snapshots use QEMU's QMP interface to create snapshots while the VM is running, eliminating the need to stop and restart the VM. This provides significant performance improvements for workflows requiring multiple snapshots.

**Performance Comparison**:

- **Offline snapshot**: Stop VM (10s) + Snapshot (2s) + Start VM (40s) = **52 seconds**
- **Live snapshot**: Auto-pause (0.5s) + Snapshot (2-4s) + Auto-resume (0.5s) = **3-5 seconds**
- **Speedup**: **10x faster per snapshot**

#### Creating Live Snapshots

```bash
# Create live snapshot (VM stays running)
maqet snapshot <vm_id> create <drive_name> <snapshot_name> --live

# Example
maqet snapshot myvm create hdd checkpoint-1 --live

# With overwrite
maqet snapshot myvm create hdd checkpoint-1 --live --overwrite
```

**Important**: The VM automatically pauses for 2-5 seconds during snapshot creation, then resumes automatically.

#### When to Use Live vs Offline Snapshots

**Use Live Snapshots When**:

- VM must stay running (production services, long-running processes)
- Creating multiple consecutive snapshots (testing workflows)
- Performance is critical (CI/CD pipelines)
- VM has moderate RAM size (< 8GB)

**Use Offline Snapshots When**:

- VM is already stopped
- VM has very large RAM (> 8GB) - live snapshots may take 10-30 seconds
- Absolute consistency is required (live snapshots capture mid-execution state)

#### Live Snapshot Workflow Example

```bash
# 1. Start VM
maqet start testvm

# 2. Create baseline snapshot (live)
maqet snapshot testvm create hdd baseline --live
# VM stays running - work continues immediately

# 3. Make changes, test feature A
# ... VM continues running ...

# 4. Create snapshot for feature A
maqet snapshot testvm create hdd feature-a-complete --live
# VM pauses ~3 seconds, resumes automatically

# 5. Test feature B
# ... VM continues running ...

# 6. Create snapshot for feature B
maqet snapshot testvm create hdd feature-b-complete --live

# Total time: ~9-15 seconds for 3 snapshots
# vs ~156 seconds with offline snapshots (shutdown/restart cycles)
```

#### Error Handling

Live snapshots require the VM to be running:

```bash
# If VM is stopped, you'll get a helpful error:
$ maqet snapshot stopped-vm create hdd test --live
ERROR: VM 'stopped-vm' is not running (status: stopped).
Live snapshots require running VM.
Options:
  1. Start VM: maqet start stopped-vm
  2. Use offline snapshot (remove --live flag)
```

Similarly, offline snapshots require the VM to be stopped:

```bash
# If VM is running, you'll get:
$ maqet snapshot running-vm create hdd test
ERROR: VM 'running-vm' is running.
Offline snapshots require stopped VM.
Options:
  1. Stop VM: maqet stop running-vm
  2. Use live snapshot (add --live flag)
```

### Snapshot Workflow Example

```bash
# 1. Create VM with QCOW2 storage
maqet add vm.yaml --name testvm

# 2. Start VM and make changes
maqet start testvm

# 3. Create snapshot before risky operation
maqet snapshot testvm create hdd before-upgrade

# 4. Perform risky operation (e.g., system upgrade)
# If something goes wrong...

# 5. Revert to snapshot
maqet snapshot testvm load hdd before-upgrade

# 6. If upgrade successful, create new snapshot
maqet snapshot testvm create hdd after-upgrade

# 7. Clean up old snapshots
maqet snapshot testvm delete hdd before-upgrade
```

### Snapshot Limitations

- **QCOW2 only**: Raw and VirtFS do not support snapshots
- **VM state**: Snapshots save disk state, not RAM/CPU state (full VM checkpoint including memory)
- **VM state requirements**:
  - **Live snapshots** (with `--live` flag): Require VM to be running
  - **Offline snapshots** (default): Require VM to be stopped
- **Disk space**: Snapshots consume additional disk space
- **Performance**: Many snapshots can impact disk performance

## Performance Considerations

### Storage Type Performance

| Type | Read | Write | Snapshots | Use Case |
|------|------|-------|-----------|----------|
| Raw | Fastest | Fastest | No | Production databases |
| QCOW2 | Fast | Fast | Yes | Development, testing |
| VirtFS | Slower | Slower | No | Shared folders |

### Interface Performance

| Interface | Performance | Compatibility |
|-----------|-------------|---------------|
| virtio | Best | Modern Linux |
| sata | Good | All OS |
| ide | Fair | Legacy OS |
| scsi | Good | Enterprise |

### Optimization Tips

#### Use VirtIO

```yaml
storage:
  - name: hdd
    type: qcow2
    interface: virtio  # Best performance
```

#### Enable KVM

```yaml
arguments:
  - enable-kvm: null  # Hardware acceleration
```

#### Raw for Performance-Critical VMs

```yaml
storage:
  - name: hdd
    type: raw  # Better performance than QCOW2
    size: 50G
```

#### QCOW2 Optimization

When creating QCOW2 manually, use optimized settings:

```bash
qemu-img create -f qcow2 \
    -o cluster_size=2M,lazy_refcounts=on,preallocation=metadata \
    disk.qcow2 50G
```

#### SSD Storage

Store disk images on SSD for better I/O performance:

```yaml
storage:
  - name: hdd
    type: qcow2
    file: /ssd/vms/disk.qcow2  # Store on SSD
    size: 50G
```

## Best Practices

### Storage Device Naming

Use descriptive names:

```yaml
storage:
  - name: system        # System disk
  - name: data          # Data disk
  - name: logs          # Log storage
  - name: workspace     # Shared workspace
```

### Separate System and Data

Separate OS and application data:

```yaml
storage:
  - name: system
    type: qcow2
    size: 30G           # OS and applications
    interface: virtio

  - name: data
    type: qcow2
    size: 100G          # Application data
    interface: virtio
```

Benefits:

- Independent snapshots
- Easier backups
- Better organization

### Use Appropriate Storage Types

- **Development**: QCOW2 (snapshots)
- **Production**: Raw (performance)
- **Sharing**: VirtFS (convenience)

### Regular Snapshots

Create snapshots before risky operations:

```bash
# Before system upgrade
maqet snapshot myvm create system before-upgrade

# Before application deployment
maqet snapshot myvm create system before-deploy

# Before configuration changes
maqet snapshot myvm create system before-config-change
```

### Snapshot Cleanup

Don't accumulate too many snapshots:

```bash
# List snapshots
maqet snapshot myvm list system

# Delete old snapshots
maqet snapshot myvm delete system snapshot-2024-01-01
maqet snapshot myvm delete system snapshot-2024-01-02
```

### Backup Strategy

Combine snapshots with backups:

```bash
# 1. Create snapshot
maqet snapshot myvm create system backup-$(date +%Y%m%d)

# 2. Export snapshot to backup location
qemu-img convert -f qcow2 -O qcow2 -c \
    /vms/system.qcow2 \
    /backups/system-$(date +%Y%m%d).qcow2

# 3. Clean up local snapshot
maqet snapshot myvm delete system backup-$(date +%Y%m%d)
```

### Disk Space Management

Monitor disk usage:

```bash
# Check VM storage usage
du -sh /vms/*

# Check available space
df -h /vms

# Find large snapshots
qemu-img info /vms/disk.qcow2
```

### VirtFS Security

For production VirtFS:

```yaml
storage:
  - name: shared
    type: virtfs
    path: /opt/shared
    security_model: mapped-xattr  # Most secure
    readonly: true                # Prevent writes
```

## Common Patterns

### Pattern 1: Development VM with Snapshots

```yaml
name: dev-vm
binary: /usr/bin/qemu-system-x86_64

storage:
  # System disk with snapshots
  - name: system
    type: qcow2
    file: /vms/dev-system.qcow2
    size: 50G
    interface: virtio

  # Shared workspace
  - name: workspace
    type: virtfs
    path: /home/user/projects
    mount_tag: workspace
    security_model: mapped-xattr
```

Usage:

```bash
# Create snapshot before testing
maqet snapshot dev-vm create system before-test

# Test changes...

# Revert if needed
maqet snapshot dev-vm load system before-test
```

### Pattern 2: Production VM with Performance

```yaml
name: prod-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - enable-kvm: null
  - cpu: "host"

storage:
  # System disk (raw for performance)
  - name: system
    type: raw
    file: /vms/prod-system.raw
    size: 50G
    interface: virtio

  # Data disk (raw for performance)
  - name: data
    type: raw
    file: /vms/prod-data.raw
    size: 200G
    interface: virtio
```

### Pattern 3: Testing VM with Multiple Snapshots

```yaml
storage:
  - name: system
    type: qcow2
    size: 30G
    interface: virtio
```

Workflow:

```bash
# Initial setup
maqet add test-vm.yaml
maqet start test-vm
# Install OS and applications
maqet snapshot test-vm create system clean-install

# Test scenario 1
# Make changes...
maqet snapshot test-vm create system scenario-1

# Revert to clean state
maqet snapshot test-vm load system clean-install

# Test scenario 2
# Make changes...
maqet snapshot test-vm create system scenario-2

# Clean up
maqet snapshot test-vm delete system scenario-1
maqet snapshot test-vm delete system scenario-2
```

### Pattern 4: Multi-Disk VM

```yaml
storage:
  # Boot disk
  - name: boot
    type: qcow2
    size: 20G
    interface: virtio

  # Application disk
  - name: apps
    type: qcow2
    size: 50G
    interface: virtio

  # Database disk (raw for performance)
  - name: database
    type: raw
    size: 100G
    interface: virtio

  # Logs disk
  - name: logs
    type: qcow2
    size: 30G
    interface: virtio
```

## Troubleshooting

### Storage File Not Created

**Symptoms**: VM fails to start, error about missing storage file

**Check**:

```bash
# Check parent directory exists and is writable
ls -ld /vms

# Check disk space
df -h /vms

# Check qemu-img is installed
which qemu-img
qemu-img --version
```

**Solution**:

```bash
# Create directory
mkdir -p /vms

# Fix permissions
chmod 755 /vms

# Install qemu-img
sudo apt install qemu-utils  # Ubuntu/Debian
sudo dnf install qemu-img    # Fedora
```

### Insufficient Disk Space

**Symptoms**: Error about insufficient disk space

**Check**:

```bash
# Check available space
df -h /vms

# Check file sizes
du -sh /vms/*
```

**Solution**:

```bash
# Free up space
# Remove old VMs
maqet rm old-vm --force

# Clean up old snapshots
maqet snapshot myvm list system
maqet snapshot myvm delete system old-snapshot

# Move VMs to larger partition
mv /vms /larger-partition/vms
```

### Snapshot Command Fails

**Symptoms**: Snapshot create/load/delete fails

**Check**:

```bash
# Verify storage type is QCOW2
maqet status myvm | grep storage

# Check file format
qemu-img info /vms/disk.qcow2 | grep format
```

**Solution**:

Only QCOW2 supports snapshots. Convert if needed:

```bash
# Convert raw to QCOW2
qemu-img convert -f raw -O qcow2 \
    /vms/disk.raw \
    /vms/disk.qcow2

# Update VM configuration to use new file
```

### VirtFS Not Working

**Symptoms**: Shared folder not accessible in guest

**Check**:

```bash
# Verify path exists on host
ls -ld /opt/shared

# Check permissions
ls -ld /opt/shared

# Verify guest has 9p support
# In guest:
lsmod | grep 9p
```

**Solution**:

```bash
# In guest, mount VirtFS:
sudo mount -t 9p -o trans=virtio workspace /mnt/shared

# Or add to /etc/fstab:
workspace /mnt/shared 9p trans=virtio,version=9p2000.L 0 0
```

### Performance Issues

**Symptoms**: Slow disk I/O

**Solutions**:

1. **Use VirtIO interface**:

   ```yaml
   interface: virtio  # Not ide or sata
   ```

2. **Enable KVM**:

   ```yaml
   arguments:
     - enable-kvm: null
   ```

3. **Use raw format for production**:

   ```yaml
   type: raw  # Not qcow2
   ```

4. **Store on SSD**:

   ```yaml
   file: /ssd/vms/disk.qcow2
   ```

5. **Optimize QCOW2** (if using QCOW2):

   ```bash
   qemu-img create -f qcow2 \
       -o cluster_size=2M,lazy_refcounts=on \
       disk.qcow2 50G
   ```

## See Also

- [CLAUDE.md](../../CLAUDE.md) - Development documentation
- [Configuration Examples](../reference/) - More configuration examples
- [Production Deployment](../deployment/production.md) - Production setup guide
