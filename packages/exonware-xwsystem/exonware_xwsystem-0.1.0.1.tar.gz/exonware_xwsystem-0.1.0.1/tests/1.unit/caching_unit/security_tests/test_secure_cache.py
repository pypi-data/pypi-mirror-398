"""
#exonware/xwsystem/tests/1.unit/caching_unit/security_tests/test_secure_cache.py

Unit tests for secure cache implementations - Security Priority #1.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest

# Import directly from submodules
from exonware.xwsystem.caching.secure_cache import SecureLRUCache
from exonware.xwsystem.caching.errors import (
    CacheKeySizeError,
    CacheValueSizeError,
    CacheRateLimitError,
)


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
@pytest.mark.xwsystem_caching
class TestSecureLRUCache:
    """Security tests for SecureLRUCache."""
    
    def test_validates_normal_input(self):
        """Test secure cache accepts normal input."""
        cache = SecureLRUCache(capacity=10)
        
        cache.put('valid_key', 'valid_value')
        result = cache.get('valid_key')
        
        assert result == 'valid_value'
    
    def test_rejects_oversized_key(self):
        """Test secure cache rejects oversized keys."""
        cache = SecureLRUCache(capacity=10, max_key_size=100)
        
        oversized_key = 'a' * 200  # 200 bytes > 100 byte limit
        
        with pytest.raises(CacheKeySizeError, match="too large"):
            cache.put(oversized_key, 'value')
    
    def test_rejects_oversized_value(self):
        """Test secure cache rejects oversized values."""
        cache = SecureLRUCache(capacity=10, max_value_size_mb=0.001)  # 1KB limit
        
        # Create value > 1KB
        oversized_value = 'x' * 2000
        
        with pytest.raises(CacheValueSizeError, match="too large"):
            cache.put('key', oversized_value)
    
    @pytest.mark.parametrize("malicious_key", [
        pytest.param("../../../etc/passwd", id="path_traversal"),
        pytest.param("<script>alert('xss')</script>", id="xss_attempt"),
        pytest.param("'; DROP TABLE cache; --", id="sql_injection"),
    ])
    def test_handles_malicious_keys_safely(self, malicious_key):
        """Test cache handles malicious keys safely."""
        cache = SecureLRUCache(capacity=10)
        
        # Should not crash or expose vulnerabilities
        cache.put(malicious_key, 'value')
        result = cache.get(malicious_key)
        
        assert result == 'value'  # Safely stored and retrieved
    
    def test_security_stats_tracking(self):
        """Test security statistics are tracked."""
        cache = SecureLRUCache(capacity=10)
        
        cache.put('key1', 'value1')
        
        stats = cache.get_security_stats()
        
        assert 'enable_integrity' in stats
        assert 'enable_rate_limit' in stats
        assert 'max_key_size' in stats
        assert 'max_value_size_mb' in stats

