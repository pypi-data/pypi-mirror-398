#!/usr/bin/env python3
#exonware/xwsystem/caching/pluggable_cache.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Pluggable cache with runtime-switchable eviction strategies.
Extensibility Priority #5 - Maximum flexibility for custom behaviors.
"""

import threading
from typing import Any, Optional, Hashable
from .base import ACache
from .eviction_strategies import AEvictionStrategy, LRUEvictionStrategy
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.pluggable")


class PluggableCache(ACache):
    """
    Cache with pluggable eviction strategy.
    
    Allows runtime switching of eviction policies for maximum flexibility.
    
    Example:
        from .eviction_strategies import LRUEvictionStrategy, LFUEvictionStrategy
        
        cache = PluggableCache(capacity=100, strategy=LRUEvictionStrategy())
        
        # Later, switch strategy
        cache.set_strategy(LFUEvictionStrategy())
    """
    
    def __init__(
        self,
        capacity: int = 128,
        strategy: Optional[AEvictionStrategy] = None,
        name: Optional[str] = None
    ):
        """
        Initialize pluggable cache.
        
        Args:
            capacity: Maximum cache size
            strategy: Eviction strategy (default: LRU)
            name: Cache name for debugging
        """
        if capacity <= 0:
            raise ValueError(
                f"Cache capacity must be positive, got {capacity}. "
                f"Example: PluggableCache(capacity=128)"
            )
        
        super().__init__(capacity=capacity, ttl=None)
        
        self.name = name or f"PluggableCache-{id(self)}"
        self.strategy = strategy or LRUEvictionStrategy()
        
        # Storage
        self._cache: dict[Hashable, Any] = {}
        self._metadata: dict[Hashable, dict] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._strategy_switches = 0
        
        logger.debug(
            f"Pluggable cache {self.name} initialized with {self.strategy.get_strategy_name()} strategy"
        )
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """Get value and update strategy metadata."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            
            # Update strategy metadata
            self.strategy.on_access(key, self._metadata[key])
            
            self._hits += 1
            return self._cache[key]
    
    def put(self, key: Hashable, value: Any) -> None:
        """Put value using current strategy."""
        with self._lock:
            # Check if we need to evict
            if key not in self._cache and len(self._cache) >= self.capacity:
                self._evict_using_strategy()
            
            # Store value
            self._cache[key] = value
            
            # Initialize or update metadata
            if key not in self._metadata:
                self._metadata[key] = {}
                self.strategy.on_insert(key, value, self._metadata[key])
            else:
                self.strategy.on_access(key, self._metadata[key])
    
    def delete(self, key: Hashable) -> bool:
        """Delete key and update strategy."""
        with self._lock:
            if key not in self._cache:
                return False
            
            del self._cache[key]
            del self._metadata[key]
            self.strategy.on_delete(key)
            
            return True
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
            self._metadata.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def is_full(self) -> bool:
        """Check if cache is at capacity."""
        return len(self._cache) >= self.capacity
    
    def evict(self) -> None:
        """Manually evict one item using current strategy."""
        with self._lock:
            if len(self._cache) > 0:
                self._evict_using_strategy()
    
    def keys(self) -> list[Hashable]:
        """Get list of all keys."""
        with self._lock:
            return list(self._cache.keys())
    
    def values(self) -> list[Any]:
        """Get list of all values."""
        with self._lock:
            return list(self._cache.values())
    
    def items(self) -> list[tuple[Hashable, Any]]:
        """Get list of all key-value pairs."""
        with self._lock:
            return list(self._cache.items())
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'name': self.name,
                'type': 'Pluggable',
                'strategy': self.strategy.get_strategy_name(),
                'capacity': self.capacity,
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'strategy_switches': self._strategy_switches,
            }
    
    def set_strategy(self, strategy: AEvictionStrategy) -> None:
        """
        Change eviction strategy at runtime.
        
        Args:
            strategy: New eviction strategy
            
        Note:
            Metadata may need to be rebuilt for the new strategy.
        """
        with self._lock:
            old_strategy = self.strategy.get_strategy_name()
            self.strategy = strategy
            self._strategy_switches += 1
            
            # Rebuild metadata for new strategy
            for key, value in self._cache.items():
                self._metadata[key] = {}
                self.strategy.on_insert(key, value, self._metadata[key])
            
            logger.info(
                f"Cache {self.name} switched strategy: {old_strategy} -> {strategy.get_strategy_name()}"
            )
    
    def get_strategy(self) -> AEvictionStrategy:
        """Get current eviction strategy."""
        return self.strategy
    
    def _evict_using_strategy(self) -> None:
        """Evict one item using current strategy."""
        # Build cache items list with metadata
        cache_items = [
            (key, value, self._metadata.get(key, {}))
            for key, value in self._cache.items()
        ]
        
        # Select victim using strategy
        victim_key = self.strategy.select_victim(cache_items)
        
        if victim_key is not None:
            del self._cache[victim_key]
            del self._metadata[victim_key]
            self.strategy.on_delete(victim_key)
            self._evictions += 1
            
            logger.debug(f"Cache {self.name} evicted key {victim_key} using {self.strategy.get_strategy_name()}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False


__all__ = [
    'PluggableCache',
]

