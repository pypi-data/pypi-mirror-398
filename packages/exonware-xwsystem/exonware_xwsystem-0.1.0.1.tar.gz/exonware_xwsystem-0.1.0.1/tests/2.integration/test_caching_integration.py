#!/usr/bin/env python3
"""
Integration tests for caching module.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import time
import threading
import asyncio
from exonware.xwsystem.caching import (
    LRUCache,
    LFUCache,
    TTLCache,
)
from exonware.xwsystem.caching.lfu_optimized import OptimizedLFUCache
from exonware.xwsystem.caching.secure_cache import SecureLRUCache
from exonware.xwsystem.caching.observable_cache import ObservableLRUCache
from exonware.xwsystem.caching.events import CacheEvent
from exonware.xwsystem.caching.decorators import cached, async_cached
from exonware.xwsystem.caching.warming import warm_cache, PreloadWarmingStrategy


@pytest.mark.xwsystem_integration
class TestMultiCacheCoordination:
    """Test coordination between multiple cache instances."""
    
    def test_two_tier_cache_scenario(self):
        """
        Given: A two-tier cache setup (L1 memory, L2 disk simulation)
        When: Data flows through both tiers
        Then: Promotion and demotion work correctly
        """
        # L1: Small fast cache
        l1_cache = LRUCache(capacity=10)
        
        # L2: Larger slower cache
        l2_cache = LRUCache(capacity=100)
        
        # Populate L2
        for i in range(50):
            l2_cache.put(f"key_{i}", f"value_{i}")
        
        # Access pattern: promote hot items to L1
        hot_keys = [f"key_{i}" for i in range(5)]
        
        for key in hot_keys:
            value = l1_cache.get(key)
            if value is None:
                # Miss in L1, check L2
                value = l2_cache.get(key)
                if value is not None:
                    # Promote to L1
                    l1_cache.put(key, value)
        
        # Verify hot items in L1
        for key in hot_keys:
            assert l1_cache.get(key) is not None
        
        # L1 should have good hit rate for hot items
        for key in hot_keys:
            l1_cache.get(key)
        
        l1_stats = l1_cache.get_stats()
        assert l1_stats['hit_rate'] > 0.5


@pytest.mark.xwsystem_integration
class TestConcurrentCacheAccess:
    """Test concurrent access scenarios."""
    
    def test_high_concurrency_lru(self):
        """Test LRU cache under high concurrency."""
        cache = LRUCache(capacity=1000)
        errors = []
        
        def worker(worker_id: int, num_ops: int):
            try:
                for i in range(num_ops):
                    key = f"worker_{worker_id}_key_{i % 100}"
                    cache.put(key, f"value_{i}")
                    value = cache.get(key)
                    assert value is not None
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run 20 threads with 500 operations each
        threads = []
        for i in range(20):
            thread = threading.Thread(target=worker, args=(i, 500))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0, f"Errors in concurrent access: {errors[:5]}"
        
        # Verify cache state
        stats = cache.get_stats()
        assert stats['hits'] > 0
        assert stats['evictions'] >= 0


@pytest.mark.xwsystem_integration
class TestCacheWithDecorators:
    """Test cache decorators in real-world scenarios."""
    
    def test_function_caching(self):
        """Test caching expensive function results."""
        call_count = [0]
        
        @cached()
        def expensive_function(x, y):
            call_count[0] += 1
            time.sleep(0.01)  # Simulate expensive operation
            return x + y
        
        # First call - should compute
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count[0] == 1
        
        # Second call with same args - should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count[0] == 1  # No additional call
        
        # Different args - should compute
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count[0] == 2
    
    @pytest.mark.asyncio
    async def test_async_function_caching(self):
        """Test caching async function results."""
        call_count = [0]
        
        @async_cached()
        async def expensive_async_function(x, y):
            call_count[0] += 1
            await asyncio.sleep(0.01)
            return x * y
        
        # First call
        result1 = await expensive_async_function(3, 4)
        assert result1 == 12
        assert call_count[0] == 1
        
        # Cached call
        result2 = await expensive_async_function(3, 4)
        assert result2 == 12
        assert call_count[0] == 1  # Still 1


@pytest.mark.xwsystem_integration
class TestCacheWarming:
    """Test cache warming scenarios."""
    
    def test_preload_cache_on_startup(self):
        """Test preloading cache with data on startup."""
        cache = LRUCache(capacity=100)
        
        # Simulate database loader
        def load_from_db(key):
            # Simulate DB query
            return f"db_value_for_{key}"
        
        # Warm cache with important keys
        important_keys = [f"key_{i}" for i in range(20)]
        loaded = warm_cache(
            cache=cache,
            loader=load_from_db,
            keys=important_keys,
            strategy=PreloadWarmingStrategy()
        )
        
        assert loaded == 20
        assert cache.size() == 20
        
        # Verify all keys loaded
        for key in important_keys:
            assert cache.get(key) is not None


@pytest.mark.xwsystem_integration
class TestObservableCacheEvents:
    """Test observable cache with event hooks."""
    
    def test_event_hooks_triggered(self):
        """Test that event hooks are called correctly."""
        cache = ObservableLRUCache(capacity=10)
        
        events_log = []
        
        def on_hit(event, key, value):
            events_log.append(('HIT', key, value))
        
        def on_miss(event, key):
            events_log.append(('MISS', key))
        
        def on_put(event, key, value):
            events_log.append(('PUT', key, value))
        
        # Register hooks
        cache.on(CacheEvent.HIT, on_hit)
        cache.on(CacheEvent.MISS, on_miss)
        cache.on(CacheEvent.PUT, on_put)
        
        # Operations
        cache.put("k1", "v1")
        cache.get("k1")
        cache.get("k2")
        
        # Verify events
        assert ('PUT', 'k1', 'v1') in events_log
        assert ('HIT', 'k1', 'v1') in events_log
        assert ('MISS', 'k2') in events_log


@pytest.mark.xwsystem_integration
class TestPerformanceOptimizations:
    """Test end-to-end performance optimizations."""
    
    def test_optimized_vs_naive_lfu(self):
        """
        Compare optimized O(1) LFU vs naive O(n) LFU.
        
        Optimized version should be significantly faster for evictions.
        """
        from exonware.xwsystem.caching.lfu_cache import LFUCache
        
        # Naive LFU (O(n) eviction)
        naive_cache = LFUCache(capacity=1000)
        for i in range(1000):
            naive_cache.put(f"key_{i}", f"value_{i}")
        
        start = time.perf_counter()
        for i in range(1000, 1100):
            naive_cache.put(f"key_{i}", f"value_{i}")
        naive_time = time.perf_counter() - start
        
        # Optimized LFU (O(1) eviction)
        optimized_cache = OptimizedLFUCache(capacity=1000)
        for i in range(1000):
            optimized_cache.put(f"key_{i}", f"value_{i}")
        
        start = time.perf_counter()
        for i in range(1000, 1100):
            optimized_cache.put(f"key_{i}", f"value_{i}")
        optimized_time = time.perf_counter() - start
        
        # Optimized should be faster (at least not slower)
        speedup = naive_time / optimized_time if optimized_time > 0 else 1.0
        
        print(f"\nNaive LFU: {naive_time:.4f}s")
        print(f"Optimized LFU: {optimized_time:.4f}s")
        print(f"Speedup: {speedup:.2f}x")
        
        # Optimized should be at least as fast (ideally much faster)
        assert optimized_time <= naive_time * 1.2, (
            f"Optimized LFU not faster: {speedup:.2f}x speedup"
        )

