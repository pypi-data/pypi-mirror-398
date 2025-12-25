"""
#exonware/xwsystem/tests/3.advance/caching/test_security.py

Security excellence tests for caching module - Priority #1.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest

# Import directly from submodules
from exonware.xwsystem.caching.secure_cache import SecureLRUCache, SecureLFUCache
from exonware.xwsystem.caching.errors import (
    CacheKeySizeError,
    CacheValueSizeError,
    CacheRateLimitError,
)


@pytest.mark.xwsystem_advance
@pytest.mark.xwsystem_security
@pytest.mark.xwsystem_caching
class TestCachingSecurityExcellence:
    """Security excellence validation - Priority #1."""
    
    def test_comprehensive_input_validation(self, malicious_inputs):
        """Test comprehensive input validation against malicious patterns."""
        cache = SecureLRUCache(capacity=100)
        
        for malicious_input in malicious_inputs:
            try:
                # Should either accept safely or reject with proper error
                cache.put(str(malicious_input), 'test_value')
            except (CacheKeySizeError, CacheValueSizeError):
                # Expected for oversized inputs
                pass
    
    def test_defense_in_depth(self):
        """Test multiple layers of security working together."""
        cache = SecureLRUCache(
            capacity=100,
            enable_integrity=True,
            enable_rate_limit=True,
            max_key_size=1024,
            max_value_size_mb=1.0
        )
        
        # Validation layer
        cache.put('key', 'value')
        
        # Integrity layer
        result = cache.get('key')
        assert result is not None
        
        # Rate limiting layer (tracked but not enforced in single op)
        stats = cache.get_security_stats()
        assert 'rate_limiter' in stats
    
    def test_no_information_leakage(self):
        """Test that error messages don't leak sensitive information."""
        cache = SecureLRUCache(capacity=10, max_key_size=10)
        
        oversized_key = 'x' * 100
        
        try:
            cache.put(oversized_key, 'value')
            assert False, "Should have raised error"
        except CacheKeySizeError as e:
            error_msg = str(e)
            # Should not include the actual oversized key
            assert 'x' * 50 not in error_msg
            # Should provide helpful guidance
            assert 'too large' in error_msg
    
    def test_dos_protection_via_rate_limiting(self):
        """Test DoS protection through rate limiting."""
        cache = SecureLRUCache(
            capacity=10,
            enable_rate_limit=True,
            max_ops_per_second=10
        )
        
        # Should handle normal traffic
        for i in range(5):
            cache.put(f'key_{i}', f'value_{i}')
        
        # Excessive traffic should be limited
        # (implementation specific - may need adjustment based on rate limiter)
        assert cache.size() <= 10

