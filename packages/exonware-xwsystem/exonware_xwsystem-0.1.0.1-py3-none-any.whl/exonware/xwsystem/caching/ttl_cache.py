"""
TTL (Time To Live) Cache Implementation
======================================

Production-grade TTL caching for XSystem.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generated: 2025-01-27
"""

import asyncio
import time
import threading
from typing import Any, Optional, Union
from dataclasses import dataclass
import logging
from .base import ACache

logger = logging.getLogger(__name__)


@dataclass
class TTLEntry:
    """Entry in TTL cache with expiration time."""
    value: Any
    expires_at: float
    access_count: int = 0
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.expires_at
    
    def touch(self):
        """Update access count."""
        self.access_count += 1


class TTLCache(ACache):
    """
    Production-grade Time-To-Live cache with automatic expiration.
    
    Features:
    - Automatic expiration based on TTL
    - LRU eviction when capacity is reached
    - Thread-safe operations
    - Statistics tracking
    - Background cleanup
    - Configurable cleanup intervals
    """
    
    def __init__(self, 
                 capacity: int = 128, 
                 ttl: float = 300.0,
                 cleanup_interval: float = 60.0,
                 name: str = "ttl_cache"):
        """
        Initialize TTL cache.
        
        Args:
            capacity: Maximum number of entries
            ttl: Time to live in seconds
            cleanup_interval: Cleanup interval in seconds
            name: Cache name for debugging
        """
        if capacity <= 0:
            raise ValueError(
                f"Cache capacity must be positive, got {capacity}. "
                f"Example: TTLCache(capacity=128, ttl=300.0)"
            )
        
        # Call parent constructor
        super().__init__(capacity=capacity, ttl=int(ttl))
        
        self.cleanup_interval = cleanup_interval
        self.name = name
        
        # Storage
        self._cache: dict[str, TTLEntry] = {}
        self._access_order = []  # For LRU tracking
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'cleanups': 0
        }
        
        # Background cleanup
        self._cleanup_thread = None
        self._shutdown = threading.Event()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        if self.cleanup_interval > 0:
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                name=f"TTLCache-{self.name}-cleanup",
                daemon=True
            )
            self._cleanup_thread.start()
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        while not self._shutdown.wait(self.cleanup_interval):
            try:
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"TTL cache cleanup error: {e}")
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.expires_at <= current_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats['expirations'] += 1
            
            if expired_keys:
                self._stats['cleanups'] += 1
                logger.debug(f"TTL cache '{self.name}' cleaned up {len(expired_keys)} expired entries")
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]
            self._stats['evictions'] += 1
    
    def _update_access_order(self, key: str):
        """Update LRU access order."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Custom TTL for this entry (overrides default)
            
        Returns:
            True if stored successfully
        """
        with self._lock:
            try:
                # Use custom TTL or default
                entry_ttl = ttl if ttl is not None else self.ttl
                expires_at = time.time() + entry_ttl
                
                # Create entry
                entry = TTLEntry(value=value, expires_at=expires_at)
                
                # Check if we need to make space
                if key not in self._cache and len(self._cache) >= self.capacity:
                    self._evict_lru()
                
                # Store entry
                self._cache[key] = entry
                self._update_access_order(key)
                
                logger.debug(f"TTL cache '{self.name}' stored key '{key}' (expires in {entry_ttl}s)")
                return True
                
            except Exception as e:
                logger.error(f"TTL cache put error: {e}")
                return False
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache (abstract method implementation).
        Delegates to put() for backward compatibility.
        
        Args:
            key: Key to store
            value: Value to store
            ttl: Optional time-to-live in seconds
        """
        self.put(key, value, float(ttl) if ttl is not None else None)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return default
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats['misses'] += 1
                self._stats['expirations'] += 1
                return default
            
            # Update access tracking
            entry.touch()
            self._update_access_order(key)
            self._stats['hits'] += 1
            
            return entry.value
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return True
            return False
    
    def clear(self):
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            logger.debug(f"TTL cache '{self.name}' cleared")
    
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
        Evict entry from cache (uses LRU strategy).
        Implementation of abstract method from ACacheBase.
        """
        with self._lock:
            self._evict_lru()
    
    def contains(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats['expirations'] += 1
                return False
            
            return True
    
    def keys(self) -> list[str]:
        """Get list of all cache keys."""
        with self._lock:
            return list(self._cache.keys())
    
    def values(self) -> list[Any]:
        """Get list of all cache values."""
        with self._lock:
            return [entry.value for entry in self._cache.values() if not entry.is_expired()]
    
    def items(self) -> list[tuple[str, Any]]:
        """Get list of all key-value pairs."""
        with self._lock:
            return [(key, entry.value) for key, entry in self._cache.items() if not entry.is_expired()]
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0.0
            
            return {
                'name': self.name,
                'capacity': self.capacity,
                'size': len(self._cache),
                'ttl': self.ttl,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'cleanups': self._stats['cleanups']
            }
    
    def get_remaining_ttl(self, key: str) -> Optional[float]:
        """Get remaining TTL for a key."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            remaining = entry.expires_at - time.time()
            return max(0, remaining) if remaining > 0 else None
    
    def shutdown(self):
        """Shutdown the cache and cleanup thread."""
        self._shutdown.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1.0)
    
    def __del__(self):
        """Cleanup on deletion."""
        self.shutdown()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


class AsyncTTLCache:
    """
    Async-compatible TTL cache.
    
    Features:
    - Full asyncio integration
    - Automatic expiration
    - Async cleanup tasks
    - Thread-safe operations
    """
    
    def __init__(self, 
                 capacity: int = 128, 
                 ttl: float = 300.0,
                 cleanup_interval: float = 60.0,
                 name: str = "async_ttl_cache"):
        """Initialize async TTL cache."""
        self.capacity = capacity
        self.ttl = ttl
        self.cleanup_interval = cleanup_interval
        self.name = name
        
        # Storage
        self._cache: dict[str, TTLEntry] = {}
        self._access_order = []
        
        # Async synchronization
        self._lock = asyncio.Lock()
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'cleanups': 0
        }
        
        # Background cleanup task
        self._cleanup_task = None
        self._shutdown = False
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        if self.cleanup_interval > 0:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.cleanup_interval)
                if not self._shutdown:
                    await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Async TTL cache cleanup error: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired entries."""
        async with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.expires_at <= current_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats['expirations'] += 1
            
            if expired_keys:
                self._stats['cleanups'] += 1
                logger.debug(f"Async TTL cache '{self.name}' cleaned up {len(expired_keys)} expired entries")
    
    async def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Store a value in the async cache."""
        async with self._lock:
            try:
                # Use custom TTL or default
                entry_ttl = ttl if ttl is not None else self.ttl
                expires_at = time.time() + entry_ttl
                
                # Create entry
                entry = TTLEntry(value=value, expires_at=expires_at)
                
                # Check if we need to make space
                if key not in self._cache and len(self._cache) >= self.capacity:
                    await self._evict_lru()
                
                # Store entry
                self._cache[key] = entry
                self._update_access_order(key)
                
                return True
                
            except Exception as e:
                logger.error(f"Async TTL cache put error: {e}")
                return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the async cache."""
        async with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return default
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats['misses'] += 1
                self._stats['expirations'] += 1
                return default
            
            # Update access tracking
            entry.touch()
            self._update_access_order(key)
            self._stats['hits'] += 1
            
            return entry.value
    
    async def delete(self, key: str) -> bool:
        """Delete a key from the async cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return True
            return False
    
    async def clear(self):
        """Clear all entries from the async cache."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    async def size(self) -> int:
        """Get current cache size."""
        async with self._lock:
            return len(self._cache)
    
    async def get_stats(self) -> dict[str, Any]:
        """Get async cache statistics."""
        async with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0.0
            
            return {
                'name': self.name,
                'capacity': self.capacity,
                'size': len(self._cache),
                'ttl': self.ttl,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'cleanups': self._stats['cleanups']
            }
    
    async def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]
            self._stats['evictions'] += 1
    
    def _update_access_order(self, key: str):
        """Update LRU access order."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    async def shutdown(self):
        """Shutdown the async cache."""
        self._shutdown = True
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()
