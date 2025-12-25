#!/usr/bin/env python3
#exonware/xwsystem/caching/validation.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Input validation for caching module - Security Priority #1.
Implements comprehensive validation to prevent security vulnerabilities.
"""

from typing import Any, Hashable
from .errors import CacheValidationError, CacheKeySizeError, CacheValueSizeError
from .utils import estimate_object_size


# Security limits (configurable via environment or config)
DEFAULT_MAX_KEY_SIZE = 1024  # 1KB
DEFAULT_MAX_VALUE_SIZE_MB = 10  # 10MB
DEFAULT_MAX_VALUE_SIZE = DEFAULT_MAX_VALUE_SIZE_MB * 1024 * 1024


def validate_cache_key(
    key: Any,
    max_size: int = DEFAULT_MAX_KEY_SIZE,
    allow_none: bool = False
) -> None:
    """
    Validate cache key for security and correctness.
    
    Args:
        key: Cache key to validate
        max_size: Maximum key size in bytes
        allow_none: Whether to allow None as a key
        
    Raises:
        CacheValidationError: If key is invalid
        CacheKeySizeError: If key exceeds maximum size
        
    Security considerations:
        - Prevents memory exhaustion attacks via large keys
        - Ensures keys are hashable
        - Validates key types
    """
    # Check for None
    if key is None:
        if not allow_none:
            raise CacheValidationError(
                "Cache key cannot be None. "
                "Use a valid hashable object (str, int, tuple, etc.)"
            )
        return
    
    # Check if key is hashable
    try:
        hash(key)
    except TypeError as e:
        raise CacheValidationError(
            f"Cache key must be hashable, got {type(key).__name__}. "
            f"Error: {e}. "
            f"Valid key types: str, int, float, tuple, frozenset"
        )
    
    # Check key size (prevent memory exhaustion)
    if isinstance(key, str):
        key_size = len(key.encode('utf-8'))
        if key_size > max_size:
            raise CacheKeySizeError(
                f"Cache key too large: {key_size:,} bytes (max: {max_size:,}). "
                f"This prevents memory exhaustion attacks. "
                f"Consider using a hash of the key instead."
            )
    elif isinstance(key, bytes):
        if len(key) > max_size:
            raise CacheKeySizeError(
                f"Cache key too large: {len(key):,} bytes (max: {max_size:,}). "
                f"Consider using a hash instead."
            )


def validate_cache_value(
    value: Any,
    max_size_mb: float = DEFAULT_MAX_VALUE_SIZE_MB,
    max_size: int = None
) -> None:
    """
    Validate cache value for security and correctness.
    
    Args:
        value: Cache value to validate
        max_size_mb: Maximum value size in megabytes
        max_size: Maximum value size in bytes (overrides max_size_mb)
        
    Raises:
        CacheValueSizeError: If value exceeds maximum size
        
    Security considerations:
        - Prevents memory exhaustion attacks via large values
        - Protects against DoS via excessive memory usage
    """
    # Determine max size
    if max_size is None:
        max_size = int(max_size_mb * 1024 * 1024)
    
    # Estimate value size
    value_size = estimate_object_size(value)
    
    if value_size > max_size:
        raise CacheValueSizeError(
            f"Cache value too large: {value_size:,} bytes "
            f"({value_size / (1024*1024):.2f} MB) "
            f"(max: {max_size:,} bytes / {max_size_mb:.1f} MB). "
            f"This prevents memory exhaustion. "
            f"Consider storing a reference instead of the full value."
        )


def sanitize_key(key: Any) -> str:
    """
    Sanitize cache key to ensure it's safe for use.
    
    Args:
        key: Cache key to sanitize
        
    Returns:
        Sanitized key as string
        
    Note:
        This function converts any hashable object to a safe string representation.
        For complex objects, use a custom key builder function.
    """
    if isinstance(key, str):
        # Already a string, return as-is
        return key
    
    if isinstance(key, (int, float, bool)):
        # Simple types: convert to string
        return str(key)
    
    if isinstance(key, bytes):
        # Bytes: decode if possible, otherwise use hex
        try:
            return key.decode('utf-8')
        except UnicodeDecodeError:
            return key.hex()
    
    if isinstance(key, (tuple, frozenset)):
        # Collections: convert to string representation
        return str(key)
    
    # Fallback: use string representation
    return str(key)


def validate_ttl(ttl: float, min_ttl: float = 0.0, max_ttl: float = 31536000) -> None:
    """
    Validate TTL (time-to-live) parameter.
    
    Args:
        ttl: TTL in seconds
        min_ttl: Minimum allowed TTL
        max_ttl: Maximum allowed TTL (default: 1 year)
        
    Raises:
        CacheValidationError: If TTL is invalid
    """
    if not isinstance(ttl, (int, float)):
        raise CacheValidationError(
            f"TTL must be a number (int or float), got {type(ttl).__name__}. "
            f"Example: ttl=300.0 (5 minutes)"
        )
    
    if ttl < min_ttl:
        raise CacheValidationError(
            f"TTL must be at least {min_ttl} seconds, got {ttl}. "
            f"Example: ttl=60.0 (1 minute)"
        )
    
    if ttl > max_ttl:
        raise CacheValidationError(
            f"TTL too large: {ttl:,.0f} seconds ({ttl/86400:.1f} days). "
            f"Maximum: {max_ttl:,.0f} seconds ({max_ttl/86400:.1f} days)"
        )


def validate_capacity(
    capacity: int,
    min_capacity: int = 1,
    max_capacity: int = 10000000
) -> None:
    """
    Validate cache capacity parameter.
    
    Args:
        capacity: Capacity to validate
        min_capacity: Minimum allowed capacity
        max_capacity: Maximum allowed capacity
        
    Raises:
        CacheValidationError: If capacity is invalid
    """
    if not isinstance(capacity, int):
        raise CacheValidationError(
            f"Cache capacity must be an integer, got {type(capacity).__name__}. "
            f"Example: capacity=1000"
        )
    
    if capacity < min_capacity:
        raise CacheValidationError(
            f"Cache capacity must be at least {min_capacity}, got {capacity}. "
            f"Example: capacity={min_capacity}"
        )
    
    if capacity > max_capacity:
        raise CacheValidationError(
            f"Cache capacity too large: {capacity:,} (max: {max_capacity:,}). "
            f"For very large caches, consider using a distributed cache system."
        )


__all__ = [
    'validate_cache_key',
    'validate_cache_value',
    'sanitize_key',
    'validate_ttl',
    'validate_capacity',
    'DEFAULT_MAX_KEY_SIZE',
    'DEFAULT_MAX_VALUE_SIZE_MB',
    'DEFAULT_MAX_VALUE_SIZE',
]

