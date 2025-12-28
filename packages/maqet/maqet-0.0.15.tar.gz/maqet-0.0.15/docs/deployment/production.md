# Production Deployment Guide

This guide covers deploying MAQET in production environments for VM management at scale.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Security Considerations](#security-considerations)
- [Systemd Integration](#systemd-integration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Upgrade Procedures](#upgrade-procedures)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements

**Minimum**:

- CPU: 2 cores
- RAM: 2 GB
- Disk: 10 GB free space
- QEMU/KVM support

**Recommended**:

- CPU: 4+ cores with VT-x/AMD-V
- RAM: 8+ GB
- Disk: 50+ GB SSD
- KVM enabled

### Software Requirements

**Required**:

- Python 3.12 or higher
- QEMU 8.0+ (qemu-system-x86_64, qemu-img)
- Linux kernel with KVM support
- systemd (for daemon mode)
- DBus (for daemon communication)

**Optional**:

- DBus libraries (python3-dbus, python3-gi) for daemon mode
- Git (for development deployments)

### System Sizing

| Workload | VMs | CPU | RAM | Disk |
|----------|-----|-----|-----|------|
| Small | 1-5 | 2-4 cores | 4-8 GB | 50 GB |
| Medium | 5-20 | 4-8 cores | 16-32 GB | 200 GB |
| Large | 20-50 | 8-16 cores | 32-64 GB | 500 GB |
| Enterprise | 50+ | 16+ cores | 64+ GB | 1+ TB |

**Note**: Add VM resource requirements on top of host requirements.

## Installation

### Option 1: PyPI Installation (Recommended for Production)

```bash
# Install from PyPI
pip install maqet

# Verify installation
maqet --version
maqet --help

# Test basic functionality
maqet ls
```

### Option 2: From Source (For Development/Testing)

```bash
# Clone repository
git clone https://gitlab.com/m4x0n_24/maqet.git
cd maqet

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Install with optional dependencies
pip install -e .[qemu,dev]
```

### Post-Installation Setup

```bash
# Verify QEMU installation
which qemu-system-x86_64
which qemu-img

# Check KVM support
lsmod | grep kvm

# Test QEMU
qemu-system-x86_64 --version

# Create data directory (if not using XDG defaults)
mkdir -p /opt/maqet/data
chown maqet:maqet /opt/maqet/data
```

## Security Considerations

### User Permissions

#### Running as Non-Root User (Recommended)

```bash
# Create dedicated user
sudo useradd -r -s /bin/bash -d /opt/maqet -m maqet

# Add to KVM group for hardware acceleration
sudo usermod -a -G kvm maqet

# Verify group membership
groups maqet
```

#### KVM Device Permissions

```bash
# Check KVM device permissions
ls -l /dev/kvm
# Should show: crw-rw---- 1 root kvm

# If user can't access KVM:
sudo usermod -a -G kvm $USER
# Log out and back in
```

#### File System Permissions

```bash
# Data directory
sudo chown -R maqet:maqet /opt/maqet/data
sudo chmod 750 /opt/maqet/data

# Runtime directory (XDG_RUNTIME_DIR)
# Automatically created per-user at /run/user/<uid>/maqet/
```

### Socket Permissions

QMP sockets are created in `$XDG_RUNTIME_DIR/maqet/sockets/`:

- Default: `/run/user/<uid>/maqet/sockets/`
- Permissions: 0600 (owner read/write only)
- Owner: User running maqet

**Security implications**:

- Only the user who created a VM can control it
- Root cannot access user VMs by default
- Multi-user deployments are isolated

### Multi-User Deployments

#### Shared VMs (Advanced)

For shared VM access across users:

```bash
# Create shared group
sudo groupadd maqet-shared

# Add users to group
sudo usermod -a -G maqet-shared user1
sudo usermod -a -G maqet-shared user2

# Set up shared data directory
sudo mkdir -p /opt/maqet/shared
sudo chown root:maqet-shared /opt/maqet/shared
sudo chmod 2770 /opt/maqet/shared

# Run maqet with shared data directory
maqet --maqet-data-dir /opt/maqet/shared ls
```

**Important**: Shared deployments require careful socket permission management.

#### User Isolation (Recommended)

For production, keep users isolated:

- Each user runs their own maqet instance
- VMs stored in user's XDG_DATA_HOME
- Sockets in user's XDG_RUNTIME_DIR
- No cross-user VM access

### VirtFS Security Models

When using VirtFS for shared folders, choose appropriate security model:

```yaml
storage:
  - name: shared
    type: virtfs
    path: /opt/shared
    mount_tag: hostshare
    security_model: mapped-xattr  # Recommended for production
    readonly: true  # Prevent guest modifications
```

**Security models**:

- `mapped-xattr`: Map file ownership to extended attributes (most secure)
- `mapped-file`: Store permissions in .virtfs files (portable)
- `passthrough`: Direct host permissions (requires root, not recommended)
- `none`: No security mapping (read-only recommended)

**Production recommendation**: Use `mapped-xattr` with `readonly: true`.

## Systemd Integration

### Install Systemd Service

#### User Service (Recommended)

```bash
# Copy service file
mkdir -p ~/.config/systemd/user
cp docs/deployment/maqetd.service ~/.config/systemd/user/

# Edit if needed (change paths, etc.)
nano ~/.config/systemd/user/maqetd.service

# Reload systemd
systemctl --user daemon-reload

# Enable service (start on login)
systemctl --user enable maqetd.service

# Start service
systemctl --user start maqetd.service

# Check status
systemctl --user status maqetd.service
```

#### System Service (For Dedicated VM Host)

```bash
# Create system service
sudo cp docs/deployment/maqetd.service /etc/systemd/system/maqetd.service

# Edit for system service
sudo nano /etc/systemd/system/maqetd.service
# Change:
#   ExecStart=/usr/local/bin/maqet daemon start --foreground
#   User=maqet
#   Group=maqet

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable maqetd.service

# Start service
sudo systemctl start maqetd.service

# Check status
sudo systemctl status maqetd.service
```

### Service File Contents

The service file (`maqetd.service`) contains:

```ini
[Unit]
Description=MAQET Daemon - Persistent QMP connections for VM management
Documentation=https://gitlab.com/m4x0n_24/maqet
After=dbus.service

[Service]
Type=dbus
BusName=com.maqet.Manager
ExecStart=%h/.local/bin/maqet daemon start --foreground
Restart=on-failure
RestartSec=5

# Security settings
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=default.target
```

### Daemon Mode Setup

```bash
# Start daemon manually (foreground for debugging)
maqet daemon start --foreground

# Start daemon (background)
maqet daemon start

# Check daemon status
maqet daemon status
# Output: {"running": true, "pid": 12345, "machine_count": 0}

# Stop daemon
maqet daemon stop

# Restart daemon
maqet daemon restart
```

### Service Management

```bash
# View logs
journalctl --user -u maqetd.service -f

# Restart service
systemctl --user restart maqetd.service

# Stop service
systemctl --user stop maqetd.service

# Disable service
systemctl --user disable maqetd.service
```

## Monitoring and Logging

### Log File Management

#### Application Logs

```bash
# Enable file logging
maqet --log-file /var/log/maqet/maqet.log start myvm       # Default: ERROR only (console)

# Set console verbosity levels
maqet -v --log-file /var/log/maqet/maqet.log start myvm    # WARNING + ERROR (console)
maqet -vv --log-file /var/log/maqet/maqet.log start myvm   # INFO + WARNING + ERROR (console)
maqet -vvv --log-file /var/log/maqet/maqet.log start myvm  # DEBUG (all levels, console)

# Note: File logging is always at DEBUG level regardless of -v flags
```

#### Daemon Logs

```bash
# Daemon logs location
# User service: journalctl --user -u maqetd.service
# System service: journalctl -u maqetd.service

# View recent logs
journalctl --user -u maqetd.service --since "1 hour ago"

# Follow logs in real-time
journalctl --user -u maqetd.service -f

# Export logs
journalctl --user -u maqetd.service --since "2024-01-01" > maqet-logs.txt
```

#### Log Rotation

Create `/etc/logrotate.d/maqet`:

```
/var/log/maqet/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 maqet maqet
    sharedscripts
    postrotate
        systemctl reload maqetd.service > /dev/null 2>&1 || true
    endscript
}
```

### Metrics to Monitor

#### System Metrics

- CPU usage (per VM and host)
- Memory usage (per VM and host)
- Disk I/O (per VM storage device)
- Network I/O (per VM interface)
- KVM performance counters

#### MAQET Metrics

```bash
# Number of running VMs
maqet ls --status running | wc -l

# Daemon health
maqet daemon status

# VM status
maqet status myvm

# Storage usage
du -sh ~/.local/share/maqet/
```

#### Monitoring Script Example

```bash
#!/bin/bash
# /opt/maqet/monitor.sh

# Check daemon health
if ! maqet daemon status > /dev/null 2>&1; then
    echo "ERROR: MAQET daemon not running"
    systemctl --user restart maqetd.service
fi

# Count running VMs
VM_COUNT=$(maqet ls --status running | wc -l)
echo "Running VMs: $VM_COUNT"

# Check disk space
DISK_USAGE=$(df -h ~/.local/share/maqet/ | tail -1 | awk '{print $5}')
echo "Data directory usage: $DISK_USAGE"

# Alert if >90% full
if [ "${DISK_USAGE%\%}" -gt 90 ]; then
    echo "WARNING: Disk usage above 90%"
fi
```

### Health Checks

```bash
# Basic health check
maqet daemon status | jq '.running'

# Detailed health check
#!/bin/bash
set -e

# Check daemon
maqet daemon status > /dev/null || exit 1

# Check VM status
for vm in $(maqet ls | jq -r '.[].name'); do
    maqet status "$vm" > /dev/null || echo "WARNING: $vm status check failed"
done

echo "Health check passed"
```

## Backup and Recovery

### What to Back Up

1. **VM Definitions** (Database):
   - Location: `~/.local/share/maqet/instances.db`
   - Contains: VM configurations, status, metadata

2. **VM Storage** (Disk images):
   - QCOW2/Raw files (can be large, 10GB-100GB+)
   - Location: Varies (check VM config)

3. **Configuration** (Optional):
   - Systemd service files
   - Custom scripts
   - Application configs

### Backup Procedures

#### Database Backup

```bash
# Manual backup
cp ~/.local/share/maqet/instances.db ~/.local/share/maqet/instances.db.backup

# Automated backup script
#!/bin/bash
BACKUP_DIR="/opt/maqet/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Backup database
cp ~/.local/share/maqet/instances.db "$BACKUP_DIR/instances-$DATE.db"

# Keep only last 30 days
find "$BACKUP_DIR" -name "instances-*.db" -mtime +30 -delete
```

#### VM Storage Backup

```bash
# Backup VM disk image
qemu-img convert -f qcow2 -O qcow2 -c \
    /path/to/vm.qcow2 \
    /backup/vm-backup.qcow2

# Incremental backup with rsync
rsync -av --progress \
    /path/to/vm-storage/ \
    /backup/vm-storage/
```

#### Snapshot-Based Backup

```bash
# Create VM snapshot before backup
maqet snapshot myvm create hdd backup-$(date +%Y%m%d)

# List snapshots
maqet snapshot myvm list hdd

# Backup snapshot
qemu-img convert -f qcow2 -s backup-20240101 \
    /path/to/vm.qcow2 \
    /backup/vm-backup.qcow2
```

### Recovery Procedures

#### Restore Database

```bash
# Stop daemon
maqet daemon stop

# Restore database
cp /backup/instances-20240101.db ~/.local/share/maqet/instances.db

# Restart daemon
maqet daemon start
```

#### Restore VM Storage

```bash
# Restore disk image
cp /backup/vm-backup.qcow2 /path/to/vm.qcow2

# Or convert format
qemu-img convert -f qcow2 -O qcow2 \
    /backup/vm-backup.qcow2 \
    /path/to/vm.qcow2
```

#### Disaster Recovery

```bash
# 1. Reinstall MAQET
pip install maqet

# 2. Restore database
mkdir -p ~/.local/share/maqet
cp /backup/instances.db ~/.local/share/maqet/

# 3. Restore VM storage
cp /backup/vm-*.qcow2 /path/to/storage/

# 4. Start daemon
maqet daemon start

# 5. Verify VMs
maqet ls
maqet status myvm
```

## Upgrade Procedures

### Pre-Upgrade Checklist

- [ ] Backup database
- [ ] Backup critical VM storage
- [ ] Stop all running VMs
- [ ] Stop daemon
- [ ] Note current version

### Upgrade from PyPI

```bash
# Stop daemon
maqet daemon stop

# Stop all VMs
for vm in $(maqet ls | jq -r '.[].name'); do
    maqet stop "$vm"
done

# Backup database
cp ~/.local/share/maqet/instances.db ~/.local/share/maqet/instances.db.backup

# Upgrade
pip install --upgrade maqet

# Verify version
maqet --version

# Restart daemon
maqet daemon start

# Start VMs
for vm in $(maqet ls | jq -r '.[].name'); do
    maqet start "$vm"
done
```

### Upgrade from Source

```bash
# Stop daemon
maqet daemon stop

# Backup database
cp ~/.local/share/maqet/instances.db ~/.local/share/maqet/instances.db.backup

# Pull latest code
cd /path/to/maqet
git pull origin main

# Reinstall
pip install -e .

# Restart daemon
maqet daemon start
```

### Rollback Procedure

```bash
# Stop daemon
maqet daemon stop

# Restore database
cp ~/.local/share/maqet/instances.db.backup ~/.local/share/maqet/instances.db

# Downgrade to previous version
pip install maqet==0.0.4  # Replace with previous version

# Restart daemon
maqet daemon start
```

## Performance Tuning

### QEMU Configuration

#### Enable KVM

```yaml
# config.yaml
arguments:
  - enable-kvm: null  # Hardware acceleration
  - cpu: "host"       # Pass through host CPU features
```

#### Memory Tuning

```yaml
arguments:
  - m: "4G"           # VM memory
  - mem-path: "/dev/hugepages"  # Use huge pages (requires setup)
```

#### CPU Pinning

```yaml
arguments:
  - smp: "4,sockets=1,cores=4,threads=1"
  - cpu: "host"
```

### Storage Optimization

#### Use VirtIO

```yaml
storage:
  - name: hdd
    type: qcow2
    interface: virtio  # Faster than IDE/SATA
    size: 50G
```

#### QCOW2 Options

```bash
# Create QCOW2 with optimized settings
qemu-img create -f qcow2 \
    -o cluster_size=2M,lazy_refcounts=on,preallocation=metadata \
    disk.qcow2 50G
```

#### Raw vs QCOW2

- **QCOW2**: Snapshots, thin provisioning, compression (slower)
- **Raw**: Better performance, no snapshots (faster)

Use Raw for production VMs with high I/O requirements.

### Network Optimization

```yaml
arguments:
  - netdev: "user,id=net0"
  - device: "virtio-net-pci,netdev=net0"  # VirtIO networking
```

### System-Level Tuning

#### Kernel Parameters

```bash
# /etc/sysctl.d/99-kvm.conf
vm.swappiness = 10
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5
```

#### CPU Governor

```bash
# Set performance governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## Troubleshooting

### Common Issues

#### Daemon Won't Start

```bash
# Check logs
journalctl --user -u maqetd.service -n 50

# Check DBus
python3 -c "import dbus; print('OK')"

# Start in foreground to see errors
maqet daemon start --foreground
```

#### Permission Denied Errors

```bash
# Check KVM permissions
ls -l /dev/kvm
groups $USER | grep kvm

# Fix KVM permissions
sudo usermod -a -G kvm $USER
# Log out and back in
```

#### VM Won't Start

```bash
# Enable debug logging
maqet --log-file /tmp/debug.log -vv start myvm
cat /tmp/debug.log

# Check QEMU binary
which qemu-system-x86_64
qemu-system-x86_64 --version

# Check storage files exist
maqet status myvm | jq '.storage'
```

#### Out of Disk Space

```bash
# Check disk usage
df -h ~/.local/share/maqet/

# Find large files
du -sh ~/.local/share/maqet/*

# Clean up old snapshots
maqet snapshot myvm list hdd
maqet snapshot myvm delete hdd old-snapshot
```

### Performance Issues

```bash
# Check if KVM is enabled
maqet status myvm | grep kvm

# Monitor VM performance
top  # Look for qemu-system processes

# Check I/O wait
iostat -x 1

# Network monitoring
iftop
```

### Getting Support

- **Documentation**: Check [docs/](../../docs/)
- **Issues**: Report at GitHub Issues
- **Logs**: Always include logs with issue reports
