# Configuration Guide

Essential guide for configuring MAQET virtual machines.

## Table of Contents

- [Configuration File Format](#configuration-file-format)
- [Required Settings](#required-settings)
- [Storage Configuration](#storage-configuration)
- [Common Configuration Examples](#common-configuration-examples)
- [Configuration Merging](#configuration-merging)
- [Advanced Options](#advanced-options)

---

## Configuration File Format

MAQET uses YAML files for VM configuration.

### Basic Structure

```yaml
# VM identification
name: vm-name

# QEMU binary path
binary: /usr/bin/qemu-system-x86_64

# QEMU command-line arguments
arguments:
  - m: "4G"
  - smp: 4
  - enable-kvm: null

# Storage devices
storage:
  - name: disk1
    type: qcow2
    size: 20G
```

### YAML Syntax

- **Indentation**: Use 2 spaces (not tabs)
- **Lists**: Start with `-` (dash + space)
- **Comments**: Start with `#`
- **Strings**: Quote if contains special characters
- **Null values**: Use `null` for flags

---

## Required Settings

### binary

**Type**: String
**Required**: Yes
**Description**: Path to QEMU system binary

```yaml
binary: /usr/bin/qemu-system-x86_64
```

Find your QEMU binary:

```bash
which qemu-system-x86_64
```

### name

**Type**: String
**Required**: No (can be specified via CLI)
**Description**: Unique identifier for the VM

```yaml
name: ubuntu-dev-vm
```

Use descriptive names with hyphens or underscores.

---

## Arguments Configuration

The `arguments` key passes options directly to QEMU. MAQET supports three formats:

### 1. Dictionary Format

For arguments with values:

```yaml
arguments:
  - m: "2G"              # -m 2G
  - smp: 4               # -smp 4
  - cpu: "host"          # -cpu host
```

### 2. Flag Format

For boolean flags:

```yaml
arguments:
  - enable-kvm: null     # -enable-kvm
  - no-reboot: null      # -no-reboot
```

### 3. Complex Arguments

For QEMU arguments with suboptions:

```yaml
arguments:
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"
  - device: "virtio-net,netdev=net0"
```

**For complete QEMU argument reference, see**: [QEMU Documentation](https://www.qemu.org/docs/master/system/invocation.html)

---

## Display Options

### Common Display Configurations

```yaml
# Graphical window
arguments:
  - display: "gtk"
  - vga: "std"

# Headless (no display)
arguments:
  - display: "none"

# VNC remote access
arguments:
  - display: "vnc=:1"
  - vga: "std"
```

**Display types**: `gtk`, `sdl`, `vnc`, `none`
**VGA types**: `std` (recommended), `virtio`, `qxl`, `none`

**Note**: Use `vga: std` for maximum compatibility. Not all QEMU builds include virtio-vga.

---

## Storage Configuration

Storage devices are defined in the `storage` list.

### QCOW2 Storage (Recommended)

```yaml
storage:
  - name: hdd
    type: qcow2
    size: 20G
    interface: virtio
```

**Options**:

- **name** (required): Device identifier
- **type**: `qcow2`
- **size** (required): Disk size (e.g., `20G`, `500M`, `1T`)
- **file** (optional): Path to disk image (auto-generated if omitted)
- **interface**: `virtio`, `sata`, `ide`, `scsi` (default: `virtio`)
- **media**: `disk` (default), `cdrom`

**Note**: MAQET automatically creates missing qcow2 files. Use `virtio` interface for best performance.

### Raw Storage (ISOs and Images)

```yaml
storage:
  - name: cdrom
    type: raw
    file: /path/to/ubuntu.iso
    interface: sata
    media: cdrom
```

### VirtFS (Shared Folders)

```yaml
storage:
  - name: shared
    type: virtfs
    path: /home/user/projects
    mount_tag: hostshare
    security_model: mapped-xattr
```

**Guest mounting (Linux)**:

```bash
sudo mount -t 9p -o trans=virtio hostshare /mnt/shared
```

---

## Network Configuration

### User Mode Networking

Simplest setup, no root required:

```yaml
arguments:
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"
  - device: "virtio-net,netdev=net0"
```

This enables internet access and forwards host port 2222 to guest SSH (port 22).

**For advanced networking options, see**: [QEMU Networking](https://wiki.qemu.org/Documentation/Networking)

---

## Configuration Merging

MAQET supports merging multiple configuration files. Later configs override earlier ones.

```bash
maqet add --vm-config base.yaml --vm-config overrides.yaml
```

**Example**:

**base.yaml**:

```yaml
binary: /usr/bin/qemu-system-x86_64
arguments:
  - m: "2G"
  - smp: 2
```

**overrides.yaml**:

```yaml
arguments:
  - m: "4G"  # Overrides memory from base.yaml
```

**Result**: Memory is 4G, CPU cores are 2 (from base).

**Priority**: CLI arguments > config files (right to left)

---

## Common Configuration Examples

### Desktop VM

```yaml
name: desktop-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 4
  - cpu: "host"
  - enable-kvm: null
  - display: "gtk"
  - vga: "std"

storage:
  - name: system
    type: qcow2
    size: 50G
    interface: virtio
```

### Headless Server

```yaml
name: server-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "8G"
  - smp: 4
  - cpu: "host"
  - enable-kvm: null
  - display: "none"
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"
  - device: "virtio-net,netdev=net0"

storage:
  - name: system
    type: qcow2
    size: 50G
    interface: virtio
```

### Development VM with Shared Folder

```yaml
name: dev-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 2
  - enable-kvm: null
  - display: "gtk"
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"
  - device: "virtio-net,netdev=net0"

storage:
  - name: system
    type: qcow2
    size: 30G
    interface: virtio

  - name: projects
    type: virtfs
    path: /home/user/projects
    mount_tag: projects
    security_model: mapped-xattr
```

### Essential Best Practices

1. **Enable KVM for performance**: Add `- enable-kvm: null` to arguments
2. **Use VirtIO devices**: Set `interface: virtio` for storage and `virtio-net` for network
3. **Use descriptive names**: `ubuntu-22-webserver` instead of `vm1`
4. **Quote complex values**: Always quote arguments with commas or colons
5. **Validate YAML syntax**: Run `python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"`

---

## Advanced Options

MAQET passes QEMU arguments directly with minimal transformation. For complete documentation on QEMU options:

- **QEMU Invocation**: <https://www.qemu.org/docs/master/system/invocation.html>
- **QEMU Networking**: <https://wiki.qemu.org/Documentation/Networking>
- **QEMU Storage**: <https://qemu.readthedocs.io/en/latest/system/qemu-block-drivers.html>

### Common Advanced Configurations

**UEFI Boot**:

```yaml
arguments:
  - bios: "/usr/share/ovmf/OVMF.fd"
```

**Custom Boot Order**:

```yaml
arguments:
  - boot: "order=dc,menu=on"
```

**Sound Card**:

```yaml
arguments:
  - device: "intel-hda"
  - device: "hda-duplex"
```

**USB Passthrough** (find IDs with `lsusb`):

```yaml
arguments:
  - device: "usb-host,vendorid=0x1234,productid=0x5678"
```

---

## Next Steps

- **[Quick Start Guide](quickstart.md)**: Create your first VM
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions
- **[CLI Reference](../api/cli-reference.md)**: Command-line options

---

**Last Updated**: 2025-10-31
**MAQET Version**: 0.0.10
