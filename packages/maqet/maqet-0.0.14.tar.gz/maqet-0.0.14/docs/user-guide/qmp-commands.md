# QMP Commands Reference

Complete QEMU Machine Protocol (QMP) command reference for MAQET.

## Table of Contents

- [QMP Overview](#qmp-overview)
- [Daemon Mode](#daemon-mode)
- [Keyboard Commands](#keyboard-commands)
- [Display Commands](#display-commands)
- [VM Control Commands](#vm-control-commands)
- [Device Management Commands](#device-management-commands)
- [Raw QMP Commands](#raw-qmp-commands)
- [QMP Protocol Details](#qmp-protocol-details)

## QMP Overview

QEMU Machine Protocol (QMP) is a JSON-based protocol for controlling QEMU instances. MAQET provides high-level wrappers for common QMP operations.

### What is QMP?

QMP enables:

- **Keyboard input** to VMs (typing, key combinations)
- **Display capture** (screenshots)
- **VM control** (pause, resume, powerdown)
- **Device management** (hot-plug, hot-unplug)
- **Status queries** (VM state, devices, etc.)

### Process Architecture Considerations

**Python API Mode:**

- QMP works seamlessly within the same Python process
- Machine instances persist with QMP connections
- No daemon required

**CLI Mode:**

- Each CLI command runs in a separate process
- Machine instances are lost between commands
- **Daemon required for QMP commands**

### QMP Socket Location

QMP sockets are created at:

```
/run/user/<UID>/maqet/sockets/<VM_ID>.sock
```

Example:

```
/run/user/1000/maqet/sockets/myvm.sock
```

## Daemon Mode

The daemon maintains persistent Machine instances and QMP connections for CLI usage.

### Starting the Daemon

**CLI:**

```bash
# Start in background
maqet daemon start

# Start in foreground (for debugging)
maqet daemon start --foreground
```

**Python API:**

```python
from maqet import Maqet

maqet = Maqet()
maqet.daemon("start")
```

### Checking Daemon Status

**CLI:**

```bash
maqet daemon status
```

**Output:**

```json
{
  "status": "running",
  "pid": 12345,
  "uptime": "2h 34m"
}
```

### Stopping the Daemon

**CLI:**

```bash
maqet daemon stop
```

### When to Use Daemon

Use daemon when:

- Running QMP commands from CLI
- Long-running VM monitoring
- Cross-process VM management
- Multiple CLI sessions need QMP access

Don't need daemon when:

- Using Python API exclusively
- Just managing VM lifecycle (start/stop)
- No QMP automation required

## Keyboard Commands

### Key Press Commands

Send single keys or key combinations to VM.

#### `qmp keys` - Send Key Combination

**CLI Syntax:**

```bash
maqet qmp keys [OPTIONS] VM_ID KEY [KEY...]
```

**Python API:**

```python
maqet.qmp_key(vm_id, *keys, hold_time=100)
```

**Parameters:**

- `vm_id` (str): VM identifier
- `keys` (str): One or more key names
- `hold_time` (int, optional): Key hold duration in milliseconds (default: 100)

**Examples:**

```bash
# CLI: Switch to TTY2
maqet qmp keys myvm ctrl alt f2

# CLI: Send Ctrl+C
maqet qmp keys myvm ctrl c

# CLI: Custom hold time
maqet qmp keys myvm --hold-time 200 ctrl alt delete
```

```python
# Python: Switch to TTY2
maqet.qmp_key("myvm", "ctrl", "alt", "f2")

# Python: Send Ctrl+C
maqet.qmp_key("myvm", "ctrl", "c")

# Python: Custom hold time
maqet.qmp_key("myvm", "ctrl", "alt", "delete", hold_time=200)
```

---

#### `qmp type` - Type Text String

Type text to VM as if typing on keyboard.

**CLI Syntax:**

```bash
maqet qmp type [OPTIONS] VM_ID TEXT
```

**Python API:**

```python
maqet.qmp_type(vm_id, text, hold_time=100)
```

**Parameters:**

- `vm_id` (str): VM identifier
- `text` (str): Text to type
- `hold_time` (int, optional): Key hold duration in milliseconds (default: 100)

**Examples:**

```bash
# CLI: Type username
maqet qmp type myvm root

# CLI: Type command with spaces (quote required)
maqet qmp type myvm "ls -la /home"

# CLI: Slower typing
maqet qmp type myvm --hold-time 150 "sensitive-data"
```

```python
# Python: Type username
maqet.qmp_type("myvm", "root")

# Python: Type command
maqet.qmp_type("myvm", "ls -la /home")

# Python: Slower typing
maqet.qmp_type("myvm", "sensitive-data", hold_time=150)
```

**Supported characters:**

- Letters: a-z, A-Z
- Numbers: 0-9
- Symbols: ` ~ ! @ # $ % ^ & * ( ) - _ = + [ ] { } \ | ; : ' " , < . > / ?
- Special: space, enter (newline), return (carriage return)

**Unsupported characters:**

- Unicode/non-ASCII characters
- Control characters (except \n, \r)

---

### Available Key Names

#### Modifier Keys

```
shift, shift_r        # Shift keys
ctrl, ctrl_r          # Control keys
alt, alt_r            # Alt keys
meta_l, meta_r        # Meta/Windows keys
menu                  # Menu key
```

#### Function Keys

```
f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12
f13, f14, f15, f16, f17, f18, f19, f20, f21, f22, f23, f24
```

#### Navigation Keys

```
up, down, left, right      # Arrow keys
home, end                  # Home/End
pgup, pgdn                 # Page Up/Down
insert, delete             # Insert/Delete
```

#### Special Keys

```
esc                   # Escape
ret                   # Return/Enter
tab                   # Tab
backspace             # Backspace
spc                   # Space
caps_lock             # Caps Lock
num_lock              # Num Lock
scroll_lock           # Scroll Lock
print, sysrq          # Print Screen/SysRq
pause                 # Pause/Break
```

#### Alphanumeric Keys

```
a-z                   # Letters (lowercase)
0-9                   # Numbers
```

#### Symbol Keys

```
minus                 # -
equal                 # =
bracket_left          # [
bracket_right         # ]
backslash             # \
semicolon             # ;
apostrophe            # '
grave_accent          # `
comma                 # ,
dot                   # .
slash                 # /
less                  # <
asterisk              # *
```

#### Keypad Keys

```
kp_0 to kp_9          # Numpad 0-9
kp_divide             # Numpad /
kp_multiply           # Numpad *
kp_subtract           # Numpad -
kp_add                # Numpad +
kp_enter              # Numpad Enter
kp_decimal            # Numpad .
```

#### Media Keys

```
volumeup, volumedown  # Volume control
audiomute             # Mute
audionext             # Next track
audioprev             # Previous track
audiostop             # Stop
audioplay             # Play/Pause
mediaselect           # Media select
```

#### System Keys

```
power                 # Power button
sleep                 # Sleep
wake                  # Wake
calculator            # Calculator
computer              # Computer
mail                  # Mail
```

#### Special Function Keys

```
help                  # Help
undo                  # Undo
copy                  # Copy
paste                 # Paste
cut                   # Cut
find                  # Find
open                  # Open
stop                  # Stop
again                 # Again
props                 # Properties
front                 # Front
```

---

### Common Key Combinations

**TTY Switching:**

```bash
# Switch to TTY1-6
maqet qmp keys myvm ctrl alt f1  # TTY1 (often graphical)
maqet qmp keys myvm ctrl alt f2  # TTY2
maqet qmp keys myvm ctrl alt f3  # TTY3
# ... up to f6

# Switch to graphical (TTY7 on some systems)
maqet qmp keys myvm ctrl alt f7
```

**Text Editing:**

```bash
# Copy
maqet qmp keys myvm ctrl c

# Paste
maqet qmp keys myvm ctrl v

# Cut
maqet qmp keys myvm ctrl x

# Undo
maqet qmp keys myvm ctrl z

# Select all
maqet qmp keys myvm ctrl a
```

**Process Control:**

```bash
# Interrupt (Ctrl+C)
maqet qmp keys myvm ctrl c

# End of file (Ctrl+D)
maqet qmp keys myvm ctrl d

# Suspend (Ctrl+Z)
maqet qmp keys myvm ctrl z

# Kill line (Ctrl+U)
maqet qmp keys myvm ctrl u
```

**Window Management:**

```bash
# Close window
maqet qmp keys myvm alt f4

# Switch windows
maqet qmp keys myvm alt tab

# Minimize
maqet qmp keys myvm meta_l d
```

---

## Display Commands

### Screenshot Capture

#### `qmp screendump` - Capture VM Screen

Capture the VM's display as a PPM image file.

**CLI Syntax:**

```bash
maqet qmp screendump VM_ID FILENAME
```

**Python API:**

```python
maqet.screendump(vm_id, filename)
```

**Parameters:**

- `vm_id` (str): VM identifier
- `filename` (str): Output filename (PPM format)

**Examples:**

```bash
# CLI: Basic screenshot
maqet qmp screendump myvm screenshot.ppm

# CLI: Timestamped screenshot
maqet qmp screendump myvm "screen_$(date +%Y%m%d_%H%M%S).ppm"
```

```python
# Python: Basic screenshot
maqet.screendump("myvm", "screenshot.ppm")

# Python: Timestamped screenshot
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
maqet.screendump("myvm", f"screen_{timestamp}.ppm")
```

**Output format:**

Screenshots are saved in PPM (Portable Pixmap) format. Convert to PNG/JPEG:

```bash
# Using ImageMagick
convert screenshot.ppm screenshot.png

# Using Python PIL
from PIL import Image
img = Image.open("screenshot.ppm")
img.save("screenshot.png")
```

**Use cases:**

- Visual VM monitoring
- Automated testing with screenshot validation
- Documentation generation
- Debugging display issues

---

## VM Control Commands

### Pause and Resume

#### `qmp pause` - Pause VM Execution

Pause (freeze) VM execution via QMP.

**CLI Syntax:**

```bash
maqet qmp pause VM_ID
```

**Python API:**

```python
maqet.qmp_stop(vm_id)
```

**Note:** Method name is `qmp_stop()` in Python (QMP command is "stop").

**Examples:**

```bash
# CLI: Pause VM
maqet qmp pause myvm
```

```python
# Python: Pause VM
maqet.qmp_stop("myvm")
```

**Use cases:**

- Taking consistent snapshots
- Freezing VM state for inspection
- Debugging guest OS

---

#### `qmp resume` - Resume VM Execution

Resume paused VM execution.

**CLI Syntax:**

```bash
maqet qmp resume VM_ID
```

**Python API:**

```python
maqet.qmp_cont(vm_id)
```

**Note:** Method name is `qmp_cont()` in Python (QMP command is "cont").

**Examples:**

```bash
# CLI: Resume VM
maqet qmp resume myvm
```

```python
# Python: Resume VM
maqet.qmp_cont("myvm")
```

---

### Pause and Snapshot Workflow

**CLI:**

```bash
# Pause for consistent snapshot
maqet qmp pause myvm
maqet snapshot myvm create hdd frozen-state
maqet qmp resume myvm
```

**Python API:**

```python
# Pause for consistent snapshot
maqet.qmp_stop("myvm")
maqet.snapshot("myvm", "create", "hdd", "frozen-state")
maqet.qmp_cont("myvm")
```

---

## Device Management Commands

### Hot-Plug Devices

#### `qmp device-add` - Add Device

Hot-plug device to running VM.

**CLI Syntax:**

```bash
maqet qmp device-add VM_ID DRIVER --device-id ID [OPTIONS...]
```

**Python API:**

```python
maqet.device_add(vm_id, driver, device_id, **kwargs)
```

**Parameters:**

- `vm_id` (str): VM identifier
- `driver` (str): Device driver name
- `device_id` (str): Unique device identifier
- `**kwargs`: Driver-specific properties

**Examples:**

```bash
# CLI: Add USB storage
maqet qmp device-add myvm usb-storage --device-id usb1 --drive usb-drive

# CLI: Add network device
maqet qmp device-add myvm e1000 --device-id net1 --netdev user1

# CLI: Add virtio-serial
maqet qmp device-add myvm virtio-serial --device-id serial1
```

```python
# Python: Add USB storage
maqet.device_add("myvm", driver="usb-storage", device_id="usb1", drive="usb-drive")

# Python: Add network device
maqet.device_add("myvm", driver="e1000", device_id="net1", netdev="user1")

# Python: Add virtio-serial
maqet.device_add("myvm", driver="virtio-serial", device_id="serial1")
```

**Common device drivers:**

- `usb-storage`: USB mass storage
- `usb-kbd`: USB keyboard
- `usb-mouse`: USB mouse
- `e1000`: Intel E1000 network card
- `virtio-net-pci`: VirtIO network device
- `virtio-blk-pci`: VirtIO block device
- `virtio-serial`: VirtIO serial port

---

#### `qmp device-del` - Remove Device

Hot-unplug device from running VM.

**CLI Syntax:**

```bash
maqet qmp device-del VM_ID DEVICE_ID
```

**Python API:**

```python
maqet.device_del(vm_id, device_id)
```

**Parameters:**

- `vm_id` (str): VM identifier
- `device_id` (str): Device identifier to remove

**Examples:**

```bash
# CLI: Remove USB device
maqet qmp device-del myvm usb1

# CLI: Remove network device
maqet qmp device-del myvm net1
```

```python
# Python: Remove USB device
maqet.device_del("myvm", "usb1")

# Python: Remove network device
maqet.device_del("myvm", "net1")
```

**Important notes:**

- Device ID must match the one used in `device-add`
- Some devices may not support hot-unplug
- Guest OS cooperation may be required

---

## Raw QMP Commands

### Generic QMP Execution

#### `qmp` - Execute Raw QMP Command

Execute any QMP command directly.

**CLI Syntax:**

```bash
maqet qmp VM_ID COMMAND [ARGS...]
```

**Python API:**

```python
maqet.qmp(vm_id, command, **kwargs)
```

**Parameters:**

- `vm_id` (str): VM identifier
- `command` (str): QMP command name
- `**kwargs`: Command-specific arguments

**Examples:**

```bash
# CLI: Power down VM
maqet qmp myvm system_powerdown

# CLI: Query VM status
maqet qmp myvm query-status

# CLI: Query block devices
maqet qmp myvm query-block

# CLI: Query CPUs
maqet qmp myvm query-cpus-fast
```

```python
# Python: Power down VM
maqet.qmp("myvm", "system_powerdown")

# Python: Query VM status
status = maqet.qmp("myvm", "query-status")
print(status)  # {'status': 'running', 'running': True}

# Python: Query block devices
blocks = maqet.qmp("myvm", "query-block")

# Python: Query CPUs
cpus = maqet.qmp("myvm", "query-cpus-fast")
```

---

### Useful QMP Commands

#### System Commands

```bash
# Power down VM gracefully
maqet qmp myvm system_powerdown

# Reset VM
maqet qmp myvm system_reset

# Wake up VM
maqet qmp myvm system_wakeup
```

#### Query Commands

```bash
# Query VM status
maqet qmp myvm query-status

# Query block devices
maqet qmp myvm query-block

# Query network devices
maqet qmp myvm query-network

# Query CPUs
maqet qmp myvm query-cpus-fast

# Query PCI devices
maqet qmp myvm query-pci

# Query memory size
maqet qmp myvm query-memory-size-summary
```

#### Block Device Commands

```bash
# Eject CD-ROM
maqet qmp myvm eject --device ide0-cd0

# Change CD-ROM media
maqet qmp myvm blockdev-change-medium --device ide0-cd0 --filename /path/to/new.iso
```

---

## QMP Protocol Details

### Connection Method

MAQET uses UNIX domain sockets for QMP communication:

**Socket path:**

```
/run/user/<UID>/maqet/sockets/<VM_ID>.sock
```

**Connection:**

- Socket created when VM starts
- Removed when VM stops
- Requires read/write permissions

### Message Format

QMP uses JSON-based protocol:

**Request:**

```json
{
  "execute": "command-name",
  "arguments": {
    "arg1": "value1",
    "arg2": "value2"
  }
}
```

**Response:**

```json
{
  "return": {
    "result": "data"
  }
}
```

**Error:**

```json
{
  "error": {
    "class": "ErrorClass",
    "desc": "Error description"
  }
}
```

### MAQET QMP Abstraction

MAQET abstracts QMP complexity:

1. **Socket management**: Automatic socket creation/cleanup
2. **Connection handling**: Persistent connections in daemon mode
3. **Command wrapping**: High-level methods for common operations
4. **Error handling**: Python exceptions from QMP errors

**Example internal flow:**

```python
# User calls:
maqet.qmp_key("myvm", "ctrl", "c")

# MAQET does:
1. Get Machine instance from daemon/cache
2. Get QMP socket path: /run/user/1000/maqet/sockets/myvm.sock
3. Build QMP command:
   {
     "execute": "send-key",
     "arguments": {
       "keys": [
         {"type": "qcode", "data": "ctrl"},
         {"type": "qcode", "data": "c"}
       ],
       "hold-time": 100
     }
   }
4. Send to socket and wait for response
5. Return result or raise exception
```

### Available QMP Commands

QEMU provides 200+ QMP commands. Common categories:

- **VM control**: start, stop, pause, resume, reset
- **Block devices**: eject, change-media, snapshot
- **Display**: screendump, set_password
- **Input**: send-key, input-send-event
- **Migration**: migrate, migrate-cancel
- **Monitoring**: query-status, query-block, query-cpus
- **Device management**: device_add, device_del

**Full QMP reference:**
<https://qemu-project.gitlab.io/qemu/interop/qemu-qmp-ref.html>

---

## Troubleshooting

### QMP Command Fails in CLI

**Symptom:**

```bash
$ maqet qmp keys myvm ctrl c
Error: QMP not available for VM 'myvm' - VM was started in a different process
```

**Solution:**

Start the daemon:

```bash
maqet daemon start
```

**Why this happens:**

- CLI commands run in separate processes
- QMP requires persistent Machine instances
- Daemon maintains instances across processes

---

### Socket Permission Denied

**Symptom:**

```bash
Error: Permission denied accessing /run/user/1000/maqet/sockets/myvm.sock
```

**Solution:**

Check socket ownership and permissions:

```bash
ls -la /run/user/1000/maqet/sockets/
```

Ensure:

- Socket owned by your user
- Socket has rw permissions
- Parent directory accessible

---

### Key Not Recognized

**Symptom:**

```bash
Error: Character 'X' cannot be translated into keys
```

**Solution:**

- Use lowercase for letters: `a` not `A`
- For uppercase, use shift: `shift a`
- Check available keys list above

---

### Daemon Not Responding

**Symptom:**

```bash
$ maqet daemon status
Error: Failed to connect to daemon
```

**Solution:**

Restart the daemon:

```bash
maqet daemon stop
maqet daemon start
```

Check daemon logs:

```bash
maqet daemon start --foreground
```

---

## See Also

- [Python API Reference](../api/python-api.md) - Complete API documentation
- [CLI Reference](../api/cli-reference.md) - Command-line interface documentation
- [Examples](../api/examples.md) - Practical code examples
- [QEMU QMP Reference](https://qemu-project.gitlab.io/qemu/interop/qemu-qmp-ref.html) - Official QMP documentation
