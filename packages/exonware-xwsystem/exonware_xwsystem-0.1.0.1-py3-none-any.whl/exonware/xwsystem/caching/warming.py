#!/usr/bin/env python3
#exonware/xwsystem/caching/warming.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Cache warming utilities for preloading data.
Performance Priority #4 - Reduce cold start penalties.
"""

from typing import Any, Callable, Optional, Hashable
from abc import ABC, abstractmethod
import time
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.warming")


class AWarmingStrategy(ABC):
    """Abstract base class for cache warming strategies."""
    
    @abstractmethod
    def warm(self, cache: Any, keys: list[Hashable], loader: Callable[[Hashable], Any]) -> int:
        """
        Warm cache with data.
        
        Args:
            cache: Cache instance to warm
            keys: Keys to preload
            loader: Function to load data for a key
            
        Returns:
            Number of keys successfully loaded
        """
        pass


class PreloadWarmingStrategy(AWarmingStrategy):
    """
    Preload warming strategy - load all keys upfront.
    
    Suitable for small datasets that fit entirely in cache.
    """
    
    def warm(self, cache: Any, keys: list[Hashable], loader: Callable[[Hashable], Any]) -> int:
        """Preload all keys into cache."""
        success_count = 0
        failures = []
        
        logger.info(f"Preloading {len(keys)} keys into cache {cache.name if hasattr(cache, 'name') else 'unknown'}")
        start_time = time.time()
        
        for key in keys:
            try:
                value = loader(key)
                cache.put(key, value)
                success_count += 1
            except Exception as e:
                failures.append((key, str(e)))
                logger.warning(f"Failed to warm key {key}: {e}")
        
        elapsed = time.time() - start_time
        
        logger.info(
            f"Cache warming complete: {success_count}/{len(keys)} loaded "
            f"in {elapsed:.2f}s ({len(keys)/elapsed:.0f} keys/sec)"
        )
        
        if failures:
            logger.warning(f"Failed to load {len(failures)} keys: {failures[:5]}...")
        
        return success_count


class LazyWarmingStrategy(AWarmingStrategy):
    """
    Lazy warming strategy - load keys on-demand as accessed.
    
    Suitable for large datasets where only subset will be accessed.
    """
    
    def __init__(self, preload_limit: int = 100):
        """
        Initialize lazy warming strategy.
        
        Args:
            preload_limit: Maximum keys to preload upfront
        """
        self.preload_limit = preload_limit
    
    def warm(self, cache: Any, keys: list[Hashable], loader: Callable[[Hashable], Any]) -> int:
        """Preload limited number of keys, rest loaded lazily."""
        # Preload up to limit
        preload_keys = keys[:self.preload_limit]
        
        logger.info(
            f"Lazy warming: preloading {len(preload_keys)}/{len(keys)} keys"
        )
        
        success_count = 0
        for key in preload_keys:
            try:
                value = loader(key)
                cache.put(key, value)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to warm key {key}: {e}")
        
        return success_count


class PriorityWarmingStrategy(AWarmingStrategy):
    """
    Priority-based warming - load high-priority keys first.
    
    Suitable when some keys are more critical than others.
    """
    
    def __init__(self, priority_func: Callable[[Hashable], float]):
        """
        Initialize priority warming strategy.
        
        Args:
            priority_func: Function that returns priority score for a key
                          (higher score = higher priority)
        """
        self.priority_func = priority_func
    
    def warm(self, cache: Any, keys: list[Hashable], loader: Callable[[Hashable], Any]) -> int:
        """Load keys in priority order."""
        # Sort keys by priority (descending)
        sorted_keys = sorted(keys, key=self.priority_func, reverse=True)
        
        logger.info(f"Priority warming: loading {len(sorted_keys)} keys by priority")
        
        success_count = 0
        for key in sorted_keys:
            try:
                value = loader(key)
                cache.put(key, value)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to warm key {key}: {e}")
        
        return success_count


def warm_cache(
    cache: Any,
    loader: Callable[[Hashable], Any],
    keys: list[Hashable],
    strategy: Optional[AWarmingStrategy] = None,
    on_progress: Optional[Callable[[int, int], None]] = None
) -> int:
    """
    Warm cache with data using specified strategy.
    
    Args:
        cache: Cache instance to warm
        loader: Function to load data for a key
        keys: List of keys to preload
        strategy: Warming strategy (default: PreloadWarmingStrategy)
        on_progress: Optional callback for progress updates (loaded, total)
        
    Returns:
        Number of keys successfully loaded
        
    Example:
        def load_user(user_id):
            return database.get_user(user_id)
        
        user_ids = [1, 2, 3, 4, 5]
        loaded = warm_cache(cache, load_user, user_ids)
        print(f"Warmed cache with {loaded} users")
    """
    if strategy is None:
        strategy = PreloadWarmingStrategy()
    
    if on_progress:
        # Wrap loader with progress callback
        original_loader = loader
        success = [0]
        
        def loader_with_progress(key):
            value = original_loader(key)
            success[0] += 1
            on_progress(success[0], len(keys))
            return value
        
        return strategy.warm(cache, keys, loader_with_progress)
    else:
        return strategy.warm(cache, keys, loader)


def warm_cache_async(
    cache: Any,
    loader: Callable,
    keys: list[Hashable]
) -> int:
    """
    Warm async cache with data.
    
    Args:
        cache: Async cache instance
        loader: Async function to load data
        keys: List of keys to preload
        
    Returns:
        Number of keys successfully loaded
        
    Note:
        This is a synchronous wrapper. For true async warming,
        use the loader directly with async for.
    """
    import asyncio
    
    async def async_warm():
        success_count = 0
        for key in keys:
            try:
                value = await loader(key)
                await cache.put(key, value)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to warm key {key}: {e}")
        return success_count
    
    return asyncio.run(async_warm())


__all__ = [
    'AWarmingStrategy',
    'PreloadWarmingStrategy',
    'LazyWarmingStrategy',
    'PriorityWarmingStrategy',
    'warm_cache',
    'warm_cache_async',
]

