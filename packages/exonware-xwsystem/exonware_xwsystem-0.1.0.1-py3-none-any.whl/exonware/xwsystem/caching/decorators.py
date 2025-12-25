#!/usr/bin/env python3
#exonware/xwsystem/caching/decorators.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Advanced cache decorators with hooks and customization.
Extensibility Priority #5 - Flexible caching decorators for functions.
"""

import functools
import asyncio
from typing import Any, Callable, Optional, Hashable
from .lru_cache import LRUCache, AsyncLRUCache
from .utils import default_key_builder
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.decorators")


def xwcached(
    cache: Optional[Any] = None,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None,
    condition: Optional[Callable] = None,
    on_hit: Optional[Callable] = None,
    on_miss: Optional[Callable] = None,
    namespace: Optional[str] = None
):
    """
    Advanced caching decorator with hooks and customization (eXonware naming convention).
    
    Args:
        cache: Cache instance to use (default: new LRUCache(128))
        ttl: Time to live for cached results
        key_builder: Custom key generation function(func, args, kwargs) -> key
        condition: Conditional caching function(args, kwargs) -> bool
        on_hit: Callback on cache hit(key, value) -> None
        on_miss: Callback on cache miss(key, result) -> None
        namespace: Cache namespace for key prefixing
        
    Example:
        @xwcached(ttl=300, on_hit=lambda k, v: print(f"Hit: {k}"))
        def expensive_function(x, y):
            return x + y
        
        @xwcached(
            key_builder=lambda f, a, kw: f"custom:{a[0]}",
            condition=lambda a, kw: a[0] > 0  # Only cache if first arg > 0
        )
        def conditional_cache(value):
            return value * 2
    """
    # Initialize cache if not provided
    if cache is None:
        cache = LRUCache(capacity=128)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check condition
            if condition and not condition(args, kwargs):
                return func(*args, **kwargs)
            
            # Build cache key
            if key_builder:
                key = key_builder(func, args, kwargs)
            else:
                key = default_key_builder(func, args, kwargs)
            
            # Add namespace prefix
            if namespace:
                key = f"{namespace}:{key}"
            
            # Try to get from cache
            result = cache.get(key)
            
            if result is not None:
                # Cache hit
                if on_hit:
                    try:
                        on_hit(key, result)
                    except Exception as e:
                        logger.warning(f"on_hit callback failed: {e}")
                
                return result
            
            # Cache miss - compute result
            result = func(*args, **kwargs)
            
            # Store in cache
            if hasattr(cache, 'put'):
                cache.put(key, result)
            elif hasattr(cache, 'set'):
                cache.set(key, result)
            
            # Call on_miss hook
            if on_miss:
                try:
                    on_miss(key, result)
                except Exception as e:
                    logger.warning(f"on_miss callback failed: {e}")
            
            return result
        
        # Add cache control methods to wrapper
        wrapper.cache = cache
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: cache.get_stats() if hasattr(cache, 'get_stats') else {}
        
        return wrapper
    
    return decorator


def xw_async_cached(
    cache: Optional[Any] = None,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None,
    condition: Optional[Callable] = None,
    on_hit: Optional[Callable] = None,
    on_miss: Optional[Callable] = None,
    namespace: Optional[str] = None
):
    """
    Advanced async caching decorator (eXonware naming convention).
    
    Args:
        cache: Async cache instance (default: new AsyncLRUCache(128))
        ttl: Time to live for cached results
        key_builder: Custom key generation function
        condition: Conditional caching function
        on_hit: Async callback on cache hit
        on_miss: Async callback on cache miss
        namespace: Cache namespace for key prefixing
        
    Example:
        @xw_async_cached(ttl=300)
        async def expensive_async_function(x, y):
            await asyncio.sleep(1)
            return x + y
    """
    if cache is None:
        cache = AsyncLRUCache(capacity=128)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check condition
            if condition:
                if asyncio.iscoroutinefunction(condition):
                    should_cache = await condition(args, kwargs)
                else:
                    should_cache = condition(args, kwargs)
                
                if not should_cache:
                    return await func(*args, **kwargs)
            
            # Build key
            if key_builder:
                if asyncio.iscoroutinefunction(key_builder):
                    key = await key_builder(func, args, kwargs)
                else:
                    key = key_builder(func, args, kwargs)
            else:
                key = default_key_builder(func, args, kwargs)
            
            if namespace:
                key = f"{namespace}:{key}"
            
            # Try cache
            result = await cache.get(key)
            
            if result is not None:
                # Cache hit
                if on_hit:
                    if asyncio.iscoroutinefunction(on_hit):
                        await on_hit(key, result)
                    else:
                        on_hit(key, result)
                return result
            
            # Cache miss
            result = await func(*args, **kwargs)
            
            await cache.put(key, result)
            
            if on_miss:
                if asyncio.iscoroutinefunction(on_miss):
                    await on_miss(key, result)
                else:
                    on_miss(key, result)
            
            return result
        
        wrapper.cache = cache
        wrapper.cache_clear = lambda: asyncio.run(cache.clear())
        wrapper.cache_info = lambda: asyncio.run(cache.get_stats())
        
        return wrapper
    
    return decorator


# Simplified aliases with XW prefix
def xwcache(func: Optional[Callable] = None, ttl: Optional[int] = None):
    """
    Simple cache decorator (eXonware naming convention).
    
    Example:
        @xwcache
        def my_function(x):
            return x * 2
            
        @xwcache(ttl=300)
        def another_function(x):
            return x * 3
    """
    if func is None:
        # Called with arguments: @xwcache(ttl=300)
        return xwcached(ttl=ttl)
    else:
        # Called without arguments: @xwcache
        return xwcached()(func)


def xw_async_cache(func: Optional[Callable] = None, ttl: Optional[int] = None):
    """
    Simple async cache decorator (eXonware naming convention).
    
    Example:
        @xw_async_cache
        async def my_async_function(x):
            await asyncio.sleep(1)
            return x * 2
    """
    if func is None:
        return xw_async_cached(ttl=ttl)
    else:
        return xw_async_cached()(func)


# Backward compatibility aliases (deprecated, use xw-prefixed versions)
cached = xwcached
async_cached = xw_async_cached
cache = xwcache
async_cache = xw_async_cache
cache_result = xwcache
async_cache_result = xw_async_cache


__all__ = [
    # New XW-prefixed names (preferred)
    'xwcached',
    'xw_async_cached',
    'xwcache',
    'xw_async_cache',
    # Backward compatibility (deprecated)
    'cached',
    'async_cached',
    'cache',
    'async_cache',
    'cache_result',
    'async_cache_result',
]
