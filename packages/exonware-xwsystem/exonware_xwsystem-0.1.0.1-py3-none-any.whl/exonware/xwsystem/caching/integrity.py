#!/usr/bin/env python3
#exonware/xwsystem/caching/integrity.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Cache integrity verification - Security Priority #1.
Protects against cache poisoning and tampering.
"""

from typing import Any, Optional
from dataclasses import dataclass
from .errors import CacheIntegrityError
from .utils import compute_checksum


@dataclass
class CacheEntry:
    """
    Cache entry with integrity verification.
    
    Attributes:
        key: Cache key
        value: Cached value
        checksum: Integrity checksum (SHA256 by default)
        created_at: Creation timestamp
        access_count: Number of accesses
    """
    key: Any
    value: Any
    checksum: str
    created_at: float
    access_count: int = 0
    
    def verify_integrity(self) -> bool:
        """
        Verify entry integrity.
        
        Returns:
            True if integrity check passes
            
        Raises:
            CacheIntegrityError: If integrity check fails
        """
        try:
            current_checksum = compute_checksum(self.value)
            if current_checksum != self.checksum:
                raise CacheIntegrityError(
                    f"Integrity check failed for key: {self.key}. "
                    f"Expected checksum: {self.checksum[:16]}..., "
                    f"Got: {current_checksum[:16]}... "
                    f"Cache may have been tampered with."
                )
            return True
        except Exception as e:
            if isinstance(e, CacheIntegrityError):
                raise
            raise CacheIntegrityError(
                f"Integrity verification failed: {e}"
            )


def create_secure_entry(
    key: Any,
    value: Any,
    created_at: float,
    algorithm: str = 'sha256'
) -> CacheEntry:
    """
    Create cache entry with integrity checksum.
    
    Args:
        key: Cache key
        value: Value to cache
        created_at: Creation timestamp
        algorithm: Hash algorithm for checksum
        
    Returns:
        CacheEntry with integrity checksum
    """
    checksum = compute_checksum(value, algorithm=algorithm)
    return CacheEntry(
        key=key,
        value=value,
        checksum=checksum,
        created_at=created_at,
        access_count=0
    )


def verify_entry_integrity(entry: CacheEntry) -> bool:
    """
    Verify cache entry integrity.
    
    Args:
        entry: Cache entry to verify
        
    Returns:
        True if integrity check passes
        
    Raises:
        CacheIntegrityError: If integrity check fails
    """
    return entry.verify_integrity()


def update_entry_checksum(entry: CacheEntry) -> None:
    """
    Update entry checksum after value modification.
    
    Args:
        entry: Cache entry to update
        
    Note:
        Call this after modifying the entry value.
    """
    entry.checksum = compute_checksum(entry.value)


__all__ = [
    'CacheEntry',
    'create_secure_entry',
    'verify_entry_integrity',
    'update_entry_checksum',
]

