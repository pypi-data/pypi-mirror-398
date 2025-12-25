"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: January 31, 2025

Unit tests for caching framework.
"""

import asyncio
import time
import pytest
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from src.exonware.xwsystem.caching.lru_cache import LRUCache, AsyncLRUCache


class TestLRUCache:
    """Test LRU Cache functionality."""

    def test_basic_operations(self):
        """Test basic cache operations."""
        cache = LRUCache(capacity=3)
        
        # Test put and get
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.size() == 3

    def test_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = LRUCache(capacity=2)
        
        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new item - should evict key2 (least recently used)
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # New item

    def test_update_existing_key(self):
        """Test updating existing key."""
        cache = LRUCache(capacity=2)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Update existing key
        cache.put("key1", "new_value1")
        
        assert cache.get("key1") == "new_value1"
        assert cache.size() == 2

    def test_delete_operation(self):
        """Test delete operation."""
        cache = LRUCache(capacity=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("nonexistent") is False
        assert cache.size() == 1

    def test_clear_operation(self):
        """Test clear operation."""
        cache = LRUCache(capacity=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        cache.clear()
        
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_capacity_limits(self):
        """Test capacity limits and full cache behavior."""
        cache = LRUCache(capacity=2)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        assert cache.is_full() is True
        
        # Adding another item should evict oldest
        cache.put("key3", "value3")
        
        assert cache.size() == 2
        assert cache.get("key1") is None  # Evicted

    def test_keys_values_items(self):
        """Test keys, values, and items methods."""
        cache = LRUCache(capacity=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 to change order
        cache.get("key1")
        
        keys = cache.keys()
        values = cache.values()
        items = cache.items()
        
        assert len(keys) == 3
        assert len(values) == 3
        assert len(items) == 3
        
        # key1 should be most recently used (first in order)
        assert keys[0] == "key1"
        assert values[0] == "value1"
        assert items[0] == ("key1", "value1")

    def test_dict_like_interface(self):
        """Test dictionary-like interface."""
        cache = LRUCache(capacity=3)
        
        # Test __setitem__ and __getitem__
        cache["key1"] = "value1"
        cache["key2"] = "value2"
        
        assert cache["key1"] == "value1"
        assert cache["key2"] == "value2"
        
        # Test __contains__
        assert "key1" in cache
        assert "nonexistent" not in cache
        
        # Test __len__
        assert len(cache) == 2
        
        # Test __delitem__
        del cache["key1"]
        assert "key1" not in cache

    def test_key_error_on_missing(self):
        """Test KeyError on missing key with __getitem__."""
        cache = LRUCache(capacity=3)
        
        with pytest.raises(KeyError):
            _ = cache["nonexistent"]

    def test_ttl_functionality(self):
        """Test TTL (Time To Live) functionality."""
        cache = LRUCache(capacity=3, ttl=0.1)  # 100ms TTL
        
        cache.put("key1", "value1")
        
        # Should be available immediately
        assert cache.get("key1") == "value1"
        
        # Wait for TTL to expire
        time.sleep(0.15)
        
        # Should be expired now
        assert cache.get("key1") is None

    def test_statistics(self):
        """Test cache statistics."""
        cache = LRUCache(capacity=3)
        
        # Generate some hits and misses
        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key1")  # Hit
        cache.get("key3")  # Miss
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 2
        assert stats['misses'] == 2
        assert stats['hit_rate'] == 0.5
        assert stats['capacity'] == 3
        assert stats['size'] == 1
        assert stats['type'] == 'LRU'

    def test_reset_stats(self):
        """Test statistics reset."""
        cache = LRUCache(capacity=3)
        
        cache.put("key1", "value1")
        cache.get("key1")
        cache.get("key2")
        
        stats_before = cache.get_stats()
        assert stats_before['hits'] > 0 or stats_before['misses'] > 0
        
        cache.reset_stats()
        
        stats_after = cache.get_stats()
        assert stats_after['hits'] == 0
        assert stats_after['misses'] == 0

    def test_thread_safety(self):
        """Test thread safety of LRU cache."""
        cache = LRUCache(capacity=100)
        results = []
        
        def worker(worker_id):
            # Each worker puts and gets items
            for i in range(10):
                key = f"worker_{worker_id}_item_{i}"
                value = f"value_{worker_id}_{i}"
                cache.put(key, value)
                retrieved = cache.get(key)
                results.append(retrieved == value)
        
        # Run multiple workers concurrently
        threads = []
        for i in range(5):
            thread = Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All operations should have succeeded
        assert all(results)
        assert len(results) == 50  # 5 workers * 10 items each


class TestAsyncLRUCache:
    """Test Async LRU Cache functionality."""

    @pytest.mark.asyncio
    async def test_basic_async_operations(self):
        """Test basic async cache operations."""
        cache = AsyncLRUCache(capacity=3)
        
        # Test put and get
        await cache.put("key1", "value1")
        await cache.put("key2", "value2")
        await cache.put("key3", "value3")
        
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        assert await cache.size() == 3

    @pytest.mark.asyncio
    async def test_async_lru_eviction(self):
        """Test LRU eviction policy in async cache."""
        cache = AsyncLRUCache(capacity=2)
        
        # Fill cache
        await cache.put("key1", "value1")
        await cache.put("key2", "value2")
        
        # Access key1 to make it recently used
        await cache.get("key1")
        
        # Add new item - should evict key2
        await cache.put("key3", "value3")
        
        assert await cache.get("key1") == "value1"  # Still there
        assert await cache.get("key2") is None      # Evicted
        assert await cache.get("key3") == "value3"  # New item

    @pytest.mark.asyncio
    async def test_async_delete_and_clear(self):
        """Test async delete and clear operations."""
        cache = AsyncLRUCache(capacity=3)
        
        await cache.put("key1", "value1")
        await cache.put("key2", "value2")
        
        assert await cache.delete("key1") is True
        assert await cache.get("key1") is None
        assert await cache.delete("nonexistent") is False
        
        await cache.clear()
        assert await cache.size() == 0

    @pytest.mark.asyncio
    async def test_async_ttl_functionality(self):
        """Test TTL functionality in async cache."""
        cache = AsyncLRUCache(capacity=3, ttl=0.1)  # 100ms TTL
        
        await cache.put("key1", "value1")
        
        # Should be available immediately
        assert await cache.get("key1") == "value1"
        
        # Wait for TTL to expire
        await asyncio.sleep(0.15)
        
        # Should be expired now
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_async_statistics(self):
        """Test async cache statistics."""
        cache = AsyncLRUCache(capacity=3)
        
        # Generate some hits and misses
        await cache.put("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        await cache.get("key1")  # Hit
        await cache.get("key3")  # Miss
        
        stats = await cache.get_stats()
        
        assert stats['hits'] == 2
        assert stats['misses'] == 2
        assert stats['hit_rate'] == 0.5
        assert stats['type'] == 'AsyncLRU'

    @pytest.mark.asyncio
    async def test_async_concurrent_operations(self):
        """Test concurrent async operations."""
        cache = AsyncLRUCache(capacity=100)
        
        async def worker(worker_id):
            results = []
            for i in range(10):
                key = f"worker_{worker_id}_item_{i}"
                value = f"value_{worker_id}_{i}"
                await cache.put(key, value)
                retrieved = await cache.get(key)
                results.append(retrieved == value)
            return results
        
        # Run multiple workers concurrently
        tasks = [worker(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Flatten results and check all succeeded
        all_results = [item for sublist in results for item in sublist]
        assert all(all_results)
        assert len(all_results) == 50  # 5 workers * 10 items each

    @pytest.mark.asyncio
    async def test_async_keys_values_items(self):
        """Test async keys, values, and items methods."""
        cache = AsyncLRUCache(capacity=3)
        
        await cache.put("key1", "value1")
        await cache.put("key2", "value2")
        await cache.put("key3", "value3")
        
        # Access key1 to change order
        await cache.get("key1")
        
        keys = await cache.keys()
        values = await cache.values()
        items = await cache.items()
        
        assert len(keys) == 3
        assert len(values) == 3
        assert len(items) == 3
        
        # key1 should be most recently used (first in order)
        assert keys[0] == "key1"
        assert values[0] == "value1"
        assert items[0] == ("key1", "value1")

    @pytest.mark.asyncio
    async def test_async_cache_performance(self):
        """Test async cache performance with many operations."""
        cache = AsyncLRUCache(capacity=1000)
        
        start_time = time.time()
        
        # Perform many operations
        tasks = []
        for i in range(100):
            tasks.append(cache.put(f"key_{i}", f"value_{i}"))
        
        await asyncio.gather(*tasks)
        
        # Now read them all back
        tasks = []
        for i in range(100):
            tasks.append(cache.get(f"key_{i}"))
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # Verify all operations completed correctly
        assert len(results) == 100
        for i, result in enumerate(results):
            assert result == f"value_{i}"
        
        # Should complete reasonably quickly (less than 1 second)
        assert (end_time - start_time) < 1.0


class TestCacheEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_capacity_error(self):
        """Test error on zero capacity."""
        with pytest.raises(ValueError, match="Capacity must be positive"):
            LRUCache(capacity=0)

    def test_negative_capacity_error(self):
        """Test error on negative capacity."""
        with pytest.raises(ValueError, match="Capacity must be positive"):
            LRUCache(capacity=-1)

    def test_cache_with_none_values(self):
        """Test cache behavior with None values."""
        cache = LRUCache(capacity=3)
        
        cache.put("key1", None)
        cache.put("key2", "value2")
        
        # None is a valid value
        assert cache.get("key1") is None
        assert "key1" in cache
        
        # But missing keys also return None
        assert cache.get("missing") is None
        assert "missing" not in cache

    def test_cache_with_complex_objects(self):
        """Test cache with complex objects as values."""
        cache = LRUCache(capacity=3)
        
        # Test with various object types
        cache.put("list", [1, 2, 3])
        cache.put("dict", {"a": 1, "b": 2})
        cache.put("tuple", (1, 2, 3))
        
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"a": 1, "b": 2}
        assert cache.get("tuple") == (1, 2, 3)

    def test_cache_key_types(self):
        """Test cache with different key types."""
        cache = LRUCache(capacity=5)
        
        # Test various hashable key types
        cache.put("string", "value1")
        cache.put(123, "value2")
        cache.put((1, 2), "value3")
        cache.put(frozenset([1, 2, 3]), "value4")
        
        assert cache.get("string") == "value1"
        assert cache.get(123) == "value2"
        assert cache.get((1, 2)) == "value3"
        assert cache.get(frozenset([1, 2, 3])) == "value4"

    @pytest.mark.asyncio
    async def test_async_cache_edge_cases(self):
        """Test async cache edge cases."""
        cache = AsyncLRUCache(capacity=2)
        
        # Test with None values
        await cache.put("none_key", None)
        assert await cache.get("none_key") is None
        
        # Test rapid put/get cycles
        for i in range(10):
            await cache.put(f"rapid_{i}", f"value_{i}")
            result = await cache.get(f"rapid_{i}")
            assert result == f"value_{i}"


if __name__ == "__main__":
    pytest.main([__file__])
