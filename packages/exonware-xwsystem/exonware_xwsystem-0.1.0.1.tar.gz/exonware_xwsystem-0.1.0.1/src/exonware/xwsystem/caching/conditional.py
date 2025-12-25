#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Conditional eviction policies for caching.
Extensibility Priority #5 - Customizable eviction behavior.
"""

import time
from typing import Any, Callable, Optional, Hashable
from .lru_cache import LRUCache, CacheNode
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.conditional")


class ConditionalEvictionCache(LRUCache):
    """
    LRU Cache with conditional eviction policies.
    
    Allows custom logic to determine which entries can be evicted.
    Useful for protecting important entries from eviction.
    
    Example:
        # Don't evict entries starting with 'protected:'
        def can_evict(key, value):
            return not str(key).startswith('protected:')
        
        cache = ConditionalEvictionCache(
            capacity=100,
            eviction_policy=can_evict
        )
        
        cache.put('protected:admin', admin_data)
        cache.put('temp:user', user_data)
        
        # When cache is full, only non-protected entries can be evicted
    """
    
    def __init__(
        self,
        capacity: int = 128,
        eviction_policy: Optional[Callable[[Any, Any], bool]] = None,
        ttl: Optional[float] = None,
        name: Optional[str] = None
    ):
        """
        Initialize conditional eviction cache.
        
        Args:
            capacity: Maximum cache size
            eviction_policy: Function (key, value) -> bool returning True if entry can be evicted
            ttl: Optional TTL in seconds
            name: Cache name
        """
        super().__init__(capacity, ttl, name)
        self.eviction_policy = eviction_policy or (lambda k, v: True)  # Default: evict all
        self._eviction_rejections = 0
    
    def put(self, key: Hashable, value: Any) -> None:
        """
        Put value with conditional eviction.
        
        Args:
            key: Cache key
            value: Value to cache
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
                    # Find evictable entry
                    evicted = self._evict_conditional()
                    if not evicted:
                        logger.warning(f"Cache full but no evictable entries found")
                        # Still add the new entry (exceeds capacity temporarily)
                
                self._cache[key] = node
                self._add_to_head(node)
                logger.debug(f"Cache {self.name} added key: {key}")
    
    def _evict_conditional(self) -> bool:
        """
        Evict LRU entry that passes eviction policy.
        
        Returns:
            True if entry was evicted
        """
        # Start from least recently used
        node = self._tail.prev
        attempts = 0
        max_attempts = len(self._cache)
        
        while node != self._head and attempts < max_attempts:
            attempts += 1
            
            # Check if this entry can be evicted
            can_evict = self.eviction_policy(node.key, node.value)
            
            if can_evict:
                # Evict this entry
                self._remove_node(node)
                del self._cache[node.key]
                self._evictions += 1
                logger.debug(f"Cache {self.name} evicted key: {node.key}")
                return True
            else:
                # Try next entry
                self._eviction_rejections += 1
                node = node.prev
        
        # No evictable entry found
        logger.warning(f"No evictable entry found after {attempts} attempts")
        return False
    
    def set_eviction_policy(self, policy: Callable[[Any, Any], bool]) -> None:
        """
        Update eviction policy.
        
        Args:
            policy: New eviction policy function
        """
        self.eviction_policy = policy
        logger.info("Eviction policy updated")
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics including eviction rejections."""
        stats = super().get_stats()
        stats['eviction_rejections'] = self._eviction_rejections
        return stats


__all__ = [
    'ConditionalEvictionCache',
]

