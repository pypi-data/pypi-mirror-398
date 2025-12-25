#!/usr/bin/env python3
#exonware/xwsystem/caching/observable_cache.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Observable cache implementations with event emission.
Extensibility Priority #5 - Event-driven caching for custom behaviors.
"""

from typing import Any, Optional, Hashable
from .lru_cache import LRUCache
from .lfu_optimized import OptimizedLFUCache
from .events import CacheEventEmitter, CacheEvent


class ObservableLRUCache(CacheEventEmitter, LRUCache):
    """
    LRU Cache with event emission.
    
    Emits events for all cache operations: HIT, MISS, PUT, DELETE, EVICT.
    
    Example:
        cache = ObservableLRUCache(capacity=100)
        
        def on_hit(event, key, value):
            print(f"Cache hit for {key}")
        
        cache.on(CacheEvent.HIT, on_hit)
        
        cache.put("key", "value")
        value = cache.get("key")  # Triggers on_hit callback
    """
    
    def __init__(
        self,
        capacity: int = 128,
        ttl: Optional[float] = None,
        name: Optional[str] = None
    ):
        """
        Initialize observable LRU cache.
        
        Args:
            capacity: Maximum cache size
            ttl: Optional TTL in seconds
            name: Cache name for debugging
        """
        LRUCache.__init__(self, capacity, ttl, name)
        CacheEventEmitter.__init__(self)
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """Get value with event emission."""
        value = super().get(key, default)
        
        if value is not None and value != default:
            self._emit(CacheEvent.HIT, key=key, value=value)
        else:
            self._emit(CacheEvent.MISS, key=key)
        
        return value
    
    def put(self, key: Hashable, value: Any) -> None:
        """Put value with event emission."""
        super().put(key, value)
        self._emit(CacheEvent.PUT, key=key, value=value)
    
    def delete(self, key: Hashable) -> bool:
        """Delete key with event emission."""
        deleted = super().delete(key)
        if deleted:
            self._emit(CacheEvent.DELETE, key=key)
        return deleted
    
    def clear(self) -> None:
        """Clear cache with event emission."""
        super().clear()
        self._emit(CacheEvent.CLEAR)
    
    def evict(self) -> None:
        """Evict with event emission."""
        # Get LRU key before evicting
        if self._tail.prev != self._head:
            lru_key = self._tail.prev.key
            super().evict()
            self._emit(CacheEvent.EVICT, key=lru_key)
        else:
            super().evict()
    
    def get_stats(self) -> dict:
        """Get statistics including event stats."""
        stats = super().get_stats()
        stats['events'] = self.get_event_stats()
        return stats


class ObservableLFUCache(CacheEventEmitter, OptimizedLFUCache):
    """
    Optimized O(1) LFU Cache with event emission.
    
    Combines performance and extensibility.
    """
    
    def __init__(self, capacity: int = 128, name: Optional[str] = None):
        """Initialize observable LFU cache."""
        OptimizedLFUCache.__init__(self, capacity, name)
        CacheEventEmitter.__init__(self)
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """Get value with event emission."""
        value = super().get(key, default)
        
        if value is not None and value != default:
            self._emit(CacheEvent.HIT, key=key, value=value)
        else:
            self._emit(CacheEvent.MISS, key=key)
        
        return value
    
    def put(self, key: Hashable, value: Any) -> None:
        """Put value with event emission."""
        super().put(key, value)
        self._emit(CacheEvent.PUT, key=key, value=value)
    
    def delete(self, key: Hashable) -> bool:
        """Delete key with event emission."""
        deleted = super().delete(key)
        if deleted:
            self._emit(CacheEvent.DELETE, key=key)
        return deleted
    
    def clear(self) -> None:
        """Clear cache with event emission."""
        super().clear()
        self._emit(CacheEvent.CLEAR)
    
    def get_stats(self) -> dict:
        """Get statistics including event stats."""
        stats = super().get_stats()
        stats['events'] = self.get_event_stats()
        return stats


__all__ = [
    'ObservableLRUCache',
    'ObservableLFUCache',
]

