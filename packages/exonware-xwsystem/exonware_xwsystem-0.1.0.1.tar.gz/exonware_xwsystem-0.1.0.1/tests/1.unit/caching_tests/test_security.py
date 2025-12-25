#!/usr/bin/env python3
"""
Unit tests for caching security features.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
import time
from exonware.xwsystem.caching.rate_limiter import RateLimiter, FixedWindowRateLimiter
from exonware.xwsystem.caching.integrity import create_secure_entry, verify_entry_integrity, CacheEntry
from exonware.xwsystem.caching.secure_cache import SecureLRUCache, SecureLFUCache
from exonware.xwsystem.caching.errors import (
    CacheRateLimitError,
    CacheIntegrityError,
    CacheValidationError,
    CacheKeySizeError,
    CacheValueSizeError,
)


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_allows_normal_operations(self):
        """Test that normal operations are allowed."""
        limiter = RateLimiter(max_ops_per_second=100)
        
        # Should allow 100 operations
        for _ in range(100):
            assert limiter.try_acquire()
    
    def test_blocks_excessive_operations(self):
        """Test that excessive operations are blocked."""
        limiter = RateLimiter(max_ops_per_second=10)
        
        # Exhaust tokens
        for _ in range(10):
            limiter.try_acquire()
        
        # Next operation should fail
        with pytest.raises(CacheRateLimitError, match="Rate limit exceeded"):
            limiter.acquire()
    
    def test_token_refill(self):
        """Test that tokens are refilled over time."""
        limiter = RateLimiter(max_ops_per_second=10, burst_capacity=5)
        
        # Use all tokens
        for _ in range(5):
            limiter.acquire()
        
        # Wait for refill
        time.sleep(0.6)  # Should refill ~6 tokens
        
        # Should be able to acquire again
        assert limiter.try_acquire()
    
    def test_statistics(self):
        """Test rate limiter statistics."""
        limiter = RateLimiter(max_ops_per_second=100)
        
        # Make some requests
        for _ in range(50):
            limiter.try_acquire()
        
        # Try to exceed limit
        for _ in range(100):
            limiter.try_acquire()
        
        stats = limiter.get_stats()
        assert stats['total_requests'] > 0
        assert stats['rejected_requests'] > 0


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
class TestIntegrityVerification:
    """Test cache integrity verification."""
    
    def test_secure_entry_creation(self):
        """Test creating secure cache entries with checksums."""
        entry = create_secure_entry("key1", "value1", created_at=time.time())
        
        assert entry.key == "key1"
        assert entry.value == "value1"
        assert len(entry.checksum) > 0
        assert entry.access_count == 0
    
    def test_integrity_verification_passes(self):
        """Test that integrity verification passes for valid entries."""
        entry = create_secure_entry("key1", "value1", created_at=time.time())
        
        # Should verify successfully
        assert verify_entry_integrity(entry) is True
    
    def test_integrity_verification_fails_on_tampering(self):
        """Test that integrity verification detects tampering."""
        entry = create_secure_entry("key1", "value1", created_at=time.time())
        
        # Tamper with value
        entry.value = "tampered_value"
        
        # Verification should fail
        with pytest.raises(CacheIntegrityError, match="Integrity check failed"):
            verify_entry_integrity(entry)
    
    def test_tampered_checksum_detected(self):
        """Test that checksum tampering is detected."""
        entry = create_secure_entry("key1", "value1", created_at=time.time())
        
        # Tamper with checksum
        entry.checksum = "fake_checksum_12345"
        
        # Verification should fail
        with pytest.raises(CacheIntegrityError):
            verify_entry_integrity(entry)


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
class TestSecureLRUCache:
    """Test secure LRU cache."""
    
    def test_validates_key_size(self):
        """Test that oversized keys are rejected."""
        cache = SecureLRUCache(capacity=10, max_key_size=100)
        
        # Normal key should work
        cache.put("normal_key", "value")
        assert cache.get("normal_key") == "value"
        
        # Oversized key should be rejected
        large_key = "x" * 1000
        with pytest.raises(CacheKeySizeError):
            cache.put(large_key, "value")
    
    def test_validates_value_size(self):
        """Test that oversized values are rejected."""
        cache = SecureLRUCache(capacity=10, max_value_size_mb=0.001)  # 1KB
        
        # Small value should work
        cache.put("key", "small_value")
        
        # Large value should be rejected
        large_value = "x" * 10000  # ~10KB
        with pytest.raises(CacheValueSizeError):
            cache.put("key2", large_value)
    
    def test_rate_limiting(self):
        """Test rate limiting prevents flooding."""
        cache = SecureLRUCache(
            capacity=100,
            enable_rate_limit=True,
            max_ops_per_second=10
        )
        
        # Should allow initial operations
        for i in range(10):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Excessive operations should be blocked
        with pytest.raises(CacheRateLimitError):
            for i in range(20):
                cache.put(f"flood_{i}", f"value_{i}")
    
    def test_integrity_checking(self):
        """Test integrity checking with secure cache."""
        cache = SecureLRUCache(
            capacity=10,
            enable_integrity=True,
            enable_rate_limit=False  # Disable for test simplicity
        )
        
        # Put value
        cache.put("key1", "value1")
        
        # Get should work
        value = cache.get("key1")
        assert value == "value1"
        
        # Statistics should track integrity violations
        stats = cache.get_security_stats()
        assert stats['integrity_violations'] == 0
    
    def test_security_stats(self):
        """Test security statistics reporting."""
        cache = SecureLRUCache(
            capacity=10,
            enable_integrity=True,
            enable_rate_limit=True
        )
        
        stats = cache.get_security_stats()
        
        assert 'enable_integrity' in stats
        assert 'enable_rate_limit' in stats
        assert 'rate_limiter' in stats
        assert stats['enable_integrity'] is True
        assert stats['enable_rate_limit'] is True


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security  
class TestSecurityDefenseInDepth:
    """Test defense-in-depth security approach."""
    
    def test_multiple_security_layers(self):
        """Test that all security layers work together."""
        cache = SecureLRUCache(
            capacity=10,
            enable_integrity=True,
            enable_rate_limit=True,
            max_ops_per_second=50,
            max_key_size=100,
            max_value_size_mb=1.0
        )
        
        # Normal operation should work
        cache.put("key", "value")
        assert cache.get("key") == "value"
        
        # All security checks should be enforced
        stats = cache.get_security_stats()
        assert stats['enable_integrity'] is True
        assert stats['enable_rate_limit'] is True
    
    def test_malicious_input_handling(self):
        """Test handling of potentially malicious inputs."""
        cache = SecureLRUCache(capacity=10, enable_rate_limit=False)
        
        malicious_inputs = [
            # Large keys
            ("x" * 10000, "value"),
            # Large values  
            ("key", "x" * (11 * 1024 * 1024)),
        ]
        
        for key, value in malicious_inputs:
            with pytest.raises((CacheKeySizeError, CacheValueSizeError)):
                cache.put(key, value)

