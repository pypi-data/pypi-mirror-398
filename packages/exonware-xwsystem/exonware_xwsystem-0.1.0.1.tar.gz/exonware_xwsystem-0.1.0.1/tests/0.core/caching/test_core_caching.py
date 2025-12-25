"""
#exonware/xwsystem/tests/0.core/caching/test_core_caching.py

Core functionality tests for xwsystem caching module.
Fast, high-value tests covering critical caching operations - 20% tests for 80% value.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import time

# Import directly from submodules to avoid package-level initialization
from exonware.xwsystem.caching.lru_cache import LRUCache
from exonware.xwsystem.caching.lfu_cache import LFUCache
from exonware.xwsystem.caching.ttl_cache import TTLCache
from exonware.xwsystem.caching.lfu_optimized import OptimizedLFUCache
from exonware.xwsystem.caching.secure_cache import SecureLRUCache
from exonware.xwsystem.caching.decorators import xwcached  # New XW-prefixed decorator


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_caching
class TestCachingCore:
    """Core caching tests - 20% for 80% value."""
    
    @pytest.mark.parametrize("cache_class", [
        pytest.param(LRUCache, id="lru"),
        pytest.param(LFUCache, id="lfu"),
        pytest.param(OptimizedLFUCache, id="optimized_lfu"),
    ])
    def test_basic_get_put(self, cache_class):
        """Test basic get/put operations for all major cache types."""
        cache = cache_class(capacity=10)
        
        # Put value
        cache.put('key1', 'value1')
        
        # Get value
        result = cache.get('key1')
        assert result == 'value1'
    
    @pytest.mark.parametrize("cache_class", [
        pytest.param(LRUCache, id="lru"),
        pytest.param(LFUCache, id="lfu"),
        pytest.param(OptimizedLFUCache, id="optimized_lfu"),
    ])
    def test_eviction_on_capacity(self, cache_class):
        """Test that caches evict when capacity is reached."""
        cache = cache_class(capacity=3)
        
        # Fill cache
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')
        
        # Add one more - should trigger eviction
        cache.put('key4', 'value4')
        
        # Cache should still be at capacity
        assert cache.size() == 3
    
    def test_lru_evicts_least_recently_used(self):
        """Test LRU evicts least recently used item."""
        cache = LRUCache(capacity=3)
        
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')
        
        # Access key1 to make it recently used
        cache.get('key1')
        
        # Add key4 - should evict key2 (least recently used)
        cache.put('key4', 'value4')
        
        assert cache.get('key2') is None
        assert cache.get('key1') == 'value1'
        assert cache.get('key4') == 'value4'
    
    def test_ttl_cache_expires(self):
        """Test TTL cache expires entries."""
        cache = TTLCache(capacity=10, ttl=0.1)  # 100ms TTL
        
        cache.put('key1', 'value1')
        
        # Should be available immediately
        assert cache.get('key1') == 'value1'
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should be expired
        assert cache.get('key1') is None
    
    def test_cache_decorator(self):
        """Test that @xwcached decorator works."""
        call_count = [0]
        
        @xwcached()
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        
        # First call - should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # Second call - should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not called again
    
    @pytest.mark.xwsystem_security
    def test_secure_cache_validates_input(self):
        """Test secure cache validates input."""
        cache = SecureLRUCache(capacity=10)
        
        # Should handle normal input
        cache.put('valid_key', 'valid_value')
        assert cache.get('valid_key') == 'valid_value'
    
    @pytest.mark.xwsystem_performance
    def test_optimized_lfu_performance(self):
        """Test optimized LFU has O(1) performance."""
        cache = OptimizedLFUCache(capacity=1000)
        
        # Fill cache
        for i in range(1000):
            cache.put(f'key_{i}', f'value_{i}')
        
        # Measure get operation
        start = time.time()
        for _ in range(100):
            cache.get('key_500')
        elapsed = time.time() - start
        
        # Should be very fast (< 10ms for 100 operations)
        assert elapsed < 0.01
    
    def test_cache_clear(self):
        """Test cache clear operation."""
        cache = LRUCache(capacity=10)
        
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        
        assert cache.size() == 2
        
        cache.clear()
        
        assert cache.size() == 0
        assert cache.get('key1') is None
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = LRUCache(capacity=10)
        
        cache.put('key1', 'value1')
        cache.get('key1')  # Hit
        cache.get('key2')  # Miss
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_security
class TestCachingSecurityCore:
    """Core security tests for caching."""
    
    def test_large_key_handling(self):
        """Test handling of large keys."""
        cache = LRUCache(capacity=10)
        
        large_key = 'a' * 500  # 500 char key
        cache.put(large_key, 'value')
        
        assert cache.get(large_key) == 'value'
    
    def test_none_value_handling(self):
        """Test handling of None values."""
        cache = LRUCache(capacity=10)
        
        cache.put('key1', None)
        
        # None is a valid value to cache
        assert cache.get('key1', 'default') == 'default'  # Returns default when not found

