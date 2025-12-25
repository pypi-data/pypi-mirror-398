#!/usr/bin/env python3
#exonware/xwsystem/caching/lfu_optimized.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Optimized O(1) LFU Cache implementation.
Performance Priority #4 - Replaces O(n) eviction with O(1) frequency buckets.

Performance Improvement:
    - OLD: O(n) min() scan across all keys for eviction
    - NEW: O(1) using frequency buckets with min_freq tracking
    - Expected: 100x+ faster eviction for large caches
"""

import threading
import asyncio
from collections import defaultdict, OrderedDict
from typing import Any, Optional, Hashable
from .base import ACache
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.lfu_optimized")


class OptimizedLFUCache(ACache):
    """
    O(1) LFU Cache using frequency buckets.
    
    Algorithm:
        - Frequency buckets: dict[freq -> Ordereddict[key -> value]]
        - Min frequency tracking for O(1) eviction
        - All operations are O(1) complexity
    
    Features:
        - O(1) get, put, and eviction operations
        - Thread-safe with RLock
        - Statistics tracking
        - Memory-efficient implementation
    
    Performance:
        - 100x+ faster eviction vs naive O(n) implementation
        - Constant time complexity regardless of cache size
        - Optimized for high-throughput scenarios
    """
    
    def __init__(self, capacity: int = 128, name: Optional[str] = None):
        """
        Initialize optimized LFU cache.
        
        Args:
            capacity: Maximum number of items to store
            name: Optional name for debugging
        """
        if capacity <= 0:
            raise ValueError(
                f"Cache capacity must be positive, got {capacity}. "
                f"Example: OptimizedLFUCache(capacity=128)"
            )
        
        super().__init__(capacity=capacity, ttl=None)
        
        self.name = name or f"OptimizedLFUCache-{id(self)}"
        
        # Core data structures
        self._cache: dict[Hashable, Any] = {}
        self._key_to_freq: dict[Hashable, int] = {}
        self._freq_to_keys: dict[int, OrderedDict] = defaultdict(OrderedDict)
        self._min_freq = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.debug(f"Optimized LFU cache {self.name} initialized with capacity {capacity}")
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """
        Get value by key with O(1) complexity.
        
        Args:
            key: Key to lookup
            default: Default value if key not found
            
        Returns:
            Value associated with key, or default
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                logger.debug(f"Cache {self.name} miss for key: {key}")
                return default
            
            # Update frequency (O(1))
            self._update_frequency(key)
            
            self._hits += 1
            logger.debug(f"Cache {self.name} hit for key: {key}")
            return self._cache[key]
    
    def put(self, key: Hashable, value: Any) -> None:
        """
        Put key-value pair with O(1) complexity.
        
        Args:
            key: Key to store
            value: Value to store
        """
        with self._lock:
            if key in self._cache:
                # Update existing key
                self._cache[key] = value
                self._update_frequency(key)
                logger.debug(f"Cache {self.name} updated key: {key}")
            else:
                # Add new key
                if len(self._cache) >= self.capacity:
                    # O(1) eviction using min frequency bucket
                    self._evict_lfu()
                
                # Insert with frequency 1
                self._cache[key] = value
                self._key_to_freq[key] = 1
                self._freq_to_keys[1][key] = None
                self._min_freq = 1
                
                logger.debug(f"Cache {self.name} added key: {key}")
    
    def delete(self, key: Hashable) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key not in self._cache:
                return False
            
            # Remove from all structures
            freq = self._key_to_freq[key]
            del self._cache[key]
            del self._key_to_freq[key]
            del self._freq_to_keys[freq][key]
            
            # Clean up empty frequency bucket
            if not self._freq_to_keys[freq]:
                del self._freq_to_keys[freq]
            
            logger.debug(f"Cache {self.name} deleted key: {key}")
            return True
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
            self._key_to_freq.clear()
            self._freq_to_keys.clear()
            self._min_freq = 0
            logger.debug(f"Cache {self.name} cleared")
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def is_full(self) -> bool:
        """Check if cache is at capacity."""
        with self._lock:
            return len(self._cache) >= self.capacity
    
    def evict(self) -> None:
        """
        Manually evict least frequently used entry.
        
        This implements the abstract method from ACache.
        """
        with self._lock:
            if len(self._cache) > 0:
                self._evict_lfu()
    
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
                'type': 'OptimizedLFU',
                'capacity': self.capacity,
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'min_freq': self._min_freq,
                'num_freq_buckets': len(self._freq_to_keys),
            }
    
    def _update_frequency(self, key: Hashable) -> None:
        """
        Update key frequency (O(1) operation).
        
        Args:
            key: Key to update
        """
        old_freq = self._key_to_freq[key]
        new_freq = old_freq + 1
        
        # Remove from old frequency bucket
        del self._freq_to_keys[old_freq][key]
        
        # Update min_freq if necessary
        if not self._freq_to_keys[old_freq] and old_freq == self._min_freq:
            self._min_freq = new_freq
        
        # Add to new frequency bucket
        self._key_to_freq[key] = new_freq
        self._freq_to_keys[new_freq][key] = None
        
        # Clean up empty bucket
        if not self._freq_to_keys[old_freq]:
            del self._freq_to_keys[old_freq]
    
    def _evict_lfu(self) -> None:
        """
        Evict least frequently used item (O(1) operation).
        
        This is the critical performance improvement:
        - OLD: O(n) min() scan
        - NEW: O(1) using min_freq bucket
        """
        if self._min_freq not in self._freq_to_keys:
            # Shouldn't happen, but handle gracefully
            if self._freq_to_keys:
                self._min_freq = min(self._freq_to_keys.keys())
            else:
                return
        
        # Get LFU key from min frequency bucket (FIFO order)
        lfu_key, _ = self._freq_to_keys[self._min_freq].popitem(last=False)
        
        # Remove from all structures
        del self._cache[lfu_key]
        del self._key_to_freq[lfu_key]
        
        # Clean up empty bucket
        if not self._freq_to_keys[self._min_freq]:
            del self._freq_to_keys[self._min_freq]
        
        self._evictions += 1
        logger.debug(f"Cache {self.name} evicted LFU key: {lfu_key} (freq: {self._min_freq})")
    
    def get_many(self, keys: list[Hashable]) -> dict[Hashable, Any]:
        """
        Get multiple values in a single operation (optimized batch get).
        
        Args:
            keys: List of keys to retrieve
            
        Returns:
            Dictionary of key-value pairs found in cache
            
        Note:
            More efficient than individual gets - single lock acquisition.
            
        Root cause fixed: Added proper type hints for consistency with base class.
        """
        with self._lock:
            results = {}
            for key in keys:
                if key in self._cache:
                    self._update_frequency(key)
                    self._hits += 1
                    results[key] = self._cache[key]
                else:
                    self._misses += 1
            return results
    
    def put_many(self, items: dict[Hashable, Any]) -> int:
        """
        Put multiple key-value pairs in a single operation (optimized batch put).
        
        Args:
            items: Dictionary of key-value pairs to cache
            
        Returns:
            Number of items successfully cached
            
        Note:
            More efficient than individual puts - single lock acquisition.
            
        Root cause fixed: Added proper type hints for consistency with base class.
        """
        with self._lock:
            count = 0
            for key, value in items.items():
                try:
                    self.put(key, value)
                    count += 1
                except Exception:
                    # Continue with other items even if one fails
                    pass
            return count
    
    def delete_many(self, keys: list[Hashable]) -> int:
        """
        Delete multiple keys in a single operation (optimized batch delete).
        
        Args:
            keys: List of keys to delete
            
        Returns:
            Number of keys successfully deleted
            
        Note:
            More efficient than individual deletes - single lock acquisition.
            
        Root cause fixed: Added proper type hints for consistency with base class.
        """
        with self._lock:
            count = 0
            for key in keys:
                if self.delete(key):
                    count += 1
            return count
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False


