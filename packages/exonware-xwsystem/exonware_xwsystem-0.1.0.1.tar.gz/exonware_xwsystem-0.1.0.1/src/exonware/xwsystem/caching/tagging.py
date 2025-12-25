#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Tag-based cache invalidation.
Extensibility Priority #5 - Flexible invalidation patterns.
"""

from typing import Any, Optional, Hashable
from collections import defaultdict
from .lru_cache import LRUCache
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.tagging")


class TaggedCache(LRUCache):
    """
    Cache with tag-based invalidation support.
    
    Allows associating tags with cache entries for bulk invalidation.
    
    Example:
        cache = TaggedCache(capacity=1000)
        
        # Tag entries
        cache.put('user:1', user1_data, tags=['user', 'active'])
        cache.put('user:2', user2_data, tags=['user', 'inactive'])
        cache.put('product:1', product_data, tags=['product'])
        
        # Invalidate all user entries
        cache.invalidate_by_tag('user')
        
        # Invalidate multiple tags
        cache.invalidate_by_tags(['user', 'product'])
    """
    
    def __init__(self, capacity: int = 128, ttl: Optional[float] = None, name: Optional[str] = None):
        """
        Initialize tagged cache.
        
        Args:
            capacity: Maximum cache size
            ttl: Optional TTL in seconds
            name: Cache name
        """
        super().__init__(capacity, ttl, name)
        
        # Tag tracking
        self._key_to_tags: dict[Hashable, set[str]] = {}
        self._tag_to_keys: dict[str, set[Hashable]] = defaultdict(set)
        self._invalidations = 0
    
    def put(self, key: Hashable, value: Any, tags: Optional[list[str]] = None) -> None:
        """
        Put value with optional tags.
        
        Args:
            key: Cache key
            value: Value to cache
            tags: List of tags to associate with entry
        """
        # Store in cache
        super().put(key, value)
        
        # Update tags
        if tags:
            self._key_to_tags[key] = set(tags)
            for tag in tags:
                self._tag_to_keys[tag].add(key)
            
            logger.debug(f"Cached {key} with tags: {tags}")
    
    def delete(self, key: Hashable) -> bool:
        """
        Delete key and remove from tag mappings.
        
        Args:
            key: Key to delete
            
        Returns:
            True if deleted
        """
        # Remove from tag mappings
        if key in self._key_to_tags:
            tags = self._key_to_tags[key]
            for tag in tags:
                self._tag_to_keys[tag].discard(key)
                # Clean up empty tag sets
                if not self._tag_to_keys[tag]:
                    del self._tag_to_keys[tag]
            del self._key_to_tags[key]
        
        # Delete from cache
        return super().delete(key)
    
    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all entries with a specific tag.
        
        Args:
            tag: Tag to invalidate
            
        Returns:
            Number of entries invalidated
        """
        if tag not in self._tag_to_keys:
            return 0
        
        # Get all keys with this tag
        keys_to_delete = list(self._tag_to_keys[tag])
        count = 0
        
        for key in keys_to_delete:
            if self.delete(key):
                count += 1
        
        self._invalidations += count
        logger.info(f"Invalidated {count} entries with tag '{tag}'")
        return count
    
    def invalidate_by_tags(self, tags: list[str]) -> int:
        """
        Invalidate all entries with any of the specified tags.
        
        Args:
            tags: List of tags to invalidate
            
        Returns:
            Number of entries invalidated
        """
        keys_to_delete = set()
        
        for tag in tags:
            if tag in self._tag_to_keys:
                keys_to_delete.update(self._tag_to_keys[tag])
        
        count = 0
        for key in keys_to_delete:
            if self.delete(key):
                count += 1
        
        self._invalidations += count
        logger.info(f"Invalidated {count} entries with tags: {tags}")
        return count
    
    def get_keys_by_tag(self, tag: str) -> set[Hashable]:
        """
        Get all keys associated with a tag.
        
        Args:
            tag: Tag to query
            
        Returns:
            Set of keys with this tag
        """
        return self._tag_to_keys.get(tag, set()).copy()
    
    def get_tags(self, key: Hashable) -> set[str]:
        """
        Get all tags associated with a key.
        
        Args:
            key: Key to query
            
        Returns:
            Set of tags for this key
        """
        return self._key_to_tags.get(key, set()).copy()
    
    def get_all_tags(self) -> set[str]:
        """
        Get all tags in cache.
        
        Returns:
            Set of all tags
        """
        return set(self._tag_to_keys.keys())
    
    def clear(self) -> None:
        """Clear cache and all tag mappings."""
        super().clear()
        self._key_to_tags.clear()
        self._tag_to_keys.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics including tag information."""
        stats = super().get_stats()
        stats['total_tags'] = len(self._tag_to_keys)
        stats['invalidations'] = self._invalidations
        stats['tagged_entries'] = len(self._key_to_tags)
        return stats


__all__ = [
    'TaggedCache',
]

