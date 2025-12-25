#!/usr/bin/env python3
"""
Advance extensibility tests for caching module.
Priority #5: Extensibility Excellence

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
from exonware.xwsystem.caching.pluggable_cache import PluggableCache
from exonware.xwsystem.caching.eviction_strategies import (
    LRUEvictionStrategy,
    LFUEvictionStrategy,
    FIFOEvictionStrategy,
    RandomEvictionStrategy,
)
from exonware.xwsystem.caching.observable_cache import ObservableLRUCache
from exonware.xwsystem.caching.events import CacheEvent
from exonware.xwsystem.caching.decorators import cached


@pytest.mark.xwsystem_advance
@pytest.mark.xwsystem_extensibility
class TestCachingExtensibilityExcellence:
    """Extensibility excellence tests for caching."""
    
    def test_custom_eviction_strategy(self):
        """Test that custom eviction strategies can be implemented."""
        from exonware.xwsystem.caching.eviction_strategies import AEvictionStrategy
        
        class CustomEvictionStrategy(AEvictionStrategy):
            """Custom strategy: evict keys starting with 'temp_'."""
            
            def select_victim(self, cache_items):
                # Prefer evicting temporary keys
                for key, value, metadata in cache_items:
                    if str(key).startswith('temp_'):
                        return key
                # Fallback to first item
                return cache_items[0][0] if cache_items else None
            
            def on_access(self, key, metadata):
                pass
            
            def on_insert(self, key, value, metadata):
                pass
            
            def on_delete(self, key):
                pass
            
            def get_strategy_name(self):
                return "CUSTOM_TEMP"
        
        # Use custom strategy
        cache = PluggableCache(capacity=3, strategy=CustomEvictionStrategy())
        
        cache.put("temp_1", "value1")
        cache.put("perm_1", "value2")
        cache.put("perm_2", "value3")
        cache.put("perm_3", "value4")  # Should evict temp_1
        
        # temp_1 should be evicted
        assert cache.get("temp_1") is None
        # Permanent keys should remain
        assert cache.get("perm_1") is not None
    
    def test_runtime_strategy_switching(self):
        """Test that eviction strategy can be changed at runtime."""
        cache = PluggableCache(capacity=10, strategy=LRUEvictionStrategy())
        
        # Add items with LRU
        for i in range(5):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Switch to LFU
        cache.set_strategy(LFUEvictionStrategy())
        
        # Add more items
        for i in range(5, 10):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Verify strategy changed
        assert cache.get_strategy().get_strategy_name() == "LFU"
        
        stats = cache.get_stats()
        assert stats['strategy_switches'] == 1
    
    def test_event_hooks_customization(self):
        """Test that event hooks allow custom behaviors."""
        cache = ObservableLRUCache(capacity=10)
        
        # Custom metrics tracking
        metrics = {'total_bytes_cached': 0}
        
        def track_bytes(event, key, value):
            import sys
            metrics['total_bytes_cached'] += sys.getsizeof(value)
        
        cache.on(CacheEvent.PUT, track_bytes)
        
        # Add items
        cache.put("k1", "x" * 100)
        cache.put("k2", "y" * 200)
        
        # Custom metric should be updated
        assert metrics['total_bytes_cached'] > 0
    
    def test_decorator_customization(self):
        """Test that decorators support custom key builders and conditions."""
        call_count = [0]
        
        # Custom key builder
        def custom_key_builder(func, args, kwargs):
            return f"custom:{args[0]}"
        
        # Conditional caching
        def should_cache(args, kwargs):
            return args[0] > 0
        
        @cached(
            key_builder=custom_key_builder,
            condition=should_cache
        )
        def function_to_cache(x):
            call_count[0] += 1
            return x * 2
        
        # Positive args should be cached
        result1 = function_to_cache(5)
        result2 = function_to_cache(5)
        assert call_count[0] == 1  # Only called once
        
        # Negative args should not be cached
        result3 = function_to_cache(-1)
        result4 = function_to_cache(-1)
        assert call_count[0] == 3  # Called twice (original + 2 non-cached)
    
    def test_easy_subclassing(self):
        """Test that caches are easy to extend via subclassing."""
        from exonware.xwsystem.caching import LRUCache
        
        class LoggingLRUCache(LRUCache):
            """Custom cache that logs all operations."""
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.operation_log = []
            
            def put(self, key, value):
                self.operation_log.append(('PUT', key, value))
                super().put(key, value)
            
            def get(self, key, default=None):
                value = super().get(key, default)
                self.operation_log.append(('GET', key, value))
                return value
        
        # Use custom cache
        cache = LoggingLRUCache(capacity=10)
        cache.put("key", "value")
        cache.get("key")
        
        # Verify logging works
        assert len(cache.operation_log) == 2
        assert cache.operation_log[0] == ('PUT', 'key', 'value')
        assert cache.operation_log[1][0] == 'GET'

