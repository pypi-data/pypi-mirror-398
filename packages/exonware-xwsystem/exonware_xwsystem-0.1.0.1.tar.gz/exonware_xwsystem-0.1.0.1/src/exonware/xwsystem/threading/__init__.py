"""
Threading utilities for safe concurrent operations.
"""

from .locks import EnhancedRLock
from .safe_factory import MethodGenerator, ThreadSafeFactory


def create_thread_safe_cache(max_size=128, maxsize=None):
    """
    Create a thread-safe cache with LRU eviction policy.
    
    Args:
        max_size: Maximum number of items in cache (primary parameter)
        maxsize: Alternative parameter name for compatibility
        
    Returns:
        LRUCache instance
    """
    from ..caching import LRUCache
    # Support both parameter names for compatibility
    size = maxsize if maxsize is not None else max_size
    return LRUCache(capacity=size)


__all__ = ["ThreadSafeFactory", "MethodGenerator", "EnhancedRLock", "create_thread_safe_cache"]
