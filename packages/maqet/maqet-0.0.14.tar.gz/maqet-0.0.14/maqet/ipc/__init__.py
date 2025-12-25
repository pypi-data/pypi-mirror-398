"""
IPC (Inter-Process Communication) Module

Provides Unix domain socket-based IPC for communication between
CLI processes and VM runner processes.

Components:
- UnixSocketIPCServer: Server for VM runner processes
- RunnerClient: Client for CLI processes
- retry: Retry logic with exponential backoff and circuit breaker

Protocol: JSON-RPC over Unix domain sockets
"""

from .unix_socket_server import UnixSocketIPCServer
from .runner_client import RunnerClient
from .retry import (
    retry_with_backoff,
    async_retry_with_backoff,
    CircuitBreaker,
)

__all__ = [
    "UnixSocketIPCServer",
    "RunnerClient",
    "retry_with_backoff",
    "async_retry_with_backoff",
    "CircuitBreaker",
]
