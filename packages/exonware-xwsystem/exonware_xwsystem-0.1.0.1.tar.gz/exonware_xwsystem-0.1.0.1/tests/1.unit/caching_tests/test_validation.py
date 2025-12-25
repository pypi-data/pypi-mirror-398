#!/usr/bin/env python3
"""
Unit tests for caching validation module.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
from exonware.xwsystem.caching.validation import (
    validate_cache_key,
    validate_cache_value,
    sanitize_key,
    validate_ttl,
    validate_capacity,
)
from exonware.xwsystem.caching.errors import (
    CacheValidationError,
    CacheKeySizeError,
    CacheValueSizeError,
)


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
class TestCacheKeyValidation:
    """Test cache key validation."""
    
    def test_valid_keys(self):
        """Test that valid keys pass validation."""
        valid_keys = ["key", 123, ("tuple", "key"), 3.14]
        
        for key in valid_keys:
            validate_cache_key(key)  # Should not raise
    
    def test_none_key_rejected(self):
        """Test that None key is rejected by default."""
        with pytest.raises(CacheValidationError, match="cannot be None"):
            validate_cache_key(None)
    
    def test_none_key_allowed_when_configured(self):
        """Test that None key is allowed when configured."""
        validate_cache_key(None, allow_none=True)  # Should not raise
    
    def test_non_hashable_key_rejected(self):
        """Test that non-hashable keys are rejected."""
        with pytest.raises(CacheValidationError, match="must be hashable"):
            validate_cache_key(['list', 'is', 'not', 'hashable'])
    
    def test_large_key_rejected(self):
        """Test that oversized keys are rejected."""
        large_key = "x" * 10000  # 10KB key
        
        with pytest.raises(CacheKeySizeError, match="too large"):
            validate_cache_key(large_key, max_size=1024)
    
    def test_error_message_includes_example(self):
        """Test that error messages include helpful examples."""
        with pytest.raises(CacheValidationError) as exc:
            validate_cache_key({'dict': 'not hashable'})
        
        error_msg = str(exc.value)
        assert "hashable" in error_msg.lower()
        assert "str" in error_msg or "int" in error_msg  # Includes valid types


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
class TestCacheValueValidation:
    """Test cache value validation."""
    
    def test_normal_values_accepted(self):
        """Test that normal-sized values pass validation."""
        values = ["string", 123, {"dict": "value"}, ["list", "values"]]
        
        for value in values:
            validate_cache_value(value)  # Should not raise
    
    def test_large_value_rejected(self):
        """Test that oversized values are rejected."""
        large_value = "x" * (11 * 1024 * 1024)  # 11MB
        
        with pytest.raises(CacheValueSizeError, match="too large"):
            validate_cache_value(large_value, max_size_mb=10)
    
    def test_custom_size_limit(self):
        """Test custom size limits work."""
        value = "x" * 1024  # 1KB
        
        # Should pass with 1MB limit
        validate_cache_value(value, max_size_mb=1)
        
        # Should fail with 0.0001MB limit
        with pytest.raises(CacheValueSizeError):
            validate_cache_value(value, max_size_mb=0.0001)


@pytest.mark.xwsystem_unit
class TestKeySanitization:
    """Test key sanitization."""
    
    def test_string_keys_unchanged(self):
        """Test that string keys pass through unchanged."""
        assert sanitize_key("my_key") == "my_key"
    
    def test_int_keys_converted(self):
        """Test that int keys are converted to strings."""
        assert sanitize_key(123) == "123"
    
    def test_tuple_keys_converted(self):
        """Test that tuple keys are converted to strings."""
        result = sanitize_key(("a", "b", "c"))
        assert isinstance(result, str)
        assert "a" in result
    
    def test_bytes_keys_decoded(self):
        """Test that bytes keys are decoded."""
        result = sanitize_key(b"bytes_key")
        assert result == "bytes_key"


@pytest.mark.xwsystem_unit
class TestTTLValidation:
    """Test TTL validation."""
    
    def test_valid_ttl_accepted(self):
        """Test that valid TTL values are accepted."""
        validate_ttl(60.0)
        validate_ttl(300)
        validate_ttl(3600.0)
    
    def test_negative_ttl_rejected(self):
        """Test that negative TTL is rejected."""
        with pytest.raises(CacheValidationError, match="at least"):
            validate_ttl(-1.0)
    
    def test_excessive_ttl_rejected(self):
        """Test that excessively large TTL is rejected."""
        one_year = 365 * 24 * 3600
        
        # Should pass for 1 year
        validate_ttl(one_year)
        
        # Should fail for 10 years
        with pytest.raises(CacheValidationError, match="too large"):
            validate_ttl(one_year * 10)


@pytest.mark.xwsystem_unit
class TestCapacityValidation:
    """Test capacity validation."""
    
    def test_valid_capacity_accepted(self):
        """Test that valid capacities are accepted."""
        validate_capacity(100)
        validate_capacity(1000)
        validate_capacity(10000)
    
    def test_zero_capacity_rejected(self):
        """Test that zero capacity is rejected."""
        with pytest.raises(CacheValidationError, match="at least"):
            validate_capacity(0)
    
    def test_negative_capacity_rejected(self):
        """Test that negative capacity is rejected."""
        with pytest.raises(CacheValidationError, match="at least"):
            validate_capacity(-10)
    
    def test_non_int_capacity_rejected(self):
        """Test that non-integer capacity is rejected."""
        with pytest.raises(CacheValidationError, match="must be an integer"):
            validate_capacity(128.5)

