#!/usr/bin/env python3
#exonware/xwsystem/caching/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Caching types and enums for XWSystem.
"""

from enum import Enum


# ============================================================================
# CACHING ENUMS
# ============================================================================

class CachePolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    TTL = "ttl"  # Time To Live
    SIZE = "size"  # Size-based
    RANDOM = "random"  # Random eviction


class CacheStatus(Enum):
    """Cache status states."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class CacheEvent(Enum):
    """Cache events."""
    HIT = "hit"
    MISS = "miss"
    SET = "set"
    DELETE = "delete"
    EXPIRE = "expire"
    EVICT = "evict"
    CLEAR = "clear"
    ERROR = "error"


class CacheLevel(Enum):
    """Cache levels."""
    L1 = "l1"  # Memory cache
    L2 = "l2"  # Disk cache
    L3 = "l3"  # Network cache
    DISTRIBUTED = "distributed"  # Distributed cache
