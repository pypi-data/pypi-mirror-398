#!/usr/bin/env python3
"""
Advance performance tests for caching module.
Priority #4: Performance Excellence

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import time
from exonware.xwsystem.caching import LRUCache, LFUCache
from exonware.xwsystem.caching.lfu_optimized import OptimizedLFUCache
from exonware.xwsystem.caching.memory_bounded import MemoryBoundedLRUCache


@pytest.mark.xwsystem_advance
@pytest.mark.xwsystem_performance
class TestCachingPerformanceExcellence:
    """Performance excellence tests for caching."""
    
    def test_o1_complexity_verification(self):
        """Verify O(1) complexity for critical operations."""
        cache = OptimizedLFUCache(capacity=10000)
        
        # Fill cache
        for i in range(10000):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Measure get time - should be constant regardless of position
        timings = []
        for key_num in [0, 5000, 9999]:  # Beginning, middle, end
            start = time.perf_counter()
            for _ in range(100):
                cache.get(f"key_{key_num}")
            elapsed = time.perf_counter() - start
            timings.append(elapsed)
        
        # All timings should be similar (within 50% of each other)
        min_time = min(timings)
        max_time = max(timings)
        assert max_time < min_time * 1.5, f"Non-constant time complexity detected: {timings}"
    
    def test_eviction_performance_at_scale(self):
        """Test eviction performance doesn't degrade at scale."""
        small_cache = OptimizedLFUCache(capacity=100)
        large_cache = OptimizedLFUCache(capacity=10000)
        
        # Fill caches
        for i in range(100):
            small_cache.put(f"key_{i}", f"value_{i}")
        for i in range(10000):
            large_cache.put(f"key_{i}", f"value_{i}")
        
        # Measure small cache eviction
        start = time.perf_counter()
        for i in range(100, 200):
            small_cache.put(f"key_{i}", f"value_{i}")
        small_time = time.perf_counter() - start
        
        # Measure large cache eviction
        start = time.perf_counter()
        for i in range(10000, 10100):
            large_cache.put(f"key_{i}", f"value_{i}")
        large_time = time.perf_counter() - start
        
        # Large cache should not be significantly slower
        # Allow 2x overhead, but not 100x (which would indicate O(n))
        assert large_time < small_time * 2, (
            f"Eviction time grows too much: small={small_time:.4f}s, large={large_time:.4f}s"
        )
    
    def test_throughput_benchmarks(self):
        """Test cache throughput meets benchmarks."""
        cache = LRUCache(capacity=1000)
        
        # Benchmark put operations
        start = time.perf_counter()
        for i in range(10000):
            cache.put(f"key_{i % 1000}", f"value_{i}")
        put_time = time.perf_counter() - start
        put_ops_per_sec = 10000 / put_time
        
        # Should achieve >500K ops/sec
        assert put_ops_per_sec > 500000, (
            f"Put throughput too low: {put_ops_per_sec:.0f} ops/sec"
        )
        
        # Benchmark get operations
        start = time.perf_counter()
        for i in range(10000):
            cache.get(f"key_{i % 1000}")
        get_time = time.perf_counter() - start
        get_ops_per_sec = 10000 / get_time
        
        # Should achieve >500K ops/sec
        assert get_ops_per_sec > 500000, (
            f"Get throughput too low: {get_ops_per_sec:.0f} ops/sec"
        )
    
    def test_memory_efficiency(self):
        """Test memory usage is reasonable."""
        cache = MemoryBoundedLRUCache(
            capacity=1000,
            memory_budget_mb=10.0
        )
        
        # Fill with 1KB values
        for i in range(1000):
            cache.put(f"key_{i}", "x" * 1024)
        
        # Get memory stats
        memory_stats = cache.get_memory_stats()
        
        # Should not exceed budget
        assert memory_stats['current_memory_bytes'] <= memory_stats['memory_budget_bytes']
        
        # Should be using memory efficiently
        assert memory_stats['memory_used_pct'] > 50  # At least 50% utilization
    
    def test_batch_operations_speedup(self):
        """Test that batch operations are faster than individual calls."""
        cache = LRUCache(capacity=1000)
        
        items = {f"key_{i}": f"value_{i}" for i in range(100)}
        
        # Measure individual puts
        start = time.perf_counter()
        for key, value in items.items():
            cache.put(key, value)
        individual_time = time.perf_counter() - start
        
        # Clear cache
        cache.clear()
        
        # Measure batch put
        start = time.perf_counter()
        cache.put_many(items)
        batch_time = time.perf_counter() - start
        
        # Batch should be at least as fast (ideally faster)
        # Allow some overhead, but batch shouldn't be slower
        assert batch_time <= individual_time * 1.2, (
            f"Batch operations not efficient: "
            f"batch={batch_time:.4f}s, individual={individual_time:.4f}s"
        )

