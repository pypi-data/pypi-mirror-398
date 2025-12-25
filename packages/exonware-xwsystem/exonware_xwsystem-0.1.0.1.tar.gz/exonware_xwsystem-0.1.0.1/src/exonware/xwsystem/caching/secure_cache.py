#!/usr/bin/env python3
#exonware/xwsystem/caching/secure_cache.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Secure cache implementations with validation, integrity checks, and rate limiting.
Security Priority #1 - Production-grade security features.
"""

import time
from typing import Any, Optional, Hashable
from .lru_cache import LRUCache
from .lfu_cache import LFUCache
from .ttl_cache import TTLCache
from .validation import (
    validate_cache_key,
    validate_cache_value,
    DEFAULT_MAX_KEY_SIZE,
    DEFAULT_MAX_VALUE_SIZE_MB,
)
from .integrity import create_secure_entry, verify_entry_integrity, CacheEntry
from .rate_limiter import RateLimiter
from .errors import CacheValidationError, CacheIntegrityError, CacheRateLimitError


class SecureLRUCache(LRUCache):
    """
    LRU Cache with security features.
    
    Additional security features:
        - Input validation (keys and values)
        - Integrity verification with checksums
        - Rate limiting to prevent DoS
        - Optional mode for performance vs security tradeoff
    """
    
    def __init__(
        self,
        capacity: int = 128,
        ttl: Optional[float] = None,
        name: Optional[str] = None,
        enable_integrity: bool = True,
        enable_rate_limit: bool = True,
        max_ops_per_second: int = 10000,
        max_key_size: int = DEFAULT_MAX_KEY_SIZE,
        max_value_size_mb: float = DEFAULT_MAX_VALUE_SIZE_MB,
    ):
        """
        Initialize secure LRU cache.
        
        Args:
            capacity: Maximum cache size
            ttl: Optional TTL in seconds
            name: Cache name for debugging
            enable_integrity: Enable integrity verification
            enable_rate_limit: Enable rate limiting
            max_ops_per_second: Maximum operations per second
            max_key_size: Maximum key size in bytes
            max_value_size_mb: Maximum value size in MB
        """
        super().__init__(capacity, ttl, name)
        
        self.enable_integrity = enable_integrity
        self.enable_rate_limit = enable_rate_limit
        self.max_key_size = max_key_size
        self.max_value_size_mb = max_value_size_mb
        
        # Security components
        if self.enable_rate_limit:
            self.rate_limiter = RateLimiter(max_ops_per_second=max_ops_per_second)
        
        # Track integrity violations
        self._integrity_violations = 0
    
    def _check_rate_limit(self) -> None:
        """Check rate limit if enabled."""
        if self.enable_rate_limit:
            try:
                self.rate_limiter.acquire()
            except CacheRateLimitError:
                # Re-raise with additional context
                raise
    
    def put(self, key: Hashable, value: Any) -> None:
        """
        Put value with security checks.
        
        Args:
            key: Cache key
            value: Value to cache
            
        Raises:
            CacheValidationError: If validation fails
            CacheRateLimitError: If rate limit exceeded
        """
        # Rate limiting
        self._check_rate_limit()
        
        # Validate key
        validate_cache_key(key, max_size=self.max_key_size)
        
        # Validate value
        validate_cache_value(value, max_size_mb=self.max_value_size_mb)
        
        # Store with integrity if enabled
        if self.enable_integrity:
            # Wrap value in secure entry
            entry = create_secure_entry(
                key=key,
                value=value,
                created_at=time.time()
            )
            super().put(key, entry)
        else:
            super().put(key, value)
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """
        Get value with integrity verification.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
            
        Raises:
            CacheIntegrityError: If integrity check fails
        """
        # Rate limiting
        self._check_rate_limit()
        
        # Get from parent
        result = super().get(key, default)
        
        if result is default:
            return default
        
        # Verify integrity if enabled
        if self.enable_integrity and isinstance(result, CacheEntry):
            try:
                verify_entry_integrity(result)
                result.access_count += 1
                return result.value
            except CacheIntegrityError as e:
                # Log violation and remove corrupted entry
                self._integrity_violations += 1
                self.delete(key)
                raise e
        
        return result
    
    def get_security_stats(self) -> dict:
        """
        Get security-related statistics.
        
        Returns:
            Dictionary with security stats
        """
        stats = {
            'enable_integrity': self.enable_integrity,
            'enable_rate_limit': self.enable_rate_limit,
            'integrity_violations': self._integrity_violations,
            'max_key_size': self.max_key_size,
            'max_value_size_mb': self.max_value_size_mb,
        }
        
        if self.enable_rate_limit:
            stats['rate_limiter'] = self.rate_limiter.get_stats()
        
        return stats


class SecureLFUCache(LFUCache):
    """
    LFU Cache with security features.
    
    Additional security features:
        - Input validation (keys and values)
        - Rate limiting to prevent DoS
    """
    
    def __init__(
        self,
        capacity: int = 128,
        name: Optional[str] = None,
        enable_rate_limit: bool = True,
        max_ops_per_second: int = 10000,
        max_key_size: int = DEFAULT_MAX_KEY_SIZE,
        max_value_size_mb: float = DEFAULT_MAX_VALUE_SIZE_MB,
    ):
        """
        Initialize secure LFU cache.
        
        Args:
            capacity: Maximum cache size
            name: Cache name for debugging
            enable_rate_limit: Enable rate limiting
            max_ops_per_second: Maximum operations per second
            max_key_size: Maximum key size in bytes
            max_value_size_mb: Maximum value size in MB
        """
        super().__init__(capacity, name)
        
        self.enable_rate_limit = enable_rate_limit
        self.max_key_size = max_key_size
        self.max_value_size_mb = max_value_size_mb
        
        if self.enable_rate_limit:
            self.rate_limiter = RateLimiter(max_ops_per_second=max_ops_per_second)
    
    def _check_rate_limit(self) -> None:
        """Check rate limit if enabled."""
        if self.enable_rate_limit:
            self.rate_limiter.acquire()
    
    def put(self, key: Hashable, value: Any) -> None:
        """Put value with security checks."""
        self._check_rate_limit()
        validate_cache_key(key, max_size=self.max_key_size)
        validate_cache_value(value, max_size_mb=self.max_value_size_mb)
        super().put(key, value)
    
    def get(self, key: Hashable, default: Any = None) -> Any:
        """Get value with rate limiting."""
        self._check_rate_limit()
        return super().get(key, default)


class SecureTTLCache(TTLCache):
    """
    TTL Cache with security features.
    
    Additional security features:
        - Input validation (keys and values)
        - Rate limiting to prevent DoS
    """
    
    def __init__(
        self,
        capacity: int = 128,
        ttl: float = 300.0,
        cleanup_interval: float = 60.0,
        name: str = "secure_ttl_cache",
        enable_rate_limit: bool = True,
        max_ops_per_second: int = 10000,
        max_key_size: int = DEFAULT_MAX_KEY_SIZE,
        max_value_size_mb: float = DEFAULT_MAX_VALUE_SIZE_MB,
    ):
        """
        Initialize secure TTL cache.
        
        Args:
            capacity: Maximum cache size
            ttl: Time to live in seconds
            cleanup_interval: Cleanup interval in seconds
            name: Cache name for debugging
            enable_rate_limit: Enable rate limiting
            max_ops_per_second: Maximum operations per second
            max_key_size: Maximum key size in bytes
            max_value_size_mb: Maximum value size in MB
        """
        super().__init__(capacity, ttl, cleanup_interval, name)
        
        self.enable_rate_limit = enable_rate_limit
        self.max_key_size = max_key_size
        self.max_value_size_mb = max_value_size_mb
        
        if self.enable_rate_limit:
            self.rate_limiter = RateLimiter(max_ops_per_second=max_ops_per_second)
    
    def _check_rate_limit(self) -> None:
        """Check rate limit if enabled."""
        if self.enable_rate_limit:
            self.rate_limiter.acquire()
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Put value with security checks."""
        self._check_rate_limit()
        validate_cache_key(key, max_size=self.max_key_size)
        validate_cache_value(value, max_size_mb=self.max_value_size_mb)
        return super().put(key, value, ttl)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with rate limiting."""
        self._check_rate_limit()
        return super().get(key, default)


__all__ = [
    'SecureLRUCache',
    'SecureLFUCache',
    'SecureTTLCache',
]

