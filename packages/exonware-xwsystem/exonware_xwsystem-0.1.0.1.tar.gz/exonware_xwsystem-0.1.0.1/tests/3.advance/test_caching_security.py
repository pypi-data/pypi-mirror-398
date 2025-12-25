#!/usr/bin/env python3
"""
Advance security tests for caching module.
Priority #1: Security Excellence

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import threading
from exonware.xwsystem.caching.secure_cache import SecureLRUCache
from exonware.xwsystem.caching.errors import (
    CacheRateLimitError,
    CacheKeySizeError,
    CacheValueSizeError,
)


@pytest.mark.xwsystem_advance
@pytest.mark.xwsystem_security
class TestCachingSecurityExcellence:
    """Security excellence tests for caching."""
    
    def test_dos_protection_rate_limiting(self):
        """Test DoS protection via rate limiting."""
        cache = SecureLRUCache(
            capacity=100,
            enable_rate_limit=True,
            max_ops_per_second=50
        )
        
        # Normal operations should work
        for i in range(40):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Flood attempt should be blocked
        with pytest.raises(CacheRateLimitError):
            for i in range(100):
                cache.put(f"flood_{i}", "value")
    
    def test_memory_exhaustion_protection(self):
        """Test protection against memory exhaustion attacks."""
        cache = SecureLRUCache(
            capacity=10,
            max_value_size_mb=1.0,  # 1MB max
            enable_rate_limit=False
        )
        
        # Normal values should work
        cache.put("key1", "x" * 1000)  # 1KB
        
        # Excessive value should be rejected
        with pytest.raises(CacheValueSizeError):
            huge_value = "x" * (2 * 1024 * 1024)  # 2MB
            cache.put("key2", huge_value)
    
    def test_cache_key_injection_protection(self):
        """Test protection against key injection attacks."""
        cache = SecureLRUCache(
            capacity=10,
            max_key_size=100,
            enable_rate_limit=False
        )
        
        # Normal keys work
        cache.put("normal_key", "value")
        
        # Oversized keys blocked
        with pytest.raises(CacheKeySizeError):
            cache.put("x" * 10000, "value")
    
    def test_concurrent_access_safety(self):
        """Test that concurrent access doesn't create race conditions."""
        cache = SecureLRUCache(capacity=1000, enable_rate_limit=False)
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(100):
                    key = f"w{worker_id}_k{i}"
                    cache.put(key, f"value_{i}")
                    value = cache.get(key)
                    assert value is not None, f"Lost value for {key}"
            except Exception as e:
                errors.append(str(e))
        
        # Run 50 threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No errors should occur
        assert len(errors) == 0, f"Race conditions detected: {errors[:5]}"
    
    def test_defense_in_depth(self):
        """Test that multiple security layers work together."""
        cache = SecureLRUCache(
            capacity=10,
            enable_integrity=True,
            enable_rate_limit=True,
            max_ops_per_second=100,
            max_key_size=256,
            max_value_size_mb=5.0
        )
        
        # All security features should be active
        security_stats = cache.get_security_stats()
        assert security_stats['enable_integrity'] is True
        assert security_stats['enable_rate_limit'] is True
        assert 'rate_limiter' in security_stats
        
        # Normal operations should work with all protections
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"

