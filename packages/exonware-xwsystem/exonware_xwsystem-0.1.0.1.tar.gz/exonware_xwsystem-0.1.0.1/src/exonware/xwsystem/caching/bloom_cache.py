#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Bloom filter-enhanced cache for faster negative lookups.
Performance Priority #4 - Probabilistic data structure for efficiency.
"""

import hashlib
from typing import Any, Optional, Hashable
from .lru_cache import LRUCache
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.bloom_cache")


class SimpleBloomFilter:
    """
    Simple Bloom filter implementation.
    
    Provides probabilistic membership testing with no false negatives.
    """
    
    def __init__(self, size: int = 10000, hash_count: int = 3):
        """
        Initialize Bloom filter.
        
        Args:
            size: Bit array size
            hash_count: Number of hash functions to use
        """
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [False] * size
        self.items_added = 0
    
    def _hashes(self, item: Any) -> list[int]:
        """Generate multiple hash values for item."""
        hashes = []
        item_bytes = str(item).encode('utf-8')
        
        for i in range(self.hash_count):
            # Use different hash functions
            h = hashlib.sha256(item_bytes + str(i).encode()).hexdigest()
            hash_val = int(h, 16) % self.size
            hashes.append(hash_val)
        
        return hashes
    
    def add(self, item: Any) -> None:
        """Add item to Bloom filter."""
        for hash_val in self._hashes(item):
            self.bit_array[hash_val] = True
        self.items_added += 1
    
    def might_contain(self, item: Any) -> bool:
        """
        Check if item might be in set.
        
        Returns:
            True if item might be present (or false positive)
            False if item is definitely NOT present
        """
        return all(self.bit_array[h] for h in self._hashes(item))
    
    def clear(self) -> None:
        """Clear all items."""
        self.bit_array = [False] * self.size
        self.items_added = 0


class BloomFilterCache(LRUCache):
    """
    LRU Cache enhanced with Bloom filter for fast negative lookups.
    
    Uses Bloom filter to quickly determine if a key is definitely not in cache,
    avoiding expensive cache lookups for non-existent keys.
    
    Performance Improvement:
        - O(1) negative lookup without locking
        - Reduces lock contention
        - Ideal for high-miss-rate scenarios
    
    Example:
        cache = BloomFilterCache(capacity=10000)
        
        # Check if key might be in cache (no lock needed)
        if not cache.might_contain('user:999'):
            # Definitely not in cache, skip lookup
            return None
        
        # Key might be in cache, perform actual lookup
        value = cache.get('user:999')
    """
    
    def __init__(
        self,
        capacity: int = 128,
        bloom_size: int = None,
        ttl: Optional[float] = None,
        name: Optional[str] = None
    ):
        """
        Initialize Bloom filter cache.
        
        Args:
            capacity: Maximum cache size
            bloom_size: Bloom filter size (default: capacity * 10)
            ttl: Optional TTL in seconds
            name: Cache name
        """
        super().__init__(capacity, ttl, name)
        
        # Initialize Bloom filter
        bloom_size = bloom_size or (capacity * 10)
        self._bloom = SimpleBloomFilter(size=bloom_size, hash_count=3)
        
        # Statistics
        self._bloom_hits = 0  # Bloom said "yes", was in cache
        self._bloom_misses = 0  # Bloom said "yes", wasn't in cache (false positive)
        self._bloom_negatives = 0  # Bloom said "no" (definitely not in cache)
    
    def put(self, key: Hashable, value: Any) -> None:
        """Put value and update Bloom filter."""
        super().put(key, value)
        self._bloom.add(key)
    
    def delete(self, key: Hashable) -> bool:
        """
        Delete key from cache.
        
        Note: Bloom filter is not updated (can't remove from Bloom filter).
        This may cause false positives until Bloom filter is rebuilt.
        """
        return super().delete(key)
    
    def might_contain(self, key: Hashable) -> bool:
        """
        Check if key might be in cache (fast, no lock).
        
        Args:
            key: Key to check
            
        Returns:
            True if key might be in cache
            False if key is definitely NOT in cache
        """
        return self._bloom.might_contain(key)
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """
        Get value with Bloom filter optimization.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        # Fast negative lookup (no lock needed)
        if not self._bloom.might_contain(key):
            self._bloom_negatives += 1
            self._misses += 1
            logger.debug(f"Bloom filter: {key} definitely not in cache")
            return default
        
        # Bloom filter says might be present - check cache
        value = super().get(key, default)
        
        if value != default:
            self._bloom_hits += 1
        else:
            self._bloom_misses += 1  # False positive
        
        return value
    
    def clear(self) -> None:
        """Clear cache and reset Bloom filter."""
        super().clear()
        self._bloom.clear()
    
    def rebuild_bloom_filter(self) -> None:
        """Rebuild Bloom filter from current cache entries."""
        self._bloom.clear()
        for key in self.keys():
            self._bloom.add(key)
        logger.info("Bloom filter rebuilt")
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics including Bloom filter metrics."""
        stats = super().get_stats()
        stats['bloom_size'] = self._bloom.size
        stats['bloom_items'] = self._bloom.items_added
        stats['bloom_hits'] = self._bloom_hits
        stats['bloom_misses'] = self._bloom_misses
        stats['bloom_negatives'] = self._bloom_negatives
        
        # Calculate Bloom filter efficiency
        total_bloom = self._bloom_hits + self._bloom_misses
        if total_bloom > 0:
            stats['bloom_false_positive_rate'] = self._bloom_misses / total_bloom
        
        return stats


__all__ = [
    'BloomFilterCache',
    'SimpleBloomFilter',
]

