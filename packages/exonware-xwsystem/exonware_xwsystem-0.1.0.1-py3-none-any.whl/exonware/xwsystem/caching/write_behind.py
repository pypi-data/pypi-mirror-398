#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Write-behind (lazy write) cache implementation.
Performance Priority #4 - Delayed persistence for better write performance.
"""

import threading
import time
from typing import Any, Callable, Optional, Hashable
from .lru_cache import LRUCache
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.write_behind")


class WriteBehindCache(LRUCache):
    """
    Write-behind cache with delayed persistence.
    
    Caches writes in memory and flushes to storage periodically in background.
    Provides better write performance than write-through at the cost of
    potential data loss if system crashes before flush.
    
    Features:
        - Asynchronous writes to storage
        - Configurable flush interval
        - Automatic background flushing
        - Manual flush support
        - Dirty entry tracking
    
    Example:
        def save_to_db(key, value):
            db.update(key, value)
        
        cache = WriteBehindCache(
            capacity=1000,
            writer=save_to_db,
            flush_interval=5.0  # Flush every 5 seconds
        )
        
        # Writes cached immediately, flushed to DB later
        cache.put('user:123', user_data)
        
        # Force immediate flush if needed
        cache.flush()
    """
    
    def __init__(
        self,
        capacity: int = 128,
        writer: Optional[Callable[[Any, Any], None]] = None,
        flush_interval: float = 5.0,
        ttl: Optional[float] = None,
        name: Optional[str] = None,
        auto_start: bool = True
    ):
        """
        Initialize write-behind cache.
        
        Args:
            capacity: Maximum cache size
            writer: Function to persist values (key, value) -> None
            flush_interval: Interval between flushes in seconds
            ttl: Optional TTL in seconds
            name: Cache name
            auto_start: Automatically start background flusher
        """
        super().__init__(capacity, ttl, name)
        
        self.writer = writer
        self.flush_interval = flush_interval
        
        # Dirty entry tracking
        self._dirty_keys: set[Hashable] = set()
        self._flush_lock = threading.Lock()
        
        # Statistics
        self._flush_count = 0
        self._write_count = 0
        self._write_errors = 0
        
        # Background flusher
        self._flusher_thread = None
        self._stop_flusher = threading.Event()
        
        if auto_start and writer:
            self.start_flusher()
    
    def put(self, key: Hashable, value: Any) -> None:
        """
        Put value in cache and mark as dirty for later flush.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Cache immediately
        super().put(key, value)
        
        # Mark as dirty for flush
        with self._flush_lock:
            self._dirty_keys.add(key)
        
        logger.debug(f"Cached {key} (dirty, will flush later)")
    
    def flush(self) -> int:
        """
        Flush all dirty entries to storage.
        
        Returns:
            Number of entries flushed
        """
        if not self.writer:
            return 0
        
        with self._flush_lock:
            dirty_keys = list(self._dirty_keys)
            self._dirty_keys.clear()
        
        flushed = 0
        
        for key in dirty_keys:
            try:
                value = self.get(key)
                if value is not None:
                    self.writer(key, value)
                    flushed += 1
                    self._write_count += 1
            except Exception as e:
                logger.error(f"Failed to flush {key}: {e}")
                self._write_errors += 1
                # Re-add to dirty set
                with self._flush_lock:
                    self._dirty_keys.add(key)
        
        if flushed > 0:
            self._flush_count += 1
            logger.info(f"Flushed {flushed} entries to storage")
        
        return flushed
    
    def start_flusher(self) -> None:
        """Start background flusher thread."""
        if self._flusher_thread and self._flusher_thread.is_alive():
            logger.warning("Flusher already running")
            return
        
        self._stop_flusher.clear()
        self._flusher_thread = threading.Thread(
            target=self._background_flusher,
            daemon=True,
            name=f"{self.name}-flusher"
        )
        self._flusher_thread.start()
        logger.info(f"Started background flusher (interval: {self.flush_interval}s)")
    
    def stop_flusher(self, flush_remaining: bool = True) -> None:
        """
        Stop background flusher thread.
        
        Args:
            flush_remaining: Flush remaining dirty entries before stopping
        """
        if not self._flusher_thread or not self._flusher_thread.is_alive():
            return
        
        self._stop_flusher.set()
        self._flusher_thread.join(timeout=5.0)
        
        if flush_remaining:
            self.flush()
        
        logger.info("Stopped background flusher")
    
    def _background_flusher(self) -> None:
        """Background thread for periodic flushing."""
        logger.debug("Background flusher started")
        
        while not self._stop_flusher.is_set():
            # Wait for interval or stop signal
            if self._stop_flusher.wait(self.flush_interval):
                break
            
            # Flush dirty entries
            try:
                self.flush()
            except Exception as e:
                logger.error(f"Background flush error: {e}")
        
        logger.debug("Background flusher stopped")
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics including write-behind metrics."""
        stats = super().get_stats()
        stats['dirty_entries'] = len(self._dirty_keys)
        stats['flush_count'] = self._flush_count
        stats['write_count'] = self._write_count
        stats['write_errors'] = self._write_errors
        stats['flusher_running'] = self._flusher_thread and self._flusher_thread.is_alive()
        return stats
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.stop_flusher(flush_remaining=True)
        except:
            pass


__all__ = [
    'WriteBehindCache',
]

