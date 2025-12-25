#!/usr/bin/env python3
#exonware/xwsystem/threading/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Threading types and enums for XWSystem.
"""

from enum import Enum
from ..shared.defs import LockType


# ============================================================================
# THREADING ENUMS
# ============================================================================

class ThreadState(Enum):
    """Thread states."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    WAITING = "waiting"
    BLOCKED = "blocked"
    TERMINATED = "terminated"


class ThreadPriority(Enum):
    """Thread priorities."""
    LOWEST = 1
    LOW = 2
    NORMAL = 3
    HIGH = 4
    HIGHEST = 5


class AsyncState(Enum):
    """Async operation states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ConcurrencyMode(Enum):
    """Concurrency modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONCURRENT = "concurrent"
    ASYNC = "async"
