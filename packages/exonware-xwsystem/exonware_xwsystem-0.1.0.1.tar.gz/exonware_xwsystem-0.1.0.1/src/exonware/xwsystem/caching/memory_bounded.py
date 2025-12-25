#!/usr/bin/env python3
#exonware/xwsystem/caching/memory_bounded.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Memory-bounded cache implementations.
Performance Priority #4 - Memory budget enforcement for controlled memory usage.
"""

from typing import Any, Optional, Hashable
from .lru_cache import LRUCache
from .lfu_optimized import OptimizedLFUCache
from .utils import estimate_object_size, format_bytes
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.memory_bounded")


class MemoryBoundedLRUCache(LRUCache):
    """
    LRU Cache with memory budget enforcement.
    
    Evicts entries based on memory usage instead of entry count.
    Useful for caching variable-size objects.
    
    Features:
        - Memory budget in megabytes
        - Automatic eviction when budget exceeded
        - Memory usage tracking per entry
        - Statistics include memory metrics
    """
    
    def __init__(
        self,
        capacity: int = 128,
        memory_budget_mb: float = 100.0,
        ttl: Optional[float] = None,
        name: Optional[str] = None
    ):
        """
        Initialize memory-bounded LRU cache.
        
        Args:
            capacity: Maximum number of entries (fallback limit)
            memory_budget_mb: Memory budget in megabytes
            ttl: Optional TTL in seconds
            name: Cache name for debugging
        """
        super().__init__(capacity, ttl, name)
        
        self.memory_budget_mb = memory_budget_mb
        self.memory_budget_bytes = int(memory_budget_mb * 1024 * 1024)
        self._current_memory_bytes = 0
        self._value_sizes: dict[Hashable, int] = {}
        
        logger.info(
            f"Memory-bounded LRU cache {self.name} initialized: "
            f"capacity={capacity}, memory_budget={memory_budget_mb}MB"
        )
    
    def put(self, key: Hashable, value: Any) -> None:
        """
        Put value with memory budget enforcement.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            value_size = estimate_object_size(value)
            
            # If single value exceeds budget, reject it
            if value_size > self.memory_budget_bytes:
                logger.warning(
                    f"Value for key {key} exceeds memory budget: "
                    f"{format_bytes(value_size)} > {self.memory_budget_mb}MB"
                )
                return
            
            # If key exists, update memory accounting
            if key in self._cache:
                old_size = self._value_sizes.get(key, 0)
                self._current_memory_bytes -= old_size
            
            # Evict LRU entries until we have enough memory
            while (self._current_memory_bytes + value_size > self.memory_budget_bytes
                   and len(self._cache) > 0):
                self._evict_lru_with_memory()
            
            # Store value using parent method
            super().put(key, value)
            
            # Update memory tracking
            self._value_sizes[key] = value_size
            self._current_memory_bytes += value_size
            
            logger.debug(
                f"Cache {self.name} stored key {key}: "
                f"{format_bytes(value_size)} "
                f"(total: {format_bytes(self._current_memory_bytes)})"
            )
    
    def delete(self, key: Hashable) -> bool:
        """Delete key and update memory tracking."""
        with self._lock:
            if key in self._cache:
                # Update memory tracking
                value_size = self._value_sizes.get(key, 0)
                self._current_memory_bytes -= value_size
                del self._value_sizes[key]
                
                # Delete using parent method
                return super().delete(key)
            return False
    
    def clear(self) -> None:
        """Clear cache and reset memory tracking."""
        with self._lock:
            super().clear()
            self._value_sizes.clear()
            self._current_memory_bytes = 0
    
    def _evict_lru_with_memory(self) -> None:
        """Evict LRU entry and update memory tracking."""
        if not self._cache:
            return
        
        # Get LRU node
        lru_node = self._tail.prev
        if lru_node == self._head:
            return
        
        lru_key = lru_node.key
        
        # Update memory tracking
        value_size = self._value_sizes.get(lru_key, 0)
        self._current_memory_bytes -= value_size
        if lru_key in self._value_sizes:
            del self._value_sizes[lru_key]
        
        # Evict node
        self._remove_node(lru_node)
        del self._cache[lru_key]
        self._evictions += 1
        
        logger.debug(
            f"Cache {self.name} evicted LRU key {lru_key}: "
            f"freed {format_bytes(value_size)}"
        )
    
    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory-specific statistics."""
        with self._lock:
            return {
                'memory_budget_mb': self.memory_budget_mb,
                'memory_budget_bytes': self.memory_budget_bytes,
                'current_memory_bytes': self._current_memory_bytes,
                'memory_used_pct': (
                    self._current_memory_bytes / self.memory_budget_bytes * 100
                    if self.memory_budget_bytes > 0 else 0
                ),
                'avg_value_size_bytes': (
                    self._current_memory_bytes / len(self._cache)
                    if len(self._cache) > 0 else 0
                ),
            }
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics including memory metrics."""
        stats = super().get_stats()
        stats.update(self.get_memory_stats())
        return stats


