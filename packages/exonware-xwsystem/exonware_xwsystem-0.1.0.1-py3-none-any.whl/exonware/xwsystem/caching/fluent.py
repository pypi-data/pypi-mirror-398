#!/usr/bin/env python3
#exonware/xwsystem/caching/fluent.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Fluent API wrappers for caching module.
Usability Priority #2 - Method chaining for better developer experience.
"""

from typing import Any, Optional, Hashable
from .lru_cache import LRUCache
from .lfu_cache import LFUCache
from .ttl_cache import TTLCache


class FluentLRUCache(LRUCache):
    """
    LRU Cache with fluent API for method chaining.
    
    Example:
        cache = FluentLRUCache(capacity=100)
        cache.put("k1", "v1").put("k2", "v2").put("k3", "v3")
        
        value = cache.get("k1")  # Still returns the value, not self
        
        cache.delete("k1").delete("k2").clear()  # Chain operations
    """
    
    def put(self, key: Hashable, value: Any) -> 'FluentLRUCache':
        """
        Put value and return self for chaining.
        
        Args:
            key: Cache key
            value: Value to cache
            
        Returns:
            Self for method chaining
        """
        super().put(key, value)
        return self
    
    def delete(self, key: Hashable) -> 'FluentLRUCache':
        """
        Delete key and return self for chaining.
        
        Args:
            key: Cache key to delete
            
        Returns:
            Self for method chaining
        """
        super().delete(key)
        return self
    
    def clear(self) -> 'FluentLRUCache':
        """
        Clear cache and return self for chaining.
        
        Returns:
            Self for method chaining
        """
        super().clear()
        return self


class FluentLFUCache(LFUCache):
    """
    LFU Cache with fluent API for method chaining.
    
    Example:
        cache = FluentLFUCache(capacity=100)
        cache.put("k1", "v1").put("k2", "v2").put("k3", "v3")
    """
    
    def put(self, key: Hashable, value: Any) -> 'FluentLFUCache':
        """Put value and return self for chaining."""
        super().put(key, value)
        return self
    
    def delete(self, key: Hashable) -> 'FluentLFUCache':
        """Delete key and return self for chaining."""
        super().delete(key)
        return self
    
    def clear(self) -> 'FluentLFUCache':
        """Clear cache and return self for chaining."""
        super().clear()
        return self


class FluentTTLCache(TTLCache):
    """
    TTL Cache with fluent API for method chaining.
    
    Example:
        cache = FluentTTLCache(capacity=100, ttl=300.0)
        cache.put("k1", "v1").put("k2", "v2", ttl=60.0).put("k3", "v3")
    """
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> 'FluentTTLCache':
        """Put value and return self for chaining."""
        super().put(key, value, ttl)
        return self
    
    def delete(self, key: str) -> 'FluentTTLCache':
        """Delete key and return self for chaining."""
        super().delete(key)
        return self
    
    def clear(self) -> 'FluentTTLCache':
        """Clear cache and return self for chaining."""
        super().clear()
        return self


__all__ = [
    'FluentLRUCache',
    'FluentLFUCache',
    'FluentTTLCache',
]

