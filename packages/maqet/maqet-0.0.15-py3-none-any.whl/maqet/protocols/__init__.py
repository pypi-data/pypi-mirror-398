"""Protocol interfaces for maqet dependency inversion.

This module provides Protocol-based interfaces that enable loose coupling
between components and eliminate circular dependencies. All protocols use
runtime_checkable for isinstance() support.
"""

from maqet.protocols.ipc import IPCClientProtocol
from maqet.protocols.process import ProcessProtocol, ProcessSpawnerProtocol
from maqet.protocols.qmp import QMPManagerProtocol
from maqet.protocols.state import (
    PathResolverProtocol,
    StateProtocol,
    VMRepositoryProtocol,
)
from maqet.protocols.storage import StorageRegistryProtocol

__all__ = [
    "IPCClientProtocol",
    "PathResolverProtocol",
    "ProcessProtocol",
    "ProcessSpawnerProtocol",
    "QMPManagerProtocol",
    "StateProtocol",
    "StorageRegistryProtocol",
    "VMRepositoryProtocol",
]
