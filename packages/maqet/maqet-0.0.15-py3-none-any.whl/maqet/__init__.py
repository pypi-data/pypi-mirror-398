"""
> LESS MARKETING, MORE FACTS!.

MAQET - M4x0n's QEMU Tool

A revolutionary VM management system implementing unified API generation architecture.

MAQET transforms traditional VM management by providing a "write once, generate everywhere"
approach where single @api_method decorated methods automatically become:
- CLI commands (maqet <command>)
- Python API methods (maqet.method())
- Configuration-driven calls (YAML key → method execution)

Key Features:
- Zero duplication: One method definition serves all interfaces
- Type-safe validation across CLI and Python APIs
- SQLite state management with XDG directory compliance
- Complete VM lifecycle management (add, start, stop, rm, etc.)
- QMP integration for VM control
- Production-ready for dependent projects

Quick Start:
    # CLI usage
    $ maqet add config.yaml --name myvm
    $ maqet start myvm --detach

    # Python API usage
    from maqet import Maqet
    maqet = Maqet()
    vm_id = maqet.add(name='myvm', memory='4G')
    maqet.start(vm_id, detach=True)

    # Configuration-driven usage
    add: {name: 'myvm', memory: '4G'}
    start: {vm_id: 'myvm', detach: true}

Architecture:
The unified API system consists of:
- @api_method decorator for metadata capture
- APIRegistry for tracking decorated methods
- Generators for creating interfaces (CLI, Python, Config)
- StateManager for persistent VM state
- Machine class for QEMU integration
"""

from .api import api_method
from .maqet import Maqet, MaqetError
from .state import StateManager, VMInstance
from .__version__ import __version__

__all__ = ["Maqet", "MaqetError", "StateManager", "VMInstance", "api_method", "__version__"]
