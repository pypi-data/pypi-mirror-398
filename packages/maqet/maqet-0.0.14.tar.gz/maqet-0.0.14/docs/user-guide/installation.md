# Installation Guide

This guide covers installing MAQET (M4x0n's QEMU Tool) on your Linux system.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Post-Installation Verification](#post-installation-verification)
- [Virtual Environment Setup](#virtual-environment-setup)
- [Common Installation Issues](#common-installation-issues)
- [Platform-Specific Notes](#platform-specific-notes)
- [Next Steps](#next-steps)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux (POSIX-compliant)
- **Python**: 3.12 or higher
- **QEMU**: qemu-system-x86_64 or other QEMU system binaries
- **Architecture**: x86_64 (other architectures supported if QEMU binary available)

### Required Software

#### 1. Python 3.12+

Check your Python version:

```bash
python3 --version
```

If you need to install or upgrade Python:

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

**Fedora:**

```bash
sudo dnf install python3.12
```

**Arch Linux:**

```bash
sudo pacman -S python
```

#### 2. QEMU

MAQET requires QEMU system binaries to create and manage virtual machines.

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install qemu-system-x86 qemu-utils
```

**Fedora:**

```bash
sudo dnf install qemu-system-x86 qemu-img
```

**Arch Linux:**

```bash
sudo pacman -S qemu-full
```

Verify QEMU installation:

```bash
qemu-system-x86_64 --version
qemu-img --version
```

Expected output:

```
QEMU emulator version 8.0.0 (or higher)
```

#### 3. KVM Support (Optional but Recommended)

For best performance, enable KVM hardware virtualization:

Check if KVM is available:

```bash
# Check CPU virtualization support
egrep -c '(vmx|svm)' /proc/cpuinfo
# Output > 0 means CPU supports virtualization

# Check if KVM modules are loaded
lsmod | grep kvm
```

Load KVM modules if needed:

```bash
# For Intel CPUs
sudo modprobe kvm_intel

# For AMD CPUs
sudo modprobe kvm_amd
```

Add your user to the kvm group:

```bash
sudo usermod -aG kvm $USER
# Log out and back in for changes to take effect
```

---

## Installation Methods

### Method 1: Install from PyPI (Recommended)

This is the easiest method for most users:

```bash
pip install maqet
```

**Note**: Prior to v0.0.8, QEMU bindings required `pip install maqet[qemu]`.
Since v0.0.8, QEMU bindings are vendored in `maqet/vendor/` and included
automatically. No additional installation step is needed.

Verify installation:

```bash
maqet --help
```

### Method 2: Install from Source

For development or to get the latest unreleased features:

#### Clone the Repository

```bash
git clone https://gitlab.com/m4x0n_24/maqet.git
cd maqet
```

#### Install in Development Mode

```bash
# Install maqet in editable mode
pip install -e .

# Or with optional dependencies
pip install -e .[qemu,dev]
```

#### Verify Installation

```bash
maqet --help
```

### Method 3: Install with QEMU Python Bindings

MAQET can use QEMU's official Python QMP library for enhanced functionality:

```bash
# Clone maqet repository
git clone https://github.com/m4x0n/maqet.git
cd maqet

# Initialize QEMU submodule (uses sparse-checkout for minimal download)
git submodule update --init --recursive

# Install maqet
pip install -e .

# Install QEMU Python bindings
cd qemu/python
pip install .
cd ../..
```

The QEMU submodule uses sparse-checkout to only download the Python bindings directory, keeping the download size minimal (~10MB instead of ~2GB).

---

## Post-Installation Verification

### 1. Check MAQET Version

```bash
maqet --version
```

Expected output:

```
maqet version 0.0.10
```

### 2. Verify Command Availability

```bash
maqet --help
```

You should see a list of available commands including:

- add - Create a new virtual machine
- start - Start a virtual machine
- stop - Stop a virtual machine
- rm - Remove a virtual machine
- ls - List virtual machines
- status - Show VM status

### 3. Check XDG Directories

MAQET follows XDG Base Directory specifications. Verify directories are created:

```bash
# Data directory
ls -la ~/.local/share/maqet/

# Runtime directory
ls -la /run/user/$(id -u)/maqet/
```

### 4. Test Basic Functionality

Create a minimal test VM configuration:

```bash
cat > test-vm.yaml << 'EOF'
name: test-vm
binary: /usr/bin/qemu-system-x86_64
arguments:
  - m: "256M"
  - display: "none"
EOF
```

Add the VM (don't start it yet):

```bash
maqet add test-vm.yaml
```

List VMs to verify it was added:

```bash
maqet ls
```

Remove the test VM:

```bash
maqet rm test-vm --force
```

If all commands complete without errors, MAQET is properly installed.

---

## Virtual Environment Setup

Using a Python virtual environment is recommended to isolate MAQET's dependencies.

### Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv ~/.venvs/maqet

# Activate virtual environment
source ~/.venvs/maqet/bin/activate

# Install maqet
pip install maqet

# Or install from source
git clone https://github.com/m4x0n/maqet.git
cd maqet
pip install -e .
```

### Activate for Each Session

```bash
source ~/.venvs/maqet/bin/activate
maqet --help
```

### Create an Alias (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias maqet='source ~/.venvs/maqet/bin/activate && maqet'
```

---

## Common Installation Issues

### Issue 1: "command not found: maqet"

**Cause**: Python's scripts directory not in PATH

**Solution**:

Check where pip installed maqet:

```bash
pip show maqet
```

Add to PATH (typically `~/.local/bin`):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Make it permanent by adding to `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Issue 2: "ModuleNotFoundError: No module named 'maqet'"

**Cause**: MAQET not installed in current Python environment

**Solution**:

Verify pip installation:

```bash
pip list | grep maqet
```

If not listed, reinstall:

```bash
pip install maqet
```

If using virtual environment, ensure it's activated:

```bash
source ~/.venvs/maqet/bin/activate
pip install maqet
```

### Issue 3: "ERROR: Could not find a version that satisfies the requirement"

**Cause**: Python version too old (MAQET requires Python 3.12+)

**Solution**:

Check Python version:

```bash
python3 --version
```

Install Python 3.12 or higher, then use it explicitly:

```bash
python3.12 -m pip install maqet
```

### Issue 4: "qemu-system-x86_64: command not found"

**Cause**: QEMU not installed

**Solution**:

Install QEMU using your distribution's package manager (see [Prerequisites](#required-software)).

After installation, verify the binary path:

```bash
which qemu-system-x86_64
```

Update your VM configurations with the correct path if needed.

### Issue 5: Permission denied accessing /run/user/UID/maqet

**Cause**: Runtime directory permissions issue

**Solution**:

Check runtime directory permissions:

```bash
ls -la /run/user/$(id -u)/
```

Create directory manually if needed:

```bash
mkdir -p /run/user/$(id -u)/maqet
chmod 700 /run/user/$(id -u)/maqet
```

### Issue 6: KVM access denied

**Cause**: User not in kvm group

**Solution**:

Add user to kvm group:

```bash
sudo usermod -aG kvm $USER
```

Log out and log back in, then verify:

```bash
groups | grep kvm
```

Test KVM access:

```bash
ls -la /dev/kvm
```

Expected permissions: `crw-rw---- 1 root kvm`

---

## Platform-Specific Notes

### Ubuntu 22.04/24.04 LTS

```bash
# Install dependencies
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip qemu-system-x86 qemu-utils

# Install maqet
pip install --user maqet

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Fedora 38+

```bash
# Install dependencies
sudo dnf install python3.12 python3-pip qemu-system-x86 qemu-img

# Install maqet
pip install --user maqet

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Arch Linux

```bash
# Install dependencies
sudo pacman -S python python-pip qemu-full

# Install maqet
pip install --user maqet

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Debian 12 (Bookworm)

```bash
# Install dependencies
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip qemu-system-x86 qemu-utils

# Install maqet
pip install --user maqet

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Dependencies Explained

MAQET has minimal dependencies for ease of installation:

### Core Dependencies

- **python-benedict** (>=0.33.2): Nested dictionary handling for configuration merging
- **PyYAML** (>=6.0.2): YAML configuration file parsing

### Optional Dependencies

- **qemu.qmp**: QEMU Machine Protocol library (vendored in `maqet/vendor/` since v0.0.8, included by default)

**Note**: Prior to v0.0.8, QEMU bindings were an optional dependency installed with `maqet[qemu]`.
Since v0.0.8, QEMU bindings are vendored and included automatically with all installations.

### Development Dependencies

Only needed if contributing to MAQET:

- **pytest**: Test framework
- **pytest-cov**: Code coverage
- **black**: Code formatter
- **flake8**: Linter
- **mypy**: Type checker
- **isort**: Import sorter
- **pre-commit**: Git hooks

Install development dependencies:

```bash
pip install maqet[dev]
```

---

## Next Steps

After successful installation:

1. **Read the Quick Start Guide**: [quickstart.md](quickstart.md) - Learn to create your first VM
2. **Review Configuration Options**: [configuration.md](configuration.md) - Understand VM configuration
3. **Explore Examples**: Check `tests/fixtures/configs/` in the source repository
4. **Join the Community**: Report issues or contribute at <https://gitlab.com/m4x0n_24/maqet>

---

## Upgrading MAQET

### Upgrade from PyPI

```bash
pip install --upgrade maqet
```

### Upgrade from Source

```bash
cd maqet
git pull origin main
pip install --upgrade -e .
```

### Check Current Version

```bash
maqet --version
```

---

## Uninstalling MAQET

### Remove Package

```bash
pip uninstall maqet
```

### Clean Up Data Directories

```bash
# Remove VM database and configurations
rm -rf ~/.local/share/maqet/

# Remove runtime files
rm -rf /run/user/$(id -u)/maqet/

# Remove config directory (if it exists)
rm -rf ~/.config/maqet/
```

**Warning**: This will delete all VM definitions and data. Export any important configurations before uninstalling.

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review [Configuration Documentation](configuration.md)
3. Search existing issues: <https://gitlab.com/m4x0n_24/maqet/issues>
4. Open a new issue with details about your system and the error

---

**Last Updated**: 2025-10-08
**MAQET Version**: 0.0.10
