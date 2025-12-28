# Troubleshooting Guide

Quick solutions to common problems when using MAQET.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Runtime Issues](#runtime-issues)
- [Configuration Issues](#configuration-issues)
- [Storage Issues](#storage-issues)
- [QMP Connection Issues](#qmp-connection-issues)
- [Performance Tips](#performance-tips)
- [Need More Help?](#need-more-help)

---

## Installation Issues

### Command not found: maqet

**Cause**: Python scripts directory not in PATH.

**Solution**: Add `~/.local/bin` to PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

Verify: `which maqet && maqet --version`

### ModuleNotFoundError: No module named 'maqet'

**Cause**: MAQET not installed or wrong Python environment.

**Solution**:

```bash
# Install MAQET
pip install maqet

# Or use virtual environment (recommended)
python3 -m venv ~/.venvs/maqet
source ~/.venvs/maqet/bin/activate
pip install maqet
```

### Python version too old

**Cause**: MAQET requires Python 3.12+.

**Solution**: Install Python 3.12:

```bash
# Ubuntu/Debian
sudo apt install python3.12 python3.12-venv

# Fedora
sudo dnf install python3.12

# Then install MAQET
python3.12 -m pip install maqet
```

### Permission errors during installation

**Solution**: Use user install or virtual environment:

```bash
# User install
pip install --user maqet

# Virtual environment (recommended)
python3 -m venv ~/.venvs/maqet
source ~/.venvs/maqet/bin/activate
pip install maqet
```

---

## Runtime Issues

### QEMU binary not found

**Cause**: QEMU not installed or wrong path.

**Solution**: Install QEMU:

```bash
# Ubuntu/Debian
sudo apt install qemu-system-x86 qemu-utils

# Fedora
sudo dnf install qemu-system-x86 qemu-img

# Arch Linux
sudo pacman -S qemu-full
```

Or specify correct path in config:

```yaml
binary: /usr/bin/qemu-system-x86_64
```

### Could not access KVM kernel module

**Cause**: KVM not enabled or permission issues.

**Solution**: Add user to kvm group:

```bash
sudo usermod -aG kvm $USER
# Log out and log back in

# Verify
groups | grep kvm
ls -la /dev/kvm
```

If KVM unavailable, disable hardware acceleration (slower):

```yaml
# Remove from config:
# - enable-kvm: null
```

### VM starts but immediately exits

**Cause**: Invalid arguments, missing files, or port conflicts.

**Solution**: Enable debug logging to see specific error:

```bash
maqet --log-file /tmp/maqet.log -vv start myvm
cat /tmp/maqet.log
```

Common issues:

- Missing storage files
- Invalid QEMU argument syntax
- Port already in use

---

## Configuration Issues

### Invalid YAML syntax

**Cause**: YAML syntax errors or indentation issues.

**Solution**: Validate YAML and fix indentation:

```bash
# Validate syntax
python3 -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
```

Common fixes:

```yaml
# WRONG - inconsistent indentation
arguments:
     - m: "2G"

# RIGHT - consistent 2-space indentation
arguments:
  - m: "2G"

# WRONG - unquoted special characters
arguments:
  - netdev: user,hostfwd=tcp::2222-:22

# RIGHT - quoted
arguments:
  - netdev: "user,hostfwd=tcp::2222-:22"
```

Minimum valid configuration:

```yaml
binary: /usr/bin/qemu-system-x86_64
arguments:
  - m: "2G"
```

---

## Storage Issues

### Failed to create storage device

**Cause**: Insufficient disk space, permissions, or qemu-img not found.

**Solution**:

```bash
# Check disk space
df -h ~/.local/share/maqet/

# Check permissions
mkdir -p ~/.local/share/maqet/storage
chmod 755 ~/.local/share/maqet/storage

# Verify qemu-img installed
which qemu-img
```

### Storage file not found

**Cause**: Storage file deleted or incorrect path.

**Solution**: Recreate storage or fix path in config:

```bash
# Recreate qcow2 disk (will be empty)
qemu-img create -f qcow2 ~/.local/share/maqet/storage/myvm/disk.qcow2 20G
```

Or update config with correct path:

```yaml
storage:
  - name: disk
    type: qcow2
    file: /correct/path/to/disk.qcow2
```

### Size format errors

**Cause**: Invalid size specification.

**Solution**: Use proper units:

```yaml
# WRONG - missing unit
storage:
  - name: disk
    size: "20"

# RIGHT - include unit (M, G, or T)
storage:
  - name: disk
    size: "20G"
```

### Snapshots not supported

**Cause**: Only qcow2 storage supports snapshots.

**Solution**: Ensure storage type is qcow2:

```yaml
storage:
  - name: disk
    type: qcow2  # Must be qcow2 for snapshots
    size: 20G
```

---

## QMP Connection Issues

### QMP socket not found

**Cause**: VM not running or crashed.

**Solution**: Verify VM is running:

```bash
maqet ls
ps aux | grep qemu | grep myvm
```

If stopped or crashed, check logs:

```bash
maqet --log-file /tmp/debug.log -vv start myvm
cat /tmp/debug.log
```

### Permission denied on socket

**Cause**: Runtime directory permissions incorrect.

**Solution**: Fix permissions:

```bash
mkdir -p /run/user/$(id -u)/maqet/sockets
chmod 700 /run/user/$(id -u)/maqet
```

### QMP command failed

**Cause**: Invalid command name or VM not responding.

**Solution**: Use valid QMP commands:

```bash
# Test basic commands
maqet qmp myvm query-status
maqet qmp myvm query-version

# If VM not responding, restart
maqet stop myvm --force
maqet start myvm
```

---

## Performance Tips

### VM is very slow

**Primary cause**: KVM not enabled (10-50x slower without it).

**Solution**: Enable KVM and verify permissions:

```yaml
arguments:
  - enable-kvm: null
```

```bash
# Verify KVM available
ls -la /dev/kvm
groups | grep kvm

# Add to kvm group if needed
sudo usermod -aG kvm $USER
```

### Slow disk I/O

**Cause**: Not using virtio interface.

**Solution**: Use virtio for storage:

```yaml
storage:
  - name: disk
    interface: virtio  # Much faster than ide/sata
```

### Resource allocation

**Best practices**:

- VM memory < 80% of host memory
- VM CPUs <= host physical CPUs
- Use `cpu: "host"` for better performance

```yaml
arguments:
  - m: "4G"
  - smp: 4
  - cpu: "host"
```

---

## Need More Help?

### Debugging Commands

Enable verbose logging to see detailed information:

```bash
# Verbose output
maqet -vv start myvm

# Save to log file
maqet --log-file /tmp/maqet.log -vv start myvm
cat /tmp/maqet.log

# Check QEMU command line
ps aux | grep qemu | grep myvm

# Validate YAML syntax
python3 -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
```

### System Information

When reporting issues, include:

```bash
# Version information
maqet --version
python3 --version
qemu-system-x86_64 --version
uname -a

# Current status
maqet ls
df -h ~/.local/share/maqet/
ls -la ~/.local/share/maqet/
```

### Documentation

For detailed information:

- [Installation Guide](installation.md) - Setup and requirements
- [Configuration Guide](configuration.md) - YAML configuration reference
- [Quick Start Guide](quickstart.md) - Basic usage examples
- [Architecture Docs](../architecture/) - Deep technical details

### Report Issues

GitLab Issues: <https://gitlab.com/m4x0n_24/maqet/issues>

Include:

- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs
- System information (versions, OS)
- Configuration file (remove sensitive data)

---

**Last Updated**: 2025-10-31
**MAQET Version**: 0.0.14+
