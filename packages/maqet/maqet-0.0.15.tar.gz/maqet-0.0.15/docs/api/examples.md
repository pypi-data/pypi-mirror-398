# API Examples

Practical code examples for common MAQET tasks with both Python API and CLI approaches.

## Table of Contents

- [Basic VM Operations](#basic-vm-operations)
- [QMP Keyboard Automation](#qmp-keyboard-automation)
- [Screenshot Capture](#screenshot-capture)
- [Snapshot Management](#snapshot-management)
- [Multiple VM Orchestration](#multiple-vm-orchestration)
- [Error Handling Patterns](#error-handling-patterns)
- [Configuration Management](#configuration-management)
- [CI/CD Integration](#cicd-integration)

## Basic VM Operations

### Creating and Starting a VM

**Python API:**

```python
from maqet import Maqet

# Create MAQET instance
maqet = Maqet()

# Create VM from config
vm_id = maqet.add(vm_config="config.yaml", name="myvm")
print(f"Created VM: {vm_id}")

# Start the VM
vm = maqet.start(vm_id)
print(f"VM started with PID: {vm.pid}")

# Check status
status = maqet.status(vm_id)
print(f"Status: {status['status']}")
print(f"Memory: {status['configuration']['memory']}")
print(f"CPUs: {status['configuration']['cpu']}")
```

**CLI:**

```bash
# Create VM
maqet add config.yaml --name myvm

# Start VM
maqet start myvm

# Check status
maqet status myvm
```

---

### Stopping and Removing VMs

**Python API:**

```python
from maqet import Maqet

maqet = Maqet()

# Graceful shutdown
try:
    maqet.stop("myvm")
    print("VM stopped gracefully")
except Exception as e:
    print(f"Graceful stop failed: {e}")
    # Force kill
    maqet.stop("myvm", force=True)
    print("VM forcefully stopped")

# Remove VM and storage
maqet.rm("myvm", force=True, clean_storage=True)
print("VM removed")
```

**CLI:**

```bash
# Graceful stop
maqet stop myvm

# Force stop if needed
maqet stop myvm --force

# Remove with storage cleanup
maqet rm myvm --force --clean-storage
```

---

### Context Manager Pattern

**Python API:**

```python
from maqet import Maqet, MaqetError

# Automatic cleanup on exit
with Maqet() as maqet:
    try:
        # Create and start VM
        vm_id = maqet.add(vm_config="config.yaml", name="auto-cleanup-vm")
        maqet.start(vm_id)

        # Perform operations
        status = maqet.status(vm_id)
        print(f"Running VM: {status['name']}")

        # VM automatically stopped and cleaned up on exit
    except MaqetError as e:
        print(f"Error: {e}")
        # Cleanup still happens
```

---

## QMP Keyboard Automation

### Automated Login Sequence

**Python API:**

```python
from maqet import Maqet
import time

def automated_login(maqet, vm_id, username, password):
    """Automate VM login via QMP keyboard."""
    # Wait for boot
    time.sleep(10)

    # Type username
    maqet.qmp_type(vm_id, username)
    maqet.qmp_key(vm_id, "ret")

    # Wait for password prompt
    time.sleep(1)

    # Type password
    maqet.qmp_type(vm_id, password)
    maqet.qmp_key(vm_id, "ret")

    # Wait for login
    time.sleep(2)

# Usage
with Maqet() as maqet:
    vm_id = maqet.add(vm_config="vm.yaml", name="test-vm")
    maqet.start(vm_id)

    automated_login(maqet, vm_id, "root", "password")
    print("Login complete")
```

**CLI (with daemon):**

```bash
# Start daemon for QMP
maqet daemon start

# Start VM
maqet start test-vm

# Wait for boot
sleep 10

# Login sequence
maqet qmp type test-vm root
maqet qmp keys test-vm ret
sleep 1
maqet qmp type test-vm password
maqet qmp keys test-vm ret
sleep 2

echo "Login complete"
```

---

### Running Commands in Guest

**Python API:**

```python
from maqet import Maqet
import time

def run_guest_command(maqet, vm_id, command, capture_screenshot=True):
    """Run command in guest OS and optionally capture screenshot."""
    # Type command
    maqet.qmp_type(vm_id, command)
    maqet.qmp_key(vm_id, "ret")

    # Wait for command execution
    time.sleep(2)

    # Capture result
    if capture_screenshot:
        screenshot_name = f"{command.replace(' ', '_')}.ppm"
        maqet.screendump(vm_id, screenshot_name)
        print(f"Screenshot saved: {screenshot_name}")

# Usage
with Maqet() as maqet:
    vm_id = "test-vm"

    commands = [
        "ip addr show",
        "df -h",
        "systemctl status",
        "uname -a"
    ]

    for cmd in commands:
        run_guest_command(maqet, vm_id, cmd)
        time.sleep(1)
```

**CLI:**

```bash
#!/bin/bash
# run-guest-commands.sh

VM="test-vm"

commands=(
    "ip addr show"
    "df -h"
    "systemctl status"
    "uname -a"
)

for cmd in "${commands[@]}"; do
    echo "Running: $cmd"
    maqet qmp type "$VM" "$cmd"
    maqet qmp keys "$VM" ret
    sleep 2

    # Capture screenshot
    filename="${cmd// /_}.ppm"
    maqet qmp screendump "$VM" "$filename"
    echo "Screenshot: $filename"
    sleep 1
done
```

---

### TTY Switching and Special Keys

**Python API:**

```python
from maqet import Maqet

maqet = Maqet()
vm_id = "myvm"

# Switch to TTY2
maqet.qmp_key(vm_id, "ctrl", "alt", "f2")

# Switch back to graphical (TTY1 or TTY7)
maqet.qmp_key(vm_id, "ctrl", "alt", "f1")

# Send Ctrl+C (interrupt)
maqet.qmp_key(vm_id, "ctrl", "c")

# Send Ctrl+Alt+Delete
maqet.qmp_key(vm_id, "ctrl", "alt", "delete")

# Function keys
maqet.qmp_key(vm_id, "f1")  # Help
maqet.qmp_key(vm_id, "alt", "f4")  # Close window
```

**CLI:**

```bash
# Switch to TTY2
maqet qmp keys myvm ctrl alt f2

# Switch back to GUI
maqet qmp keys myvm ctrl alt f1

# Interrupt command
maqet qmp keys myvm ctrl c

# Reboot prompt
maqet qmp keys myvm ctrl alt delete

# Function keys
maqet qmp keys myvm f1
maqet qmp keys myvm alt f4
```

---

## Screenshot Capture

### Sequential Screenshots for Monitoring

**Python API:**

```python
from maqet import Maqet
import time
from datetime import datetime

def monitor_vm_with_screenshots(maqet, vm_id, duration=60, interval=10):
    """Capture screenshots at regular intervals."""
    screenshots = []
    start_time = time.time()

    while (time.time() - start_time) < duration:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screen_{vm_id}_{timestamp}.ppm"

        try:
            maqet.screendump(vm_id, filename)
            screenshots.append(filename)
            print(f"Captured: {filename}")
        except Exception as e:
            print(f"Screenshot failed: {e}")

        time.sleep(interval)

    return screenshots

# Usage
with Maqet() as maqet:
    screens = monitor_vm_with_screenshots(maqet, "myvm", duration=120, interval=15)
    print(f"Captured {len(screens)} screenshots")
```

**CLI:**

```bash
#!/bin/bash
# monitor-screenshots.sh

VM="myvm"
DURATION=120  # seconds
INTERVAL=15   # seconds

end_time=$(($(date +%s) + DURATION))

while [ $(date +%s) -lt $end_time ]; do
    timestamp=$(date +%Y%m%d_%H%M%S)
    filename="screen_${VM}_${timestamp}.ppm"

    maqet qmp screendump "$VM" "$filename"
    echo "Captured: $filename"

    sleep $INTERVAL
done
```

---

### Converting Screenshots to PNG

**Python API:**

```python
from maqet import Maqet
from PIL import Image

def screenshot_to_png(maqet, vm_id, output_png):
    """Capture screenshot and convert to PNG."""
    import tempfile
    import os

    # Capture to temporary PPM file
    with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as tmp:
        tmp_ppm = tmp.name

    try:
        maqet.screendump(vm_id, tmp_ppm)

        # Convert to PNG
        img = Image.open(tmp_ppm)
        img.save(output_png)
        print(f"Screenshot saved: {output_png}")
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_ppm):
            os.remove(tmp_ppm)

# Usage
with Maqet() as maqet:
    screenshot_to_png(maqet, "myvm", "vm_screenshot.png")
```

**CLI:**

```bash
# Using ImageMagick
maqet qmp screendump myvm temp.ppm
convert temp.ppm screenshot.png
rm temp.ppm

# One-liner with cleanup
maqet qmp screendump myvm temp.ppm && convert temp.ppm screenshot.png && rm temp.ppm
```

---

## Snapshot Management

### Snapshot-Based Testing Workflow

**Python API:**

```python
from maqet import Maqet

def test_with_snapshot_rollback(maqet, vm_id, drive):
    """Test multiple configurations with automatic rollback."""
    # Create base snapshot
    maqet.snapshot(vm_id, "create", drive, "base-state")
    print("Base snapshot created")

    test_configs = [
        {"memory": "4G", "cpu": 2, "name": "config_small"},
        {"memory": "8G", "cpu": 4, "name": "config_medium"},
        {"memory": "16G", "cpu": 8, "name": "config_large"}
    ]

    results = []

    for config in test_configs:
        print(f"\nTesting {config['name']}...")

        # Apply configuration
        maqet.apply(vm_id, memory=config['memory'], cpu=config['cpu'])
        maqet.start(vm_id)

        # Run tests (example)
        import time
        time.sleep(5)
        status = maqet.status(vm_id)
        results.append({
            'config': config['name'],
            'status': status['status'],
            'success': True
        })

        # Stop and rollback
        maqet.stop(vm_id)
        maqet.snapshot(vm_id, "load", drive, "base-state")
        print(f"Rolled back to base state")

    return results

# Usage
with Maqet() as maqet:
    results = test_with_snapshot_rollback(maqet, "test-vm", "hdd")
    print("\nTest Results:")
    for result in results:
        print(f"  {result['config']}: {'PASS' if result['success'] else 'FAIL'}")
```

**CLI:**

```bash
#!/bin/bash
# test-with-snapshots.sh

VM="test-vm"
DRIVE="hdd"

# Create base snapshot
maqet snapshot "$VM" create "$DRIVE" base-state
echo "Base snapshot created"

# Test configurations
declare -a configs=(
    "4G:2:small"
    "8G:4:medium"
    "16G:8:large"
)

for config in "${configs[@]}"; do
    IFS=':' read -r memory cpu name <<< "$config"
    echo ""
    echo "Testing $name configuration..."

    # Apply config
    maqet apply "$VM" --memory "$memory" --cpu "$cpu"
    maqet start "$VM"

    # Run tests
    sleep 5
    maqet status "$VM"

    # Rollback
    maqet stop "$VM"
    maqet snapshot "$VM" load "$DRIVE" base-state
    echo "Rolled back to base state"
done

echo ""
echo "All tests complete"
```

---

### Backup Before Updates

**Python API:**

```python
from maqet import Maqet
from datetime import datetime

def backup_before_update(maqet, vm_id, drive):
    """Create timestamped backup before applying updates."""
    # Create backup snapshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"pre_update_{timestamp}"

    print(f"Creating backup: {backup_name}")
    maqet.snapshot(vm_id, "create", drive, backup_name)

    try:
        # Start VM and apply updates
        maqet.start(vm_id)

        # Simulate update process
        maqet.qmp_type(vm_id, "apt update && apt upgrade -y")
        maqet.qmp_key(vm_id, "ret")

        # Wait for updates
        import time
        time.sleep(60)

        # Verify success
        status = maqet.status(vm_id)
        if status['is_running']:
            print("Update completed successfully")
            return backup_name
        else:
            raise Exception("VM not running after update")

    except Exception as e:
        print(f"Update failed: {e}")
        print(f"Rolling back to {backup_name}...")

        maqet.stop(vm_id, force=True)
        maqet.snapshot(vm_id, "load", drive, backup_name)
        print("Rollback complete")
        raise

# Usage
with Maqet() as maqet:
    backup = backup_before_update(maqet, "prod-vm", "system")
    print(f"Backup available: {backup}")
```

---

## Multiple VM Orchestration

### Cluster Management

**Python API:**

```python
from maqet import Maqet
import concurrent.futures

def create_vm_cluster(maqet, base_config, cluster_name, node_count=3):
    """Create and start multiple VMs in parallel."""
    vm_ids = []

    # Create VMs
    for i in range(node_count):
        vm_name = f"{cluster_name}-node-{i+1}"
        vm_id = maqet.add(
            vm_config=base_config,
            name=vm_name,
            memory=f"{4 + i}G",  # Incremental memory
            cpu=2 + i  # Incremental CPUs
        )
        vm_ids.append(vm_id)
        print(f"Created {vm_name}")

    # Start VMs in parallel
    def start_vm(vm_id):
        try:
            maqet.start(vm_id)
            return (vm_id, True, None)
        except Exception as e:
            return (vm_id, False, str(e))

    with concurrent.futures.ThreadPoolExecutor(max_workers=node_count) as executor:
        futures = [executor.submit(start_vm, vm_id) for vm_id in vm_ids]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Report results
    success_count = sum(1 for _, success, _ in results if success)
    print(f"\nCluster status: {success_count}/{node_count} nodes started")

    return vm_ids

# Usage
with Maqet() as maqet:
    cluster_vms = create_vm_cluster(maqet, "node-base.yaml", "web-cluster", 5)

    # List running cluster
    print("\nCluster VMs:")
    print(maqet.ls(status="running"))
```

**CLI:**

```bash
#!/bin/bash
# create-cluster.sh

CLUSTER_NAME="web-cluster"
NODE_COUNT=5
BASE_CONFIG="node-base.yaml"

# Create VMs
for i in $(seq 1 $NODE_COUNT); do
    vm_name="${CLUSTER_NAME}-node-${i}"
    memory="$((4 + i - 1))G"
    cpu=$((2 + i - 1))

    echo "Creating $vm_name..."
    maqet add "$BASE_CONFIG" --name "$vm_name" \
        --memory "$memory" --cpu "$cpu"
done

# Start VMs in parallel
echo ""
echo "Starting cluster nodes..."
for i in $(seq 1 $NODE_COUNT); do
    vm_name="${CLUSTER_NAME}-node-${i}"
    maqet start "$vm_name" &
done

# Wait for all background jobs
wait

echo ""
echo "Cluster ready:"
maqet ls --status running
```

---

### Load Balancer Configuration

**Python API:**

```python
from maqet import Maqet
import time

def configure_load_balancer(maqet, backend_vms):
    """Configure load balancer VM with backend nodes."""
    lb_vm = maqet.add(vm_config="lb-config.yaml", name="load-balancer")
    maqet.start(lb_vm)

    # Wait for boot
    time.sleep(15)

    # Login to LB
    maqet.qmp_type(lb_vm, "root")
    maqet.qmp_key(lb_vm, "ret")
    time.sleep(1)
    maqet.qmp_type(lb_vm, "password")
    maqet.qmp_key(lb_vm, "ret")
    time.sleep(2)

    # Configure backends
    for backend in backend_vms:
        # Get backend IP (simplified - would query VM)
        backend_ip = f"192.168.1.{backend_vms.index(backend) + 10}"

        # Add backend to config
        cmd = f"echo 'backend {backend} {backend_ip}:80' >> /etc/lb/backends.conf"
        maqet.qmp_type(lb_vm, cmd)
        maqet.qmp_key(lb_vm, "ret")
        time.sleep(1)

    # Reload load balancer
    maqet.qmp_type(lb_vm, "systemctl reload load-balancer")
    maqet.qmp_key(lb_vm, "ret")

    print("Load balancer configured")
    return lb_vm

# Usage
with Maqet() as maqet:
    # Create backend VMs
    backends = []
    for i in range(3):
        vm_id = maqet.add(vm_config="backend.yaml", name=f"web-{i+1}")
        maqet.start(vm_id)
        backends.append(vm_id)

    # Configure LB
    lb = configure_load_balancer(maqet, backends)
```

---

## Error Handling Patterns

### Retry with Exponential Backoff

**Python API:**

```python
from maqet import Maqet, MaqetError
import time

def start_vm_with_retry(maqet, vm_id, max_retries=3):
    """Start VM with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            vm = maqet.start(vm_id)
            print(f"VM started successfully (attempt {attempt + 1})")
            return vm
        except MaqetError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"Start failed (attempt {attempt + 1}): {e}")
                print(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Failed after {max_retries} attempts")
                raise

# Usage
with Maqet() as maqet:
    vm_id = maqet.add(vm_config="vm.yaml", name="retry-test")
    start_vm_with_retry(maqet, vm_id)
```

---

### Graceful Cleanup

**Python API:**

```python
from maqet import Maqet, MaqetError

def safe_vm_operation(vm_config, operation_func):
    """Execute operation with guaranteed cleanup."""
    maqet = Maqet()
    vm_id = None

    try:
        # Create and start VM
        vm_id = maqet.add(vm_config=vm_config, name="temp-vm")
        maqet.start(vm_id)

        # Execute operation
        result = operation_func(maqet, vm_id)

        return result

    except MaqetError as e:
        print(f"Operation failed: {e}")
        raise

    finally:
        # Guaranteed cleanup
        if vm_id:
            try:
                maqet.stop(vm_id, force=True)
                print("VM stopped")
            except:
                pass  # Best effort

            try:
                maqet.rm(vm_id, force=True)
                print("VM removed")
            except:
                pass  # Best effort

# Usage
def my_operation(maqet, vm_id):
    status = maqet.status(vm_id)
    print(f"VM status: {status['status']}")
    return status

result = safe_vm_operation("test.yaml", my_operation)
```

---

## Configuration Management

### Configuration File Merging

**Python API:**

```python
from maqet import Maqet

# Deep merge multiple configs
maqet = Maqet()

vm_id = maqet.add(
    vm_config=[
        "base.yaml",              # Base configuration
        "env/production.yaml",    # Environment-specific
        "overrides.yaml"          # Custom overrides
    ],
    name="prod-server",
    memory="32G"  # Final override via parameter
)

print(f"Created VM with merged config: {vm_id}")
```

**Config files:**

```yaml
# base.yaml
binary: /usr/bin/qemu-system-x86_64
arguments:
  - enable-kvm: null
  - cpu: "host"
storage:
  - name: system
    type: qcow2
    size: 50G
```

```yaml
# env/production.yaml
arguments:
  - m: "16G"
  - smp: 8
storage:
  - name: data
    type: qcow2
    size: 500G
```

```yaml
# overrides.yaml
arguments:
  - display: "none"  # Headless
  - vga: "none"
```

**CLI:**

```bash
# Multiple config merge
maqet add --vm-config base.yaml \
          --vm-config env/production.yaml \
          --vm-config overrides.yaml \
          --name prod-server \
          --memory 32G
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/vm-test.yml
name: VM Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Install MAQET
        run: |
          pip install maqet

      - name: Run VM tests
        run: |
          python tests/vm_integration_test.py
```

**Test script:**

```python
# tests/vm_integration_test.py
from maqet import Maqet
import sys

def test_vm_lifecycle():
    """Test basic VM lifecycle."""
    with Maqet() as maqet:
        # Create VM
        vm_id = maqet.add(vm_config="tests/ci-vm.yaml", name="ci-test")
        assert vm_id, "VM creation failed"

        # Start VM
        vm = maqet.start(vm_id)
        assert vm.status == "running", "VM not running"

        # Verify status
        status = maqet.status(vm_id)
        assert status['is_running'], "VM not actually running"

        print("VM lifecycle test PASSED")
        return True

if __name__ == "__main__":
    try:
        success = test_vm_lifecycle()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test FAILED: {e}")
        sys.exit(1)
```

---

### GitLab CI Example

```yaml
# .gitlab-ci.yml
test:vm:
  stage: test
  image: python:3.11
  before_script:
    - pip install maqet
  script:
    - python tests/vm_tests.py
  artifacts:
    paths:
      - screenshots/
    when: always
```

**Test script:**

```python
# tests/vm_tests.py
from maqet import Maqet
import os

def run_vm_tests():
    os.makedirs("screenshots", exist_ok=True)

    with Maqet() as maqet:
        vm_id = maqet.add(vm_config="tests/test-vm.yaml")
        maqet.start(vm_id)

        # Run tests and capture screenshots
        for test_num in range(3):
            # Perform test operations
            maqet.qmp_type(vm_id, f"test-{test_num}")
            maqet.qmp_key(vm_id, "ret")

            # Capture result
            maqet.screendump(vm_id, f"screenshots/test-{test_num}.ppm")

        print("All tests passed")

if __name__ == "__main__":
    run_vm_tests()
```

---

## See Also

- [Python API Reference](python-api.md) - Complete API documentation
- [CLI Reference](cli-reference.md) - Command-line interface documentation
- [QMP Commands](../user-guide/qmp-commands.md) - QMP command reference
- [Configuration Guide](../user-guide/configuration.md) - YAML configuration details
