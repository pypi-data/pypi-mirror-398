"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

LRU (Least Recently Used) Cache implementation with thread-safety and async support.
"""

import asyncio
import threading
import time
from collections import OrderedDict
from typing import Any, Optional, Union, Callable, Hashable

from ..config.logging_setup import get_logger
from .base import ACache

logger = get_logger("xwsystem.caching.lru_cache")


class CacheNode:
    """Node for doubly-linked list in LRU cache."""
    
    def __init__(self, key: Hashable, value: Any):
        self.key = key
        self.value = value
        self.prev: Optional['CacheNode'] = None
        self.next: Optional['CacheNode'] = None
        self.access_time = time.time()


class LRUCache(ACache):
    """
    Thread-safe LRU (Least Recently Used) Cache.
    
    Features:
    - O(1) get and put operations
    - Thread-safe operations
    - Optional TTL support
    - Statistics tracking
    - Memory-efficient implementation
    
    API Note:
        This class provides both put() and set() methods:
        - put(key, value) - Preferred method (ACache interface)
        - set(key, value, ttl) - Alternative method (Protocol interface)
        Both work identically; use put() for consistency with codebase.
    """
    
    def __init__(self, capacity: int = 128, ttl: Optional[float] = None, name: Optional[str] = None):
        """
        Initialize LRU cache.
        
        Args:
            capacity: Maximum number of items to store
            ttl: Optional time-to-live in seconds
            name: Optional name for debugging
        """
        if capacity <= 0:
            raise ValueError(
                f"Cache capacity must be positive, got {capacity}. "
                f"Example: LRUCache(capacity=128)"
            )
        
        # Call parent constructor
        super().__init__(capacity=capacity, ttl=int(ttl) if ttl else None)
        
        self.name = name or f"LRUCache-{id(self)}"
        
        # Cache storage
        self._cache: dict[Hashable, CacheNode] = {}
        self._lock = threading.RLock()
        
        # Doubly-linked list for LRU ordering
        self._head = CacheNode(None, None)  # Dummy head
        self._tail = CacheNode(None, None)  # Dummy tail
        self._head.next = self._tail
        self._tail.prev = self._head
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.debug(f"LRU cache {self.name} initialized with capacity {capacity}")
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """
        Get value by key.
        
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
            
            node = self._cache[key]
            
            # Check TTL if enabled
            if self.ttl and time.time() - node.access_time > self.ttl:
                self._remove_node(node)
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache {self.name} TTL expired for key: {key}")
                return default
            
            # Move to head (most recently used)
            self._move_to_head(node)
            node.access_time = time.time()
            
            self._hits += 1
            logger.debug(f"Cache {self.name} hit for key: {key}")
            
            # Handle None values: if value is None, treat as "not found" and return default
            # This allows None to be a sentinel for "not cached" while still allowing
            # explicit None storage via put() (design decision for cache semantics)
            if node.value is None:
                return default
            
            return node.value
    
    def put(self, key: Hashable, value: Any) -> None:
        """
        Put key-value pair in cache.
        
        Args:
            key: Key to store
            value: Value to store
        """
        with self._lock:
            if key in self._cache:
                # Update existing key
                node = self._cache[key]
                node.value = value
                node.access_time = time.time()
                self._move_to_head(node)
                logger.debug(f"Cache {self.name} updated key: {key}")
            else:
                # Add new key
                node = CacheNode(key, value)
                
                if len(self._cache) >= self.capacity:
                    # Remove least recently used item
                    lru_node = self._tail.prev
                    self._remove_node(lru_node)
                    del self._cache[lru_node.key]
                    self._evictions += 1
                    logger.debug(f"Cache {self.name} evicted LRU key: {lru_node.key}")
                
                self._cache[key] = node
                self._add_to_head(node)
                logger.debug(f"Cache {self.name} added key: {key}")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache (Protocol interface method).
        
        Note: This method exists for Protocol compatibility (Cacheable interface).
        Internally delegates to put(). Prefer using put() for consistency.
        
        Args:
            key: Key to store
            value: Value to store
            ttl: Optional time-to-live (not used in LRU, available for subclasses)
        """
        self.put(key, value)
    
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
            
            node = self._cache[key]
            self._remove_node(node)
            del self._cache[key]
            logger.debug(f"Cache {self.name} deleted key: {key}")
            return True
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
            self._head.next = self._tail
            self._tail.prev = self._head
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
        Evict least recently used entry from cache.
        Implementation of abstract method from ACacheBase.
        """
        with self._lock:
            if len(self._cache) > 0:
                lru_node = self._tail.prev
                if lru_node != self._head:  # Ensure it's not the dummy head
                    self._remove_node(lru_node)
                    del self._cache[lru_node.key]
                    self._evictions += 1
                    logger.debug(f"Cache {self.name} manually evicted LRU key: {lru_node.key}")
    
    def keys(self) -> list:
        """Get list of all keys (in LRU order)."""
        with self._lock:
            keys = []
            node = self._head.next
            while node != self._tail:
                keys.append(node.key)
                node = node.next
            return keys
    
    def values(self) -> list:
        """Get list of all values (in LRU order)."""
        with self._lock:
            values = []
            node = self._head.next
            while node != self._tail:
                values.append(node.value)
                node = node.next
            return values
    
    def items(self) -> list:
        """Get list of all key-value pairs (in LRU order)."""
        with self._lock:
            items = []
            node = self._head.next
            while node != self._tail:
                items.append((node.key, node.value))
                node = node.next
            return items
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'name': self.name,
                'type': 'LRU',
                'capacity': self.capacity,
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'ttl': self.ttl,
            }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def _add_to_head(self, node: CacheNode) -> None:
        """Add node to head of list."""
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node
    
    def _remove_node(self, node: CacheNode) -> None:
        """Remove node from list."""
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _move_to_head(self, node: CacheNode) -> None:
        """Move node to head of list."""
        self._remove_node(node)
        self._add_to_head(node)
    
    def __contains__(self, key: Hashable) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            return key in self._cache
    
    def __len__(self) -> int:
        """Get cache size."""
        return self.size()
    
    def __getitem__(self, key: Hashable) -> Any:
        """Get item by key (raises KeyError if not found)."""
        result = self.get(key, None)
        if result is None and key not in self._cache:
            raise KeyError(key)
        return result
    
    def __setitem__(self, key: Hashable, value: Any) -> None:
        """Set item by key."""
        self.put(key, value)
    
    def __delitem__(self, key: Hashable) -> None:
        """Delete item by key."""
        if not self.delete(key):
            raise KeyError(key)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        # Optionally clear cache on exit (configurable behavior)
        # For now, we don't auto-clear to preserve data
        # Users can manually call clear() if needed
        return False


