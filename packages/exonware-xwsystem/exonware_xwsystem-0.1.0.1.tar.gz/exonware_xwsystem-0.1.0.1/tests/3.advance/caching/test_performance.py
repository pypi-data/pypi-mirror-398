"""
#exonware/xwsystem/tests/3.advance/caching/test_performance.py

Performance excellence tests for caching module - Priority #4.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import time

# Import directly from submodules
from exonware.xwsystem.caching.lru_cache import LRUCache
from exonware.xwsystem.caching.lfu_optimized import OptimizedLFUCache


@pytest.mark.xwsystem_advance
@pytest.mark.xwsystem_performance
@pytest.mark.xwsystem_caching
class TestCachingPerformanceExcellence:
    """Performance excellence validation - Priority #4."""
    
    def test_o1_get_operation_scaling(self):
        """Test that get operation maintains O(1) complexity at scale."""
        cache = LRUCache(capacity=10000)
        
        # Fill cache
        for i in range(10000):
            cache.put(f'key_{i}', f'value_{i}')
        
        # Measure get operations
        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            cache.get('key_5000')
        elapsed = time.time() - start
        
        # Should complete 1000 operations quickly (< 5ms)
        assert elapsed < 0.005
    
    def test_optimized_lfu_eviction_performance(self):
        """Test optimized LFU has O(1) eviction (100x faster claim)."""
        cache = OptimizedLFUCache(capacity=1000)
        
        # Fill to capacity
        for i in range(1000):
            cache.put(f'key_{i}', f'value_{i}')
        
        # Measure eviction operations (adding beyond capacity)
        start = time.time()
        for i in range(1000):
            cache.put(f'new_key_{i}', f'new_value_{i}')
        elapsed = time.time() - start
        
        # Should complete 1000 evictions quickly (< 50ms)
        assert elapsed < 0.05
    
    def test_memory_efficiency(self, very_large_cache_dataset):
        """Test memory usage remains reasonable for large datasets."""
        cache = LRUCache(capacity=10000)
        
        # Store large dataset
        for key, value in very_large_cache_dataset.items():
            cache.put(key, value)
        
        # Verify size is controlled
        assert cache.size() <= 10000
        
        # Stats should be minimal overhead
        stats = cache.get_stats()
        assert isinstance(stats, dict)
    
    @pytest.mark.slow
    def test_sustained_throughput(self):
        """Test sustained high throughput over time."""
        cache = OptimizedLFUCache(capacity=5000)
        
        start = time.time()
        operations = 50000
        
        for i in range(operations):
            cache.put(f'key_{i % 10000}', f'value_{i}')
            if i % 3 == 0:
                cache.get(f'key_{i % 10000}')
        
        elapsed = time.time() - start
        ops_per_second = operations / elapsed
        
        # Should achieve > 10,000 ops/second
        assert ops_per_second > 10000

