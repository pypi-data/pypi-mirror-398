#!/usr/bin/env python3
#exonware/xwsystem/caching/eviction_strategies.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Pluggable eviction strategies for caching module.
Extensibility Priority #5 - Strategy pattern for custom eviction policies.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Hashable
import random
import time


class AEvictionStrategy(ABC):
    """
    Abstract base class for eviction strategies.
    
    Implements Strategy pattern for pluggable eviction policies.
    """
    
    @abstractmethod
    def select_victim(self, cache_items: list[tuple[Hashable, Any, dict]]) -> Optional[Hashable]:
        """
        Select item to evict from cache.
        
        Args:
            cache_items: List of (key, value, metadata) tuples
                        metadata includes: access_time, access_count, size, etc.
                        
        Returns:
            Key of item to evict, or None if no eviction needed
        """
        pass
    
    @abstractmethod
    def on_access(self, key: Hashable, metadata: dict) -> None:
        """
        Update strategy state on item access.
        
        Args:
            key: Key that was accessed
            metadata: Item metadata
        """
        pass
    
    @abstractmethod
    def on_insert(self, key: Hashable, value: Any, metadata: dict) -> None:
        """
        Update strategy state on item insertion.
        
        Args:
            key: Key that was inserted
            value: Value that was inserted
            metadata: Item metadata
        """
        pass
    
    @abstractmethod
    def on_delete(self, key: Hashable) -> None:
        """
        Update strategy state on item deletion.
        
        Args:
            key: Key that was deleted
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        pass


class LRUEvictionStrategy(AEvictionStrategy):
    """Least Recently Used eviction strategy."""
    
    def select_victim(self, cache_items: list[tuple[Hashable, Any, dict]]) -> Optional[Hashable]:
        """Select least recently used item."""
        if not cache_items:
            return None
        
        # Find item with oldest access time
        lru_item = min(cache_items, key=lambda x: x[2].get('access_time', 0))
        return lru_item[0]
    
    def on_access(self, key: Hashable, metadata: dict) -> None:
        """Update access time."""
        metadata['access_time'] = time.time()
    
    def on_insert(self, key: Hashable, value: Any, metadata: dict) -> None:
        """Set initial access time."""
        metadata['access_time'] = time.time()
    
    def on_delete(self, key: Hashable) -> None:
        """No action needed on delete."""
        pass
    
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "LRU"


class LFUEvictionStrategy(AEvictionStrategy):
    """Least Frequently Used eviction strategy."""
    
    def __init__(self):
        """Initialize LFU strategy."""
        self._access_counts: dict = {}
    
    def select_victim(self, cache_items: list[tuple[Hashable, Any, dict]]) -> Optional[Hashable]:
        """Select least frequently used item."""
        if not cache_items:
            return None
        
        # Find item with lowest access count
        lfu_item = min(cache_items, key=lambda x: self._access_counts.get(x[0], 0))
        return lfu_item[0]
    
    def on_access(self, key: Hashable, metadata: dict) -> None:
        """Increment access count."""
        self._access_counts[key] = self._access_counts.get(key, 0) + 1
        metadata['access_count'] = self._access_counts[key]
    
    def on_insert(self, key: Hashable, value: Any, metadata: dict) -> None:
        """Initialize access count."""
        self._access_counts[key] = 1
        metadata['access_count'] = 1
    
    def on_delete(self, key: Hashable) -> None:
        """Remove access count tracking."""
        self._access_counts.pop(key, None)
    
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "LFU"


class FIFOEvictionStrategy(AEvictionStrategy):
    """First In, First Out eviction strategy."""
    
    def select_victim(self, cache_items: list[tuple[Hashable, Any, dict]]) -> Optional[Hashable]:
        """Select oldest inserted item."""
        if not cache_items:
            return None
        
        # Find item with oldest creation time
        fifo_item = min(cache_items, key=lambda x: x[2].get('created_at', 0))
        return fifo_item[0]
    
    def on_access(self, key: Hashable, metadata: dict) -> None:
        """No action on access for FIFO."""
        pass
    
    def on_insert(self, key: Hashable, value: Any, metadata: dict) -> None:
        """Set creation time."""
        metadata['created_at'] = time.time()
    
    def on_delete(self, key: Hashable) -> None:
        """No action needed on delete."""
        pass
    
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "FIFO"


class RandomEvictionStrategy(AEvictionStrategy):
    """Random eviction strategy."""
    
    def select_victim(self, cache_items: list[tuple[Hashable, Any, dict]]) -> Optional[Hashable]:
        """Select random item to evict."""
        if not cache_items:
            return None
        
        random_item = random.choice(cache_items)
        return random_item[0]
    
    def on_access(self, key: Hashable, metadata: dict) -> None:
        """No action on access for random."""
        pass
    
    def on_insert(self, key: Hashable, value: Any, metadata: dict) -> None:
        """No action on insert for random."""
        pass
    
    def on_delete(self, key: Hashable) -> None:
        """No action on delete for random."""
        pass
    
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "RANDOM"


class SizeBasedEvictionStrategy(AEvictionStrategy):
    """Evict largest items first to free maximum memory."""
    
    def select_victim(self, cache_items: list[tuple[Hashable, Any, dict]]) -> Optional[Hashable]:
        """Select largest item to evict."""
        if not cache_items:
            return None
        
        # Find item with largest size
        largest_item = max(cache_items, key=lambda x: x[2].get('size_bytes', 0))
        return largest_item[0]
    
    def on_access(self, key: Hashable, metadata: dict) -> None:
        """No action on access."""
        pass
    
    def on_insert(self, key: Hashable, value: Any, metadata: dict) -> None:
        """Track value size."""
        from .utils import estimate_object_size
        metadata['size_bytes'] = estimate_object_size(value)
    
    def on_delete(self, key: Hashable) -> None:
        """No action on delete."""
        pass
    
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "SIZE_BASED"


class TTLEvictionStrategy(AEvictionStrategy):
    """Evict items closest to expiration first."""
    
    def select_victim(self, cache_items: list[tuple[Hashable, Any, dict]]) -> Optional[Hashable]:
        """Select item closest to expiration."""
        if not cache_items:
            return None
        
        # Find item with earliest expiration
        expired_item = min(cache_items, key=lambda x: x[2].get('expires_at', float('inf')))
        return expired_item[0]
    
    def on_access(self, key: Hashable, metadata: dict) -> None:
        """No action on access for TTL."""
        pass
    
    def on_insert(self, key: Hashable, value: Any, metadata: dict) -> None:
        """Set expiration time."""
        ttl = metadata.get('ttl', 300)
        metadata['expires_at'] = time.time() + ttl
    
    def on_delete(self, key: Hashable) -> None:
        """No action on delete."""
        pass
    
    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "TTL"


__all__ = [
    'AEvictionStrategy',
    'LRUEvictionStrategy',
    'LFUEvictionStrategy',
    'FIFOEvictionStrategy',
    'RandomEvictionStrategy',
    'SizeBasedEvictionStrategy',
    'TTLEvictionStrategy',
]