class AsyncLRUCache:
    """
    Async-safe LRU (Least Recently Used) Cache.
    
    Features:
    - O(1) async get and put operations
    - Async-safe operations with asyncio locks
    - Optional TTL support
    - Statistics tracking
    - Memory-efficient implementation
    """
    
    def __init__(self, capacity: int = 128, ttl: Optional[float] = None, name: Optional[str] = None):
        """
        Initialize async LRU cache.
        
        Args:
            capacity: Maximum number of items to store
            ttl: Optional time-to-live in seconds
            name: Optional name for debugging
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self.capacity = capacity
        self.ttl = ttl
        self.name = name or f"AsyncLRUCache-{id(self)}"
        
        # Cache storage
        self._cache: dict[Hashable, CacheNode] = {}
        self._lock = asyncio.Lock()
        
        # Doubly-linked list for LRU ordering
        self._head = CacheNode(None, None)  # Dummy head
        self._tail = CacheNode(None, None)  # Dummy tail
        self._head.next = self._tail
        self._tail.prev = self._head
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.debug(f"Async LRU cache {self.name} initialized with capacity {capacity}")
    
    async def get(self, key: Hashable, default: Any = None) -> Any:
        """
        Get value by key asynchronously.
        
        Args:
            key: Key to lookup
            default: Default value if key not found
            
        Returns:
            Value associated with key, or default
        """
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                logger.debug(f"Async cache {self.name} miss for key: {key}")
                return default
            
            node = self._cache[key]
            
            # Check TTL if enabled
            if self.ttl and time.time() - node.access_time > self.ttl:
                self._remove_node(node)
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Async cache {self.name} TTL expired for key: {key}")
                return default
            
            # Move to head (most recently used)
            self._move_to_head(node)
            node.access_time = time.time()
            
            self._hits += 1
            logger.debug(f"Async cache {self.name} hit for key: {key}")
            return node.value
    
    async def put(self, key: Hashable, value: Any) -> None:
        """
        Put key-value pair in cache asynchronously.
        
        Args:
            key: Key to store
            value: Value to store
        """
        async with self._lock:
            if key in self._cache:
                # Update existing key
                node = self._cache[key]
                node.value = value
                node.access_time = time.time()
                self._move_to_head(node)
                logger.debug(f"Async cache {self.name} updated key: {key}")
            else:
                # Add new key
                node = CacheNode(key, value)
                
                if len(self._cache) >= self.capacity:
                    # Remove least recently used item
                    lru_node = self._tail.prev
                    self._remove_node(lru_node)
                    del self._cache[lru_node.key]
                    self._evictions += 1
                    logger.debug(f"Async cache {self.name} evicted LRU key: {lru_node.key}")
                
                self._cache[key] = node
                self._add_to_head(node)
                logger.debug(f"Async cache {self.name} added key: {key}")
    
    async def delete(self, key: Hashable) -> bool:
        """
        Delete key from cache asynchronously.
        
        Args:
            key: Key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key not in self._cache:
                return False
            
            node = self._cache[key]
            self._remove_node(node)
            del self._cache[key]
            logger.debug(f"Async cache {self.name} deleted key: {key}")
            return True
    
    async def clear(self) -> None:
        """Clear all items from cache asynchronously."""
        async with self._lock:
            self._cache.clear()
            self._head.next = self._tail
            self._tail.prev = self._head
            logger.debug(f"Async cache {self.name} cleared")
    
    async def size(self) -> int:
        """Get current cache size asynchronously."""
        async with self._lock:
            return len(self._cache)
    
    async def is_full(self) -> bool:
        """Check if cache is at capacity asynchronously."""
        async with self._lock:
            return len(self._cache) >= self.capacity
    
    async def keys(self) -> list:
        """Get list of all keys (in LRU order) asynchronously."""
        async with self._lock:
            keys = []
            node = self._head.next
            while node != self._tail:
                keys.append(node.key)
                node = node.next
            return keys
    
    async def values(self) -> list:
        """Get list of all values (in LRU order) asynchronously."""
        async with self._lock:
            values = []
            node = self._head.next
            while node != self._tail:
                values.append(node.value)
                node = node.next
            return values
    
    async def items(self) -> list:
        """Get list of all key-value pairs (in LRU order) asynchronously."""
        async with self._lock:
            items = []
            node = self._head.next
            while node != self._tail:
                items.append((node.key, node.value))
                node = node.next
            return items
    
    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics asynchronously."""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'name': self.name,
                'type': 'AsyncLRU',
                'capacity': self.capacity,
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'ttl': self.ttl,
            }
    
    async def reset_stats(self) -> None:
        """Reset cache statistics asynchronously."""
        async with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def _add_to_head(self, node: CacheNode) -> None:
        """Add node to head of list."""
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node
    
    def _remove_node(self, node: CacheNode) -> None:
        """Remove node from list."""
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _move_to_head(self, node: CacheNode) -> None:
        """Move node to head of list."""
        self._remove_node(node)
        self._add_to_head(node)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return False
    
    async def __aiter__(self):
        """
        Async iteration over keys.
        
        Example:
            async for key in cache:
                value = await cache.get(key)
                print(f"{key}: {value}")
        """
        async with self._lock:
            keys = list(self._cache.keys())
        
        for key in keys:
            yield key
    
    async def items_async(self):
        """
        Async iteration over items.
        
        Yields:
            Tuples of (key, value)
            
        Example:
            async for key, value in cache.items_async():
                print(f"{key}: {value}")
        """
        async with self._lock:
            items_list = []
            node = self._head.next
            while node != self._tail:
                items_list.append((node.key, node.value))
                node = node.next
        
        for item in items_list:
            yield item