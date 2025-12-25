"""
#exonware/xwsystem/tests/1.unit/caching_unit/lru_cache_tests/test_lru_cache.py

Unit tests for LRU cache implementation.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import time
import threading

# Import directly from submodules
from exonware.xwsystem.caching.lru_cache import LRUCache, AsyncLRUCache


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_caching
class TestLRUCache:
    """Unit tests for LRUCache."""
    
    def test_create_with_valid_capacity(self):
        """Test creating LRU cache with valid capacity."""
        cache = LRUCache(capacity=128)
        assert cache.capacity == 128
        assert cache.size() == 0
    
    def test_create_with_invalid_capacity_raises_error(self):
        """Test creating cache with invalid capacity raises error."""
        with pytest.raises(ValueError, match="capacity must be positive"):
            LRUCache(capacity=0)
        
        with pytest.raises(ValueError, match="capacity must be positive"):
            LRUCache(capacity=-1)
    
    def test_put_and_get(self):
        """Test basic put and get operations."""
        cache = LRUCache(capacity=10)
        
        cache.put('key1', 'value1')
        result = cache.get('key1')
        
        assert result == 'value1'
    
    def test_get_nonexistent_key_returns_default(self):
        """Test getting nonexistent key returns default value."""
        cache = LRUCache(capacity=10)
        
        result = cache.get('nonexistent', 'default')
        assert result == 'default'
    
    def test_eviction_behavior(self):
        """Test LRU eviction behavior."""
        cache = LRUCache(capacity=3)
        
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')
        
        # Access key1 to make it recently used
        cache.get('key1')
        
        # Add new key - should evict key2 (least recently used)
        cache.put('key4', 'value4')
        
        assert cache.get('key1') == 'value1'  # Still there
        assert cache.get('key2') is None  # Evicted
        assert cache.get('key3') == 'value3'  # Still there
        assert cache.get('key4') == 'value4'  # New entry
    
    def test_statistics_tracking(self):
        """Test hit/miss statistics are tracked correctly."""
        cache = LRUCache(capacity=10)
        
        cache.put('key1', 'value1')
        
        cache.get('key1')  # Hit
        cache.get('key2')  # Miss
        cache.get('key1')  # Hit
        
        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
    
    def test_context_manager(self):
        """Test cache can be used as context manager."""
        with LRUCache(capacity=10) as cache:
            cache.put('key1', 'value1')
            assert cache.get('key1') == 'value1'
    
    def test_unicode_keys_and_values(self, multilingual_cache_data):
        """Test cache handles Unicode keys and values."""
        cache = LRUCache(capacity=10)
        
        for key, value in multilingual_cache_data.items():
            cache.put(key, value)
        
        # Verify all entries
        for key, value in multilingual_cache_data.items():
            assert cache.get(key) == value


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_caching
class TestAsyncLRUCache:
    """Unit tests for AsyncLRUCache."""
    
    @pytest.mark.asyncio
    async def test_async_put_and_get(self):
        """Test async put and get operations."""
        cache = AsyncLRUCache(capacity=10)
        
        await cache.put('key1', 'value1')
        result = await cache.get('key1')
        
        assert result == 'value1'
    
    @pytest.mark.asyncio
    async def test_async_eviction(self):
        """Test async cache eviction."""
        cache = AsyncLRUCache(capacity=2)
        
        await cache.put('key1', 'value1')
        await cache.put('key2', 'value2')
        await cache.put('key3', 'value3')  # Should evict key1
        
        result = await cache.get('key1')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async cache as context manager."""
        async with AsyncLRUCache(capacity=10) as cache:
            await cache.put('key1', 'value1')
            result = await cache.get('key1')
            assert result == 'value1'

