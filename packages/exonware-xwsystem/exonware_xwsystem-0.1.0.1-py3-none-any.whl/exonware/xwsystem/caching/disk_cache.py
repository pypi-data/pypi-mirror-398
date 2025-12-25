#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 26, 2025

Disk cache implementation with pickle-based persistence.
"""

import os
import pickle
import hashlib
import threading
import time
from pathlib import Path
from typing import Any, Optional
from .contracts import ICache
from .errors import CacheError
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.disk_cache")


class DiskCache(ICache):
    """
    Disk-based cache with pickle persistence.
    
    Features:
    - Pickle-based serialization
    - SHA256 key hashing for filesystem safety
    - Size limits and eviction policies
    - Thread-safe file operations
    - Automatic cache directory management
    """
    
    def __init__(
        self,
        namespace: str = "default",
        cache_dir: Optional[str] = None,
        max_size: int = 1000,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        cleanup_interval: int = 3600,  # 1 hour
    ):
        """
        Initialize disk cache.
        
        Args:
            namespace: Cache namespace for organization
            cache_dir: Custom cache directory (default: ~/.xwsystem/cache/{namespace}/)
            max_size: Maximum number of cache entries
            max_file_size: Maximum size per cache file in bytes
            cleanup_interval: Cleanup interval in seconds
        """
        self.namespace = namespace
        self.max_size = max_size
        self.max_file_size = max_file_size
        self.cleanup_interval = cleanup_interval
        
        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            home_dir = Path.home()
            self.cache_dir = home_dir / ".xwsystem" / "cache" / namespace
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Metadata file for tracking cache entries
        self.metadata_file = self.cache_dir / "metadata.pkl"
        self._metadata: dict[str, dict[str, Any]] = {}
        self._load_metadata()
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'errors': 0,
        }
        
        # Last cleanup time
        self._last_cleanup = time.time()
    
    def _load_metadata(self):
        """Load cache metadata from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'rb') as f:
                    self._metadata = pickle.load(f)
            else:
                self._metadata = {}
        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {e}")
            self._metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self._metadata, f)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
            self._stats['errors'] += 1
    
    def _hash_key(self, key: str) -> str:
        """Hash key for filesystem safety."""
        return hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key."""
        hashed_key = self._hash_key(key)
        return self.cache_dir / f"{hashed_key}.pkl"
    
    def _cleanup_if_needed(self):
        """Cleanup old entries if needed."""
        current_time = time.time()
        if current_time - self._last_cleanup < self.cleanup_interval:
            return
        
        with self._lock:
            try:
                # Remove expired entries
                expired_keys = []
                for key, metadata in self._metadata.items():
                    if 'expires' in metadata and metadata['expires'] < current_time:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    self._delete_entry(key)
                
                # Evict oldest entries if over limit
                if len(self._metadata) > self.max_size:
                    # Sort by access time and evict oldest
                    sorted_items = sorted(
                        self._metadata.items(),
                        key=lambda x: x[1].get('last_access', 0)
                    )
                    
                    evict_count = len(self._metadata) - self.max_size
                    for key, _ in sorted_items[:evict_count]:
                        self._delete_entry(key)
                        self._stats['evictions'] += 1
                
                self._last_cleanup = current_time
                
            except Exception as e:
                logger.error(f"Cache cleanup failed: {e}")
                self._stats['errors'] += 1
    
    def _delete_entry(self, key: str):
        """Delete cache entry."""
        try:
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
            
            if key in self._metadata:
                del self._metadata[key]
                
        except Exception as e:
            logger.warning(f"Failed to delete cache entry {key}: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            try:
                self._cleanup_if_needed()
                
                if key not in self._metadata:
                    self._stats['misses'] += 1
                    return None
                
                metadata = self._metadata[key]
                
                # Check expiration
                if 'expires' in metadata and metadata['expires'] < time.time():
                    self._delete_entry(key)
                    self._stats['misses'] += 1
                    return None
                
                # Load from disk
                cache_file = self._get_cache_file(key)
                if not cache_file.exists():
                    del self._metadata[key]
                    self._stats['misses'] += 1
                    return None
                
                with open(cache_file, 'rb') as f:
                    value = pickle.load(f)
                
                # Update access time
                metadata['last_access'] = time.time()
                self._save_metadata()
                
                self._stats['hits'] += 1
                return value
                
            except Exception as e:
                logger.error(f"Cache get failed for key {key}: {e}")
                self._stats['errors'] += 1
                self._stats['misses'] += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            try:
                self._cleanup_if_needed()
                
                # Check file size limit
                serialized = pickle.dumps(value)
                if len(serialized) > self.max_file_size:
                    logger.warning(f"Value too large for cache: {len(serialized)} bytes")
                    return False
                
                # Save to disk
                cache_file = self._get_cache_file(key)
                with open(cache_file, 'wb') as f:
                    f.write(serialized)
                
                # Update metadata
                metadata = {
                    'size': len(serialized),
                    'created': time.time(),
                    'last_access': time.time(),
                }
                
                if ttl:
                    metadata['expires'] = time.time() + ttl
                
                self._metadata[key] = metadata
                self._save_metadata()
                
                self._stats['sets'] += 1
                return True
                
            except Exception as e:
                logger.error(f"Cache set failed for key {key}: {e}")
                self._stats['errors'] += 1
                return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self._lock:
            try:
                if key in self._metadata:
                    self._delete_entry(key)
                    self._stats['deletes'] += 1
                    return True
                return False
                
            except Exception as e:
                logger.error(f"Cache delete failed for key {key}: {e}")
                self._stats['errors'] += 1
                return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            try:
                # Delete all cache files
                for cache_file in self.cache_dir.glob("*.pkl"):
                    if cache_file.name != "metadata.pkl":
                        cache_file.unlink()
                
                # Clear metadata
                self._metadata.clear()
                self._save_metadata()
                
                return True
                
            except Exception as e:
                logger.error(f"Cache clear failed: {e}")
                self._stats['errors'] += 1
                return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            try:
                if key not in self._metadata:
                    return False
                
                metadata = self._metadata[key]
                
                # Check expiration
                if 'expires' in metadata and metadata['expires'] < time.time():
                    self._delete_entry(key)
                    return False
                
                # Check file exists
                cache_file = self._get_cache_file(key)
                return cache_file.exists()
                
            except Exception as e:
                logger.error(f"Cache exists check failed for key {key}: {e}")
                return False
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._metadata)
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'namespace': self.namespace,
                'size': len(self._metadata),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': hit_rate,
                'sets': self._stats['sets'],
                'deletes': self._stats['deletes'],
                'evictions': self._stats['evictions'],
                'errors': self._stats['errors'],
                'cache_dir': str(self.cache_dir),
            }


__all__ = [
    "DiskCache",
]
