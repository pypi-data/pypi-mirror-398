"""
#exonware/xwsystem/tests/2.integration/caching/test_end_to_end.py

Integration tests for end-to-end caching scenarios.

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
from exonware.xwsystem.caching.lru_cache import LRUCache
from exonware.xwsystem.caching.lfu_cache import LFUCache
from exonware.xwsystem.caching.lfu_optimized import OptimizedLFUCache
from exonware.xwsystem.caching.secure_cache import SecureLRUCache
from exonware.xwsystem.caching.decorators import xwcached  # New XW-prefixed decorator


@pytest.mark.xwsystem_integration
@pytest.mark.xwsystem_caching
class TestCachingIntegration:
    """Integration tests for caching workflows."""
    
    def test_large_dataset_caching(self, integration_cache_data):
        """
        Given: A large dataset with 500 entries
        When: Storing in cache with eviction
        Then: Cache manages data correctly with proper eviction
        """
        cache = LRUCache(capacity=100)
        
        # Store large dataset
        for key, value in integration_cache_data.items():
            cache.put(key, value)
        
        # Cache should be at capacity
        assert cache.size() <= 100
        
        # Recent entries should still be there
        assert cache.get('key_499') is not None
    
    def test_multi_threaded_cache_access(self):
        """
        Given: Multiple threads accessing cache
        When: Concurrent reads and writes
        Then: No data corruption or race conditions
        """
        cache = LRUCache(capacity=1000)
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(100):
                    key = f'thread_{thread_id}_key_{i}'
                    cache.put(key, f'value_{i}')
                    result = cache.get(key)
                    assert result == f'value_{i}'
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_decorator_with_real_computation(self):
        """
        Given: A computationally expensive function
        When: Decorated with @xwcached
        Then: Subsequent calls are fast
        """
        call_count = [0]
        
        @xwcached()
        def expensive_computation(n):
            call_count[0] += 1
            # Simulate expensive computation
            result = sum(i * i for i in range(n))
            return result
        
        # First call - expensive
        start = time.time()
        result1 = expensive_computation(1000)
        elapsed1 = time.time() - start
        
        # Second call - cached (should be faster)
        start = time.time()
        result2 = expensive_computation(1000)
        elapsed2 = time.time() - start
        
        assert result1 == result2
        assert call_count[0] == 1  # Function only called once (cached on second call)
        # Cached call should be faster or equal (when operations are very fast, both may be 0.0)
        assert elapsed2 <= elapsed1, f"Cached call should be faster or equal: {elapsed2} <= {elapsed1}"
    
    def test_cache_migration_between_types(self):
        """
        Given: Data in one cache type
        When: Migrating to another cache type
        Then: Data is preserved correctly
        """
        # Start with LRU cache
        lru_cache = LRUCache(capacity=100)
        for i in range(50):
            lru_cache.put(f'key_{i}', f'value_{i}')
        
        # Migrate to LFU cache
        lfu_cache = LFUCache(capacity=100)
        for key, value in lru_cache.items():
            lfu_cache.put(key, value)
        
        # Verify data migrated
        assert lfu_cache.size() == 50
        for i in range(50):
            assert lfu_cache.get(f'key_{i}') == f'value_{i}'
    
    @pytest.mark.xwsystem_security
    def test_secure_cache_end_to_end(self):
        """
        Given: Secure cache with validation
        When: Processing untrusted input
        Then: Security features work together
        """
        cache = SecureLRUCache(
            capacity=100,
            enable_integrity=True,
            enable_rate_limit=True
        )
        
        # Normal operation
        cache.put('user_data', {'email': 'user@example.com'})
        result = cache.get('user_data')
        
        assert result is not None
        
        # Security stats
        stats = cache.get_security_stats()
        assert stats['enable_integrity'] is True
        assert stats['enable_rate_limit'] is True
    
    @pytest.mark.xwsystem_performance
    @pytest.mark.slow
    def test_performance_under_load(self):
        """
        Given: High-volume cache operations
        When: Processing 10,000 operations
        Then: Performance remains acceptable
        """
        cache = OptimizedLFUCache(capacity=5000)
        
        start = time.time()
        
        # Perform 10,000 operations
        for i in range(10000):
            cache.put(f'key_{i}', f'value_{i}')
            if i % 2 == 0:
                cache.get(f'key_{i}')
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0
        
        # Verify stats
        stats = cache.get_stats()
        assert stats['size'] <= 5000

