#!/usr/bin/env python3
#exonware/xwsystem/ipc/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

IPC types and enums for XWSystem.
"""

from enum import Enum


# ============================================================================
# IPC ENUMS
# ============================================================================

class IPCType(Enum):
    """IPC communication types."""
    PIPE = "pipe"
    QUEUE = "queue"
    SHARED_MEMORY = "shared_memory"
    SOCKET = "socket"
    FILE = "file"


class MessageType(Enum):
    """Message types."""
    DATA = "data"
    CONTROL = "control"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class ProcessState(Enum):
    """Process states."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class QueueType(Enum):
    """Queue types."""
    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"
    BOUNDED = "bounded"


class SharedMemoryType(Enum):
    """Shared memory types."""
    MMAP = "mmap"
    SHM = "shm"
    POSIX = "posix"
    WINDOWS = "windows"
    SYSTEM_V = "system_v"


class MessageQueueType(Enum):
    """Types of message queues."""
    THREAD_SAFE = "thread_safe"
    PROCESS_SAFE = "process_safe"
    ASYNC = "async"
