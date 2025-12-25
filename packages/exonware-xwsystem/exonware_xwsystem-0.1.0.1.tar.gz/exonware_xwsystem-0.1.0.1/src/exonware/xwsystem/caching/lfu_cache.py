"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

LFU (Least Frequently Used) Cache implementation with thread-safety and async support.
"""

import asyncio
import threading
import time
from typing import Any, Optional, Hashable

from ..config.logging_setup import get_logger
from .base import ACache

logger = get_logger("xwsystem.caching.lfu_cache")


class LFUCache(ACache):
    """
    Thread-safe LFU (Least Frequently Used) Cache.
    
    ⚠️ PERFORMANCE WARNING: This implementation uses O(n) eviction.
    For better performance, use OptimizedLFUCache with O(1) eviction (100x+ faster).
    
    Features:
    - O(1) get and put operations
    - O(n) eviction (uses min() scan - slow for large caches)
    - Thread-safe operations
    - Frequency-based eviction
    - Statistics tracking
    
    Recommended Alternative:
        from exonware.xwsystem.caching import OptimizedLFUCache
        cache = OptimizedLFUCache(capacity=1000)  # O(1) eviction
    """
    
    def __init__(self, capacity: int = 128, name: Optional[str] = None):
        """
        Initialize LFU cache.
        
        ⚠️ PERFORMANCE WARNING: Consider using OptimizedLFUCache for better performance.
        This implementation has O(n) eviction complexity.
        """
        if capacity <= 0:
            raise ValueError(
                f"Cache capacity must be positive, got {capacity}. "
                f"Example: LFUCache(capacity=128)"
            )
        
        # Call parent constructor
        super().__init__(capacity=capacity, ttl=None)
        
        self.name = name or f"LFUCache-{id(self)}"
        
        self._cache: dict[Hashable, Any] = {}
        self._frequencies: dict[Hashable, int] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.debug(f"LFU cache {self.name} initialized with capacity {capacity}")
        
        # Emit performance warning for large caches
        if capacity > 1000:
            logger.warning(
                f"LFUCache with capacity {capacity} uses O(n) eviction. "
                f"Consider using OptimizedLFUCache for O(1) eviction (100x+ faster)."
            )
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """Get value by key."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            
            # Increment frequency
            self._frequencies[key] += 1
            self._hits += 1
            return self._cache[key]
    
    def put(self, key: Hashable, value: Any) -> None:
        """Put key-value pair in cache."""
        with self._lock:
            if key in self._cache:
                self._cache[key] = value
                self._frequencies[key] += 1
            else:
                if len(self._cache) >= self.capacity:
                    # Find least frequently used key
                    lfu_key = min(self._frequencies, key=self._frequencies.get)
                    del self._cache[lfu_key]
                    del self._frequencies[lfu_key]
                    self._evictions += 1
                
                self._cache[key] = value
                self._frequencies[key] = 1
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache (abstract method implementation).
        Delegates to put() for backward compatibility.
        
        Args:
            key: Key to store
            value: Value to store
            ttl: Optional time-to-live (not used in LFU)
        """
        self.put(key, value)
    
    def delete(self, key: Hashable) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._frequencies[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
            self._frequencies.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def is_full(self) -> bool:
        """Check if cache is at capacity."""
        with self._lock:
            return len(self._cache) >= self.capacity
    
    def evict(self) -> None:
        """
        Evict least frequently used entry from cache.
        Implementation of abstract method from ACacheBase.
        """
        with self._lock:
            if len(self._cache) > 0:
                # Find least frequently used key
                lfu_key = min(self._frequencies, key=self._frequencies.get)
                del self._cache[lfu_key]
                del self._frequencies[lfu_key]
                self._evictions += 1
                logger.debug(f"Cache {self.name} manually evicted LFU key: {lfu_key}")
    
    def keys(self) -> list[Hashable]:
        """Get list of all cache keys."""
        with self._lock:
            return list(self._cache.keys())
    
    def values(self) -> list[Any]:
        """Get list of all cache values."""
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
                'type': 'LFU',
                'capacity': self.capacity,
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
            }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        return False


class AsyncLFUCache:
    """
    Async-safe LFU (Least Frequently Used) Cache.
    """
    
    def __init__(self, capacity: int = 128, name: Optional[str] = None):
        """Initialize async LFU cache."""
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self.capacity = capacity
        self.name = name or f"AsyncLFUCache-{id(self)}"
        
        self._cache: dict[Hashable, Any] = {}
        self._frequencies: dict[Hashable, int] = {}
        self._lock = asyncio.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    async def get(self, key: Hashable, default: Any = None) -> Any:
        """Get value by key asynchronously."""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            
            self._frequencies[key] += 1
            self._hits += 1
            return self._cache[key]
    
    async def put(self, key: Hashable, value: Any) -> None:
        """Put key-value pair in cache asynchronously."""
        async with self._lock:
            if key in self._cache:
                self._cache[key] = value
                self._frequencies[key] += 1
            else:
                if len(self._cache) >= self.capacity:
                    lfu_key = min(self._frequencies, key=self._frequencies.get)
                    del self._cache[lfu_key]
                    del self._frequencies[lfu_key]
                    self._evictions += 1
                
                self._cache[key] = value
                self._frequencies[key] = 1
    
    async def delete(self, key: Hashable) -> bool:
        """Delete key from cache asynchronously."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._frequencies[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all items from cache asynchronously."""
        async with self._lock:
            self._cache.clear()
            self._frequencies.clear()
    
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
                'type': 'AsyncLFU',
                'capacity': self.capacity,
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
            }
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return False
