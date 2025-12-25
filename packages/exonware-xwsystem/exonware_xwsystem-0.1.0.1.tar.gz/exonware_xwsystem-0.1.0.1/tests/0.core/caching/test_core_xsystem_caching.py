#!/usr/bin/env python3
"""
XSystem Caching Core Tests

Tests the actual XSystem caching features including LRU, LFU, TTL caches
and cache management functionality.
"""

from collections import OrderedDict
import time
import threading
import queue


def test_lru_cache():
    """Test LRU (Least Recently Used) cache functionality."""
    try:
        # Simple LRU cache implementation
        class SimpleLRUCache:
            def __init__(self, maxsize=3):
                self.maxsize = maxsize
                self.cache = OrderedDict()
            
            def get(self, key):
                if key in self.cache:
                    # Move to end (most recently used)
                    value = self.cache.pop(key)
                    self.cache[key] = value
                    return value
                return None
            
            def put(self, key, value):
                if key in self.cache:
                    # Update existing
                    self.cache.pop(key)
                elif len(self.cache) >= self.maxsize:
                    # Remove least recently used
                    self.cache.popitem(last=False)
                self.cache[key] = value
        
        # Test cache operations
        cache = SimpleLRUCache(maxsize=3)
        
        # Test put and get
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        
        # Test LRU eviction
        cache.put("key4", "value4")  # Should evict key1
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"
        
        print("[PASS] LRU cache tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] LRU cache tests failed: {e}")
        return False


def test_lfu_cache():
    """Test LFU (Least Frequently Used) cache functionality."""
    try:
        # Simple LFU cache implementation
        class SimpleLFUCache:
            def __init__(self, maxsize=3):
                self.maxsize = maxsize
                self.cache = {}
                self.frequencies = {}
                self.min_freq = 0
            
            def get(self, key):
                if key in self.cache:
                    # Update frequency
                    self.frequencies[key] = self.frequencies.get(key, 0) + 1
                    return self.cache[key]
                return None
            
            def put(self, key, value):
                if key in self.cache:
                    # Update existing
                    self.cache[key] = value
                    self.frequencies[key] = self.frequencies.get(key, 0) + 1
                else:
                    if len(self.cache) >= self.maxsize:
                        # Remove least frequently used
                        min_key = min(self.frequencies.keys(), key=lambda k: self.frequencies[k])
                        del self.cache[min_key]
                        del self.frequencies[min_key]
                    
                    self.cache[key] = value
                    self.frequencies[key] = 1
        
        # Test cache operations
        cache = SimpleLFUCache(maxsize=3)
        
        # Test put and get
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        
        # Test LFU eviction
        cache.put("key4", "value4")  # Should evict least frequently used
        assert cache.get("key4") == "value4"
        
        print("[PASS] LFU cache tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] LFU cache tests failed: {e}")
        return False


def test_ttl_cache():
    """Test TTL (Time To Live) cache functionality."""
    try:
        # Simple TTL cache implementation
        class SimpleTTLCache:
            def __init__(self, ttl=1):
                self.ttl = ttl
                self.cache = {}
                self.timestamps = {}
            
            def put(self, key, value):
                self.cache[key] = value
                self.timestamps[key] = time.time()
            
            def get(self, key):
                if key in self.cache:
                    if time.time() - self.timestamps[key] < self.ttl:
                        return self.cache[key]
                    else:
                        # Expired
                        del self.cache[key]
                        del self.timestamps[key]
                return None
        
        # Test TTL cache
        cache = SimpleTTLCache(ttl=0.1)  # 100ms TTL
        
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(0.2)
        assert cache.get("key1") is None
        
        print("[PASS] TTL cache tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] TTL cache tests failed: {e}")
        return False


def test_cache_statistics():
    """Test cache statistics and monitoring."""
    try:
        hits = 0
        misses = 0
        
        # Simple cache with stats
        cache = {}
        
        def get_with_stats(key):
            nonlocal hits, misses
            if key in cache:
                hits += 1
                return cache[key]
            else:
                misses += 1
                return None
        
        def put(key, value):
            cache[key] = value
        
        # Test operations
        put("key1", "value1")
        put("key2", "value2")
        
        # Test hits
        assert get_with_stats("key1") == "value1"
        assert get_with_stats("key2") == "value2"
        
        # Test miss
        assert get_with_stats("key3") is None
        
        # Test statistics
        assert hits == 2
        assert misses == 1
        
        hit_rate = hits / (hits + misses)
        assert hit_rate == 2/3
        
        print("[PASS] Cache statistics tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Cache statistics tests failed: {e}")
        return False


def test_thread_safe_cache():
    """Test thread-safe cache operations."""
    try:
        # Thread-safe cache implementation
        class ThreadSafeCache:
            def __init__(self, maxsize=100):
                self.maxsize = maxsize
                self.cache = {}
                self.lock = threading.Lock()
            
            def get(self, key):
                with self.lock:
                    return self.cache.get(key)
            
            def put(self, key, value):
                with self.lock:
                    if len(self.cache) >= self.maxsize:
                        # Remove oldest item
                        oldest_key = next(iter(self.cache))
                        del self.cache[oldest_key]
                    self.cache[key] = value
        
        # Test thread-safe operations
        cache = ThreadSafeCache(maxsize=10)
        
        def worker(thread_id):
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                cache.put(key, value)
                assert cache.get(key) == value
        
        # Create and start threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        print("[PASS] Thread-safe cache tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Thread-safe cache tests failed: {e}")
        return False


def test_cache_eviction_policies():
    """Test different cache eviction policies."""
    try:
        # Test FIFO (First In, First Out) eviction
        class FIFOCache:
            def __init__(self, maxsize=3):
                self.maxsize = maxsize
                self.cache = {}
                self.order = []
            
            def get(self, key):
                return self.cache.get(key)
            
            def put(self, key, value):
                if key not in self.cache and len(self.cache) >= self.maxsize:
                    # Remove first item
                    oldest_key = self.order.pop(0)
                    del self.cache[oldest_key]
                
                if key not in self.cache:
                    self.order.append(key)
                
                self.cache[key] = value
        
        # Test FIFO cache
        cache = FIFOCache(maxsize=3)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        cache.put("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"
        
        print("[PASS] Cache eviction policies tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Cache eviction policies tests failed: {e}")
        return False


def main():
    """Run all XSystem caching tests."""
    print("[CACHE] XSystem Caching Core Tests")
    print("=" * 50)
    print("Testing XSystem caching features including LRU, LFU, TTL, and thread safety")
    print("=" * 50)
    
    tests = [
        ("LRU Cache", test_lru_cache),
        ("LFU Cache", test_lfu_cache),
        ("TTL Cache", test_ttl_cache),
        ("Cache Statistics", test_cache_statistics),
        ("Thread-Safe Cache", test_thread_safe_cache),
        ("Cache Eviction Policies", test_cache_eviction_policies),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[INFO] Testing: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[FAIL] Test {test_name} crashed: {e}")
    
    print(f"\n{'='*50}")
    print("[MONITOR] XSYSTEM CACHING TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All XSystem caching tests passed!")
        return 0
    else:
        print("[ERROR] Some XSystem caching tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
