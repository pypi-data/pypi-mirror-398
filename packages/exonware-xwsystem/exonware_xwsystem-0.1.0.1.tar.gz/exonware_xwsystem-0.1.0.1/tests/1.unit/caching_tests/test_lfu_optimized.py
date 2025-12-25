#!/usr/bin/env python3
"""
Unit tests for optimized O(1) LFU cache.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import time
from exonware.xwsystem.caching.lfu_optimized import OptimizedLFUCache


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_performance
class TestOptimizedLFUCache:
    """Test optimized O(1) LFU cache."""
    
    def test_basic_operations(self):
        """Test basic get/put/delete operations."""
        cache = OptimizedLFUCache(capacity=3)
        
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        cache.put("k3", "v3")
        
        assert cache.get("k1") == "v1"
        assert cache.get("k2") == "v2"
        assert cache.get("k3") == "v3"
        assert cache.size() == 3
    
    def test_o1_eviction_performance(self):
        """Test that eviction is O(1), not O(n)."""
        cache = OptimizedLFUCache(capacity=1000)
        
        # Fill cache
        for i in range(1000):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Measure eviction time
        start = time.perf_counter()
        
        # Force 100 evictions
        for i in range(1000, 1100):
            cache.put(f"key_{i}", f"value_{i}")
        
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        
        # Should be very fast (< 10ms for 100 evictions)
        assert elapsed_ms < 10, f"Evictions too slow: {elapsed_ms:.3f}ms"
        
        # Verify evictions happened
        stats = cache.get_stats()
        assert stats['evictions'] == 100
    
    def test_lfu_eviction_policy(self):
        """Test that least frequently used items are evicted."""
        cache = OptimizedLFUCache(capacity=3)
        
        # Add items
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        cache.put("k3", "v3")
        
        # Access k1 twice, k2 once, k3 not at all
        cache.get("k1")
        cache.get("k1")
        cache.get("k2")
        
        # Add new item - should evict k3 (frequency=0 from insertion only)
        cache.put("k4", "v4")
        
        # k3 should be gone
        assert cache.get("k3") is None
        # Others should remain
        assert cache.get("k1") == "v1"
        assert cache.get("k2") == "v2"
        assert cache.get("k4") == "v4"
    
    def test_frequency_tracking(self):
        """Test that frequencies are tracked correctly."""
        cache = OptimizedLFUCache(capacity=5)
        
        cache.put("k1", "v1")
        
        # Access multiple times
        for _ in range(5):
            cache.get("k1")
        
        stats = cache.get_stats()
        # k1 should have frequency of 6 (1 from put, 5 from gets)
        assert stats['hits'] == 5
    
    def test_statistics(self):
        """Test cache statistics."""
        cache = OptimizedLFUCache(capacity=100)
        
        # Add items
        for i in range(50):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Access some items
        for i in range(25):
            cache.get(f"key_{i}")
        
        # Get non-existent items
        for i in range(50, 60):
            cache.get(f"key_{i}")
        
        stats = cache.get_stats()
        assert stats['size'] == 50
        assert stats['hits'] == 25
        assert stats['misses'] == 10
        assert stats['type'] == 'OptimizedLFU'
    
    def test_context_manager(self):
        """Test context manager support."""
        with OptimizedLFUCache(capacity=10) as cache:
            cache.put("key", "value")
            assert cache.get("key") == "value"


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_performance
class TestOptimizedLFUPerformance:
    """Performance-specific tests for optimized LFU."""
    
    def test_large_cache_performance(self):
        """Test performance with large cache."""
        cache = OptimizedLFUCache(capacity=10000)
        
        # Fill cache
        start = time.perf_counter()
        for i in range(10000):
            cache.put(f"key_{i}", f"value_{i}")
        end = time.perf_counter()
        
        fill_time = end - start
        assert fill_time < 1.0, f"Filling cache too slow: {fill_time:.2f}s"
        
        # Test get performance
        start = time.perf_counter()
        for i in range(1000):
            cache.get(f"key_{i % 10000}")
        end = time.perf_counter()
        
        get_time = end - start
        assert get_time < 0.1, f"Get operations too slow: {get_time:.3f}s"
    
    def test_eviction_scales_linearly(self):
        """Test that eviction time doesn't grow with cache size."""
        # Small cache
        small_cache = OptimizedLFUCache(capacity=100)
        for i in range(100):
            small_cache.put(f"key_{i}", f"value_{i}")
        
        start = time.perf_counter()
        for i in range(100, 200):
            small_cache.put(f"key_{i}", f"value_{i}")
        small_time = time.perf_counter() - start
        
        # Large cache
        large_cache = OptimizedLFUCache(capacity=10000)
        for i in range(10000):
            large_cache.put(f"key_{i}", f"value_{i}")
        
        start = time.perf_counter()
        for i in range(10000, 10100):
            large_cache.put(f"key_{i}", f"value_{i}")
        large_time = time.perf_counter() - start
        
        # Large cache evictions should not be 100x slower
        # Allow 3x slowdown for overhead, but not O(n) behavior
        assert large_time < small_time * 3, (
            f"Eviction time grows too much with size: "
            f"small={small_time:.4f}s, large={large_time:.4f}s"
        )

