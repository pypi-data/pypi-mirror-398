#exonware/xwsystem/caching/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Caching module base classes - abstract classes for caching functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Hashable
from .defs import CachePolicy


class ACache(ABC):
    """Abstract base class for all cache implementations."""
    
    def __init__(self, capacity: int = 1000, ttl: Optional[int] = None):
        """
        Initialize cache base.
        
        Args:
            capacity: Maximum cache size
            ttl: Time to live in seconds
        """
        self.capacity = capacity
        self.ttl = ttl
        self._cache: dict[str, Any] = {}
        self._access_times: dict[str, float] = {}
        self._creation_times: dict[str, float] = {}
    
    @abstractmethod
    def get(self, key: Any, default: Any = None) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key (Hashable)
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        pass
    
    @abstractmethod
    def put(self, key: Any, value: Any) -> None:
        """
        Put value in cache.
        
        Args:
            key: Cache key (Hashable)
            value: Value to cache
        """
        pass
    
    @abstractmethod
    def delete(self, key: Any) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get cache size."""
        pass
    
    @abstractmethod
    def is_full(self) -> bool:
        """Check if cache is full."""
        pass
    
    @abstractmethod
    def evict(self) -> None:
        """Evict entries from cache."""
        pass
    
    @abstractmethod
    def keys(self) -> list[Hashable]:
        """
        Get list of all cache keys.
        
        Returns:
            List of cache keys (Hashable objects)
        """
        pass
    
    @abstractmethod
    def values(self) -> list[Any]:
        """
        Get list of all cache values.
        
        Returns:
            List of cache values
        """
        pass
    
    @abstractmethod
    def items(self) -> list[tuple[Hashable, Any]]:
        """
        Get list of all key-value pairs.
        
        Returns:
            List of (key, value) tuples
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with statistics (hits, misses, hit_rate, etc.)
        """
        pass
    
    def __contains__(self, key: Any) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists in cache
        """
        # Default implementation - subclasses can override for efficiency
        return self.get(key) is not None
    
    def __len__(self) -> int:
        """
        Get number of items in cache.
        
        Returns:
            Number of items in cache
        """
        return self.size()
    
    def get_many(self, keys: list[Hashable]) -> dict[Hashable, Any]:
        """
        Get multiple values in a single operation.
        
        Args:
            keys: List of keys to retrieve
            
        Returns:
            Dictionary of key-value pairs found in cache
            
        Note:
            More efficient than individual gets for batch operations.
        """
        results = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                results[key] = value
        return results
    
    def put_many(self, items: dict[Hashable, Any]) -> int:
        """
        Put multiple key-value pairs in a single operation.
        
        Args:
            items: Dictionary of key-value pairs to cache
            
        Returns:
            Number of items successfully cached
            
        Note:
            More efficient than individual puts for batch operations.
        """
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
        Delete multiple keys in a single operation.
        
        Args:
            keys: List of keys to delete
            
        Returns:
            Number of keys successfully deleted
            
        Note:
            More efficient than individual deletes for batch operations.
        """
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count


class ACacheManager(ABC):
    """Abstract base class for cache management."""
    
    @abstractmethod
    def create_cache(self, name: str, cache_type: str, **kwargs) -> ACache:
        """Create a new cache instance."""
        pass
    
    @abstractmethod
    def get_cache(self, name: str) -> Optional[ACache]:
        """Get cache instance by name."""
        pass
    
    @abstractmethod
    def remove_cache(self, name: str) -> bool:
        """Remove cache instance."""
        pass
    
    @abstractmethod
    def list_caches(self) -> list[str]:
        """List all cache names."""
        pass
    
    @abstractmethod
    def clear_all_caches(self) -> None:
        """Clear all caches."""
        pass


class ADistributedCache(ABC):
    """Abstract base class for distributed cache implementations."""
    
    @abstractmethod
    def connect(self, nodes: list[str]) -> None:
        """Connect to distributed cache nodes."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from distributed cache."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to distributed cache."""
        pass
    
    @abstractmethod
    def get_node_info(self) -> dict[str, Any]:
        """Get distributed cache node information."""
        pass
    
    @abstractmethod
    def sync(self) -> None:
        """Synchronize cache across nodes."""
        pass


class ACacheDecorator(ABC):
    """Abstract base class for cache decorators."""
    
    @abstractmethod
    def __call__(self, func):
        """Decorate function with caching."""
        pass
    
    @abstractmethod
    def invalidate(self, *args, **kwargs) -> None:
        """Invalidate cache for specific arguments."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached results."""
        pass