class MemoryBoundedLFUCache(OptimizedLFUCache):
    """
    Optimized O(1) LFU Cache with memory budget enforcement.
    
    Combines frequency-based eviction with memory limits.
    """
    
    def __init__(
        self,
        capacity: int = 128,
        memory_budget_mb: float = 100.0,
        name: Optional[str] = None
    ):
        """Initialize memory-bounded LFU cache."""
        super().__init__(capacity, name)
        
        self.memory_budget_mb = memory_budget_mb
        self.memory_budget_bytes = int(memory_budget_mb * 1024 * 1024)
        self._current_memory_bytes = 0
        self._value_sizes: dict[Hashable, int] = {}
    
    def put(self, key: Hashable, value: Any) -> None:
        """Put value with memory budget enforcement."""
        with self._lock:
            value_size = estimate_object_size(value)
            
            if value_size > self.memory_budget_bytes:
                logger.warning(
                    f"Value for key {key} exceeds memory budget: "
                    f"{format_bytes(value_size)} > {self.memory_budget_mb}MB"
                )
                return
            
            # Update memory for existing key
            if key in self._cache:
                old_size = self._value_sizes.get(key, 0)
                self._current_memory_bytes -= old_size
            
            # Evict until we have space
            while (self._current_memory_bytes + value_size > self.memory_budget_bytes
                   and len(self._cache) > 0):
                self._evict_lfu_with_memory()
            
            # Store using parent
            super().put(key, value)
            
            # Update memory tracking
            self._value_sizes[key] = value_size
            self._current_memory_bytes += value_size
    
    def delete(self, key: Hashable) -> bool:
        """Delete key and update memory tracking."""
        with self._lock:
            if key in self._cache:
                value_size = self._value_sizes.get(key, 0)
                self._current_memory_bytes -= value_size
                del self._value_sizes[key]
                return super().delete(key)
            return False
    
    def clear(self) -> None:
        """Clear cache and reset memory tracking."""
        with self._lock:
            super().clear()
            self._value_sizes.clear()
            self._current_memory_bytes = 0
    
    def _evict_lfu_with_memory(self) -> None:
        """Evict LFU entry and update memory tracking."""
        if self._min_freq not in self._freq_to_keys:
            if self._freq_to_keys:
                self._min_freq = min(self._freq_to_keys.keys())
            else:
                return
        
        lfu_key, _ = self._freq_to_keys[self._min_freq].popitem(last=False)
        
        # Update memory tracking
        value_size = self._value_sizes.get(lfu_key, 0)
        self._current_memory_bytes -= value_size
        if lfu_key in self._value_sizes:
            del self._value_sizes[lfu_key]
        
        # Evict
        del self._cache[lfu_key]
        del self._key_to_freq[lfu_key]
        
        if not self._freq_to_keys[self._min_freq]:
            del self._freq_to_keys[self._min_freq]
        
        self._evictions += 1
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics including memory metrics."""
        stats = super().get_stats()
        stats.update({
            'memory_budget_mb': self.memory_budget_mb,
            'current_memory_bytes': self._current_memory_bytes,
            'memory_used_pct': (
                self._current_memory_bytes / self.memory_budget_bytes * 100
                if self.memory_budget_bytes > 0 else 0
            ),
        })
        return stats


__all__ = [
    'MemoryBoundedLRUCache',
    'MemoryBoundedLFUCache',
]

