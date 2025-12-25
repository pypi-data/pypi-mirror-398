#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Read-through and Write-through cache implementations.
Extensibility Priority #5 - Auto-loading and auto-writing patterns.
"""

from typing import Any, Callable, Optional, Hashable
from .lru_cache import LRUCache
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.read_through")


class ReadThroughCache(LRUCache):
    """
    Read-through cache that automatically loads missing values.
    
    When a key is not found in cache, automatically calls the loader function
    to fetch the value and cache it.
    
    Example:
        def load_user_from_db(user_id):
            return db.users.find_one({'id': user_id})
        
        cache = ReadThroughCache(
            capacity=1000,
            loader=load_user_from_db
        )
        
        # Automatically loads from DB on cache miss
        user = cache.get('user:123')
    """
    
    def __init__(
        self,
        capacity: int = 128,
        loader: Optional[Callable[[Any], Any]] = None,
        ttl: Optional[float] = None,
        name: Optional[str] = None
    ):
        """
        Initialize read-through cache.
        
        Args:
            capacity: Maximum cache size
            loader: Function to load missing values (key) -> value
            ttl: Optional TTL in seconds
            name: Cache name
        """
        super().__init__(capacity, ttl, name)
        self.loader = loader
        self._loader_calls = 0
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """
        Get value with automatic loading on miss.
        
        Args:
            key: Cache key
            default: Default if loader fails or not provided
            
        Returns:
            Cached or loaded value
        """
        # Try cache first
        value = super().get(key)
        
        if value is not None:
            return value
        
        # Cache miss - try loader
        if self.loader:
            try:
                logger.debug(f"Cache miss for {key}, calling loader")
                loaded_value = self.loader(key)
                self._loader_calls += 1
                
                # Cache the loaded value
                if loaded_value is not None:
                    self.put(key, loaded_value)
                    return loaded_value
                
            except Exception as e:
                logger.error(f"Loader failed for key {key}: {e}")
                # Fall through to default
        
        return default
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics including loader calls."""
        stats = super().get_stats()
        stats['loader_calls'] = self._loader_calls
        return stats


class WriteThroughCache(LRUCache):
    """
    Write-through cache that automatically persists writes.
    
    When a value is put in cache, automatically calls the writer function
    to persist it to storage.
    
    Example:
        def save_user_to_db(key, value):
            db.users.update({'id': key}, value, upsert=True)
        
        cache = WriteThroughCache(
            capacity=1000,
            writer=save_user_to_db
        )
        
        # Automatically saves to DB when caching
        cache.put('user:123', user_data)
    """
    
    def __init__(
        self,
        capacity: int = 128,
        writer: Optional[Callable[[Any, Any], None]] = None,
        ttl: Optional[float] = None,
        name: Optional[str] = None
    ):
        """
        Initialize write-through cache.
        
        Args:
            capacity: Maximum cache size
            writer: Function to persist values (key, value) -> None
            ttl: Optional TTL in seconds
            name: Cache name
        """
        super().__init__(capacity, ttl, name)
        self.writer = writer
        self._writer_calls = 0
        self._writer_errors = 0
    
    def put(self, key: Hashable, value: Any) -> None:
        """
        Put value with automatic persistence.
        
        Args:
            key: Cache key
            value: Value to cache and persist
        """
        # Persist first (write-through)
        if self.writer:
            try:
                logger.debug(f"Writing through to storage for key: {key}")
                self.writer(key, value)
                self._writer_calls += 1
            except Exception as e:
                logger.error(f"Writer failed for key {key}: {e}")
                self._writer_errors += 1
                # Continue to cache even if writer fails
        
        # Then cache
        super().put(key, value)
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics including writer calls."""
        stats = super().get_stats()
        stats['writer_calls'] = self._writer_calls
        stats['writer_errors'] = self._writer_errors
        return stats


class ReadWriteThroughCache(LRUCache):
    """
    Combined read-through and write-through cache.
    
    Automatically loads on miss and persists on write.
    
    Example:
        cache = ReadWriteThroughCache(
            capacity=1000,
            loader=lambda k: db.get(k),
            writer=lambda k, v: db.put(k, v)
        )
        
        # Auto-loads from DB
        value = cache.get('key')
        
        # Auto-saves to DB
        cache.put('key', new_value)
    """
    
    def __init__(
        self,
        capacity: int = 128,
        loader: Optional[Callable[[Any], Any]] = None,
        writer: Optional[Callable[[Any, Any], None]] = None,
        ttl: Optional[float] = None,
        name: Optional[str] = None
    ):
        """Initialize read-write-through cache."""
        super().__init__(capacity, ttl, name)
        self.loader = loader
        self.writer = writer
        self._loader_calls = 0
        self._writer_calls = 0
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """Get with auto-loading."""
        value = super().get(key)
        
        if value is not None:
            return value
        
        if self.loader:
            try:
                loaded_value = self.loader(key)
                self._loader_calls += 1
                if loaded_value is not None:
                    super().put(key, loaded_value)
                    return loaded_value
            except Exception as e:
                logger.error(f"Loader failed for key {key}: {e}")
        
        return default
    
    def put(self, key: Hashable, value: Any) -> None:
        """Put with auto-persistence."""
        if self.writer:
            try:
                self.writer(key, value)
                self._writer_calls += 1
            except Exception as e:
                logger.error(f"Writer failed for key {key}: {e}")
        
        super().put(key, value)
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics."""
        stats = super().get_stats()
        stats['loader_calls'] = self._loader_calls
        stats['writer_calls'] = self._writer_calls
        return stats


__all__ = [
    'ReadThroughCache',
    'WriteThroughCache',
    'ReadWriteThroughCache',
]