class AsyncOptimizedLFUCache:
    """
    Async-compatible O(1) LFU Cache.
    
    Same algorithm as OptimizedLFUCache but with async lock.
    """
    
    def __init__(self, capacity: int = 128, name: Optional[str] = None):
        """Initialize async optimized LFU cache."""
        if capacity <= 0:
            raise ValueError(
                f"Cache capacity must be positive, got {capacity}. "
                f"Example: AsyncOptimizedLFUCache(capacity=128)"
            )
        
        self.capacity = capacity
        self.name = name or f"AsyncOptimizedLFUCache-{id(self)}"
        
        # Core data structures
        self._cache: dict[Hashable, Any] = {}
        self._key_to_freq: dict[Hashable, int] = {}
        self._freq_to_keys: dict[int, OrderedDict] = defaultdict(OrderedDict)
        self._min_freq = 0
        
        # Async safety
        self._lock = asyncio.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    async def get(self, key: Hashable, default: Any = None) -> Any:
        """Get value by key asynchronously with O(1) complexity."""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            
            self._update_frequency(key)
            self._hits += 1
            return self._cache[key]
    
    async def put(self, key: Hashable, value: Any) -> None:
        """Put key-value pair asynchronously with O(1) complexity."""
        async with self._lock:
            if key in self._cache:
                self._cache[key] = value
                self._update_frequency(key)
            else:
                if len(self._cache) >= self.capacity:
                    self._evict_lfu()
                
                self._cache[key] = value
                self._key_to_freq[key] = 1
                self._freq_to_keys[1][key] = None
                self._min_freq = 1
    
    async def delete(self, key: Hashable) -> bool:
        """Delete key from cache asynchronously."""
        async with self._lock:
            if key not in self._cache:
                return False
            
            freq = self._key_to_freq[key]
            del self._cache[key]
            del self._key_to_freq[key]
            del self._freq_to_keys[freq][key]
            
            if not self._freq_to_keys[freq]:
                del self._freq_to_keys[freq]
            
            return True
    
    async def clear(self) -> None:
        """Clear all items from cache asynchronously."""
        async with self._lock:
            self._cache.clear()
            self._key_to_freq.clear()
            self._freq_to_keys.clear()
            self._min_freq = 0
    
    async def size(self) -> int:
        """Get current cache size asynchronously."""
        return len(self._cache)
    
    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics asynchronously."""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'name': self.name,
                'type': 'AsyncOptimizedLFU',
                'capacity': self.capacity,
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'min_freq': self._min_freq,
                'num_freq_buckets': len(self._freq_to_keys),
            }
    
    def _update_frequency(self, key: Hashable) -> None:
        """Update key frequency (O(1) operation)."""
        old_freq = self._key_to_freq[key]
        new_freq = old_freq + 1
        
        del self._freq_to_keys[old_freq][key]
        
        if not self._freq_to_keys[old_freq] and old_freq == self._min_freq:
            self._min_freq = new_freq
        
        self._key_to_freq[key] = new_freq
        self._freq_to_keys[new_freq][key] = None
        
        if not self._freq_to_keys[old_freq]:
            del self._freq_to_keys[old_freq]
    
    def _evict_lfu(self) -> None:
        """Evict least frequently used item (O(1) operation)."""
        if self._min_freq not in self._freq_to_keys:
            if self._freq_to_keys:
                self._min_freq = min(self._freq_to_keys.keys())
            else:
                return
        
        lfu_key, _ = self._freq_to_keys[self._min_freq].popitem(last=False)
        
        del self._cache[lfu_key]
        del self._key_to_freq[lfu_key]
        
        if not self._freq_to_keys[self._min_freq]:
            del self._freq_to_keys[self._min_freq]
        
        self._evictions += 1
    
    async def keys(self) -> list[Hashable]:
        """
        Get list of all keys asynchronously.
        
        Root cause fixed: Added proper async implementation with async lock.
        """
        async with self._lock:
            return list(self._cache.keys())
    
    async def values(self) -> list[Any]:
        """
        Get list of all values asynchronously.
        
        Root cause fixed: Added proper async implementation with async lock.
        """
        async with self._lock:
            return list(self._cache.values())
    
    async def items(self) -> list[tuple[Hashable, Any]]:
        """
        Get list of all key-value pairs asynchronously.
        
        Root cause fixed: Added proper async implementation with async lock.
        """
        async with self._lock:
            return list(self._cache.items())
    
    async def is_full(self) -> bool:
        """Check if cache is at capacity asynchronously."""
        async with self._lock:
            return len(self._cache) >= self.capacity
    
    async def evict(self) -> None:
        """Manually evict least frequently used entry asynchronously."""
        async with self._lock:
            if len(self._cache) > 0:
                self._evict_lfu()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return False


__all__ = [
    'OptimizedLFUCache',
    'AsyncOptimizedLFUCache',
]

