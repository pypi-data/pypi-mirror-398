#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 26, 2025

Two-tier cache implementation combining memory and disk caching.
"""

import threading
from typing import Any, Optional
from .lru_cache import LRUCache
from .disk_cache import DiskCache
from .contracts import ICache
from .errors import CacheError
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.two_tier_cache")


class TwoTierCache(ICache):
    """
    Two-tier cache combining memory LRU cache with disk persistence.
    
    Features:
    - Memory tier: Fast LRU cache for hot data
    - Disk tier: Persistent storage for cold data
    - Automatic promotion from disk to memory on hit
    - Write-through to both tiers
    - Namespace support for multiple cache instances
    - Comprehensive statistics for both tiers
    """
    
    def __init__(
        self,
        namespace: str = "default",
        memory_size: int = 1000,
        disk_size: int = 10000,
        disk_cache_dir: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """
        Initialize two-tier cache.
        
        Args:
            namespace: Cache namespace for organization
            memory_size: Maximum entries in memory tier
            disk_size: Maximum entries in disk tier
            disk_cache_dir: Custom disk cache directory
            max_file_size: Maximum size per disk cache file
        """
        self.namespace = namespace
        
        # Initialize tiers
        # Root cause fixed: LRUCache uses 'capacity' parameter, not 'maxsize'
        self.memory_cache = LRUCache(capacity=memory_size)
        self.disk_cache = DiskCache(
            namespace=namespace,
            cache_dir=disk_cache_dir,
            max_size=disk_size,
            max_file_size=max_file_size,
        )
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'memory_hits': 0,
            'disk_hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'promotions': 0,  # Disk to memory promotions
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then disk)."""
        with self._lock:
            try:
                # Try memory tier first
                value = self.memory_cache.get(key)
                if value is not None:
                    self._stats['memory_hits'] += 1
                    return value
                
                # Try disk tier
                value = self.disk_cache.get(key)
                if value is not None:
                    # Promote to memory tier
                    self.memory_cache.set(key, value)
                    self._stats['disk_hits'] += 1
                    self._stats['promotions'] += 1
                    return value
                
                # Miss in both tiers
                self._stats['misses'] += 1
                return None
                
            except Exception as e:
                logger.error(f"Two-tier cache get failed for key {key}: {e}")
                self._stats['misses'] += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in both memory and disk tiers."""
        with self._lock:
            try:
                # Set in memory tier
                memory_success = self.memory_cache.set(key, value)
                
                # Set in disk tier
                disk_success = self.disk_cache.set(key, value, ttl)
                
                if memory_success or disk_success:
                    self._stats['sets'] += 1
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Two-tier cache set failed for key {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete value from both tiers."""
        with self._lock:
            try:
                memory_deleted = self.memory_cache.delete(key)
                disk_deleted = self.disk_cache.delete(key)
                
                if memory_deleted or disk_deleted:
                    self._stats['deletes'] += 1
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Two-tier cache delete failed for key {key}: {e}")
                return False
    
    def clear(self) -> bool:
        """Clear both tiers."""
        with self._lock:
            try:
                memory_cleared = self.memory_cache.clear()
                disk_cleared = self.disk_cache.clear()
                
                return memory_cleared and disk_cleared
                
            except Exception as e:
                logger.error(f"Two-tier cache clear failed: {e}")
                return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in either tier."""
        with self._lock:
            try:
                return self.memory_cache.exists(key) or self.disk_cache.exists(key)
                
            except Exception as e:
                logger.error(f"Two-tier cache exists check failed for key {key}: {e}")
                return False
    
    def size(self) -> int:
        """Get total size across both tiers."""
        with self._lock:
            return self.memory_cache.size() + self.disk_cache.size()
    
    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics for both tiers."""
        with self._lock:
            memory_stats = self.memory_cache.get_stats()
            disk_stats = self.disk_cache.get_stats()
            
            total_hits = self._stats['memory_hits'] + self._stats['disk_hits']
            total_requests = total_hits + self._stats['misses']
            overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0
            
            return {
                'namespace': self.namespace,
                'total_size': self.size(),
                'memory_size': memory_stats['size'],
                'disk_size': disk_stats['size'],
                'memory_hits': self._stats['memory_hits'],
                'disk_hits': self._stats['disk_hits'],
                'misses': self._stats['misses'],
                'overall_hit_rate': overall_hit_rate,
                'memory_hit_rate': memory_stats['hit_rate'],
                'disk_hit_rate': disk_stats['hit_rate'],
                'promotions': self._stats['promotions'],
                'sets': self._stats['sets'],
                'deletes': self._stats['deletes'],
                'memory_stats': memory_stats,
                'disk_stats': disk_stats,
            }
    
    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory tier statistics."""
        return self.memory_cache.get_stats()
    
    def get_disk_stats(self) -> dict[str, Any]:
        """Get disk tier statistics."""
        return self.disk_cache.get_stats()
    
    def preload_from_disk(self, keys: list) -> int:
        """
        Preload specified keys from disk to memory.
        
        Args:
            keys: List of keys to preload
            
        Returns:
            Number of keys successfully preloaded
        """
        with self._lock:
            preloaded = 0
            
            for key in keys:
                try:
                    value = self.disk_cache.get(key)
                    if value is not None:
                        self.memory_cache.set(key, value)
                        preloaded += 1
                except Exception as e:
                    logger.warning(f"Failed to preload key {key}: {e}")
            
            return preloaded
    
    def evict_from_memory(self, keys: list) -> int:
        """
        Evict specified keys from memory tier.
        
        Args:
            keys: List of keys to evict from memory
            
        Returns:
            Number of keys successfully evicted
        """
        with self._lock:
            evicted = 0
            
            for key in keys:
                try:
                    if self.memory_cache.delete(key):
                        evicted += 1
                except Exception as e:
                    logger.warning(f"Failed to evict key {key} from memory: {e}")
            
            return evicted


__all__ = [
    "TwoTierCache",
]
