"""
Inter-Process Communication (IPC) Module
========================================

Production-grade IPC utilities for XSystem.

Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Company: eXonware.com
Generated: 2025-01-27

This module provides:
- Process management and communication
- Shared memory abstractions
- Message queues and pipes
- Process pools with monitoring
- Cross-platform IPC primitives
"""

from .process_manager import ProcessManager, ProcessInfo
from .shared_memory import SharedMemoryManager, SharedData
from .message_queue import MessageQueue, AsyncMessageQueue
from .process_pool import ProcessPool, AsyncProcessPool
from .pipes import Pipe, AsyncPipe
from .async_fabric import AsyncProcessFabric

__all__ = [
    "ProcessManager",
    "ProcessInfo",
    "SharedMemoryManager",
    "SharedData",
    "MessageQueue",
    "AsyncMessageQueue",
    "ProcessPool",
    "AsyncProcessPool",
    "Pipe",
    "AsyncPipe",
    "AsyncProcessFabric",
]
