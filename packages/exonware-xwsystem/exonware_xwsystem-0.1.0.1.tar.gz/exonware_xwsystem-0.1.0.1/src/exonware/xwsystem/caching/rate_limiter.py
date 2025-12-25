#!/usr/bin/env python3
#exonware/xwsystem/caching/rate_limiter.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Rate limiting for caching module - Security Priority #1.
Prevents DoS attacks via cache flooding.
"""

import time
import threading
from collections import deque
from typing import Optional
from .errors import CacheRateLimitError


class RateLimiter:
    """
    Token bucket rate limiter for cache operations.
    
    Prevents DoS attacks by limiting the rate of cache operations.
    
    Features:
        - Token bucket algorithm
        - Thread-safe implementation
        - Configurable burst capacity
        - Graceful degradation
    """
    
    def __init__(
        self,
        max_ops_per_second: int = 10000,
        burst_capacity: Optional[int] = None,
        time_window: float = 1.0
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_ops_per_second: Maximum operations per second
            burst_capacity: Maximum burst size (default: max_ops_per_second)
            time_window: Time window in seconds
        """
        if max_ops_per_second <= 0:
            raise ValueError(
                f"max_ops_per_second must be positive, got {max_ops_per_second}"
            )
        
        self.max_ops_per_second = max_ops_per_second
        self.burst_capacity = burst_capacity or max_ops_per_second
        self.time_window = time_window
        
        # Token bucket state
        self._tokens = self.burst_capacity
        self._last_update = time.time()
        self._lock = threading.RLock()
        
        # Statistics
        self._total_requests = 0
        self._rejected_requests = 0
        self._timestamps = deque(maxlen=max_ops_per_second)
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens for an operation.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired successfully
            
        Raises:
            CacheRateLimitError: If rate limit is exceeded
        """
        with self._lock:
            self._total_requests += 1
            
            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self._last_update
            self._tokens = min(
                self.burst_capacity,
                self._tokens + (elapsed * self.max_ops_per_second)
            )
            self._last_update = now
            
            # Check if enough tokens available
            if self._tokens >= tokens:
                self._tokens -= tokens
                self._timestamps.append(now)
                return True
            else:
                self._rejected_requests += 1
                raise CacheRateLimitError(
                    f"Rate limit exceeded: {self.max_ops_per_second} ops/sec. "
                    f"Current rate: {self.get_current_rate():.0f} ops/sec. "
                    f"Please slow down and try again later."
                )
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without raising exception.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
        """
        try:
            return self.acquire(tokens)
        except CacheRateLimitError:
            return False
    
    def get_current_rate(self) -> float:
        """
        Get current operations per second rate.
        
        Returns:
            Current ops/sec rate
        """
        with self._lock:
            if len(self._timestamps) < 2:
                return 0.0
            
            # Calculate rate from recent timestamps
            now = time.time()
            recent_timestamps = [
                ts for ts in self._timestamps
                if now - ts <= self.time_window
            ]
            
            if len(recent_timestamps) < 2:
                return 0.0
            
            time_span = now - recent_timestamps[0]
            if time_span > 0:
                return len(recent_timestamps) / time_span
            return 0.0
    
    def get_stats(self) -> dict:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            rejection_rate = (
                self._rejected_requests / self._total_requests
                if self._total_requests > 0
                else 0.0
            )
            
            return {
                'max_ops_per_second': self.max_ops_per_second,
                'burst_capacity': self.burst_capacity,
                'current_tokens': int(self._tokens),
                'current_rate': self.get_current_rate(),
                'total_requests': self._total_requests,
                'rejected_requests': self._rejected_requests,
                'rejection_rate': rejection_rate,
            }
    
    def reset(self) -> None:
        """Reset rate limiter state."""
        with self._lock:
            self._tokens = self.burst_capacity
            self._last_update = time.time()
            self._total_requests = 0
            self._rejected_requests = 0
            self._timestamps.clear()


class FixedWindowRateLimiter:
    """
    Fixed window rate limiter.
    
    Simpler than token bucket but can have burst issues at window boundaries.
    """
    
    def __init__(self, max_ops: int = 10000, window_seconds: float = 1.0):
        """
        Initialize fixed window rate limiter.
        
        Args:
            max_ops: Maximum operations per window
            window_seconds: Window size in seconds
        """
        self.max_ops = max_ops
        self.window_seconds = window_seconds
        
        self._window_start = time.time()
        self._operation_count = 0
        self._lock = threading.RLock()
        
        # Statistics
        self._total_requests = 0
        self._rejected_requests = 0
    
    def acquire(self) -> bool:
        """
        Acquire permission for an operation.
        
        Returns:
            True if operation allowed
            
        Raises:
            CacheRateLimitError: If rate limit exceeded
        """
        with self._lock:
            self._total_requests += 1
            now = time.time()
            
            # Check if we need to start a new window
            if now - self._window_start >= self.window_seconds:
                self._window_start = now
                self._operation_count = 0
            
            # Check if within limit
            if self._operation_count < self.max_ops:
                self._operation_count += 1
                return True
            else:
                self._rejected_requests += 1
                raise CacheRateLimitError(
                    f"Rate limit exceeded: {self.max_ops} ops per {self.window_seconds}s window. "
                    f"Try again in {self.window_seconds - (now - self._window_start):.2f} seconds."
                )
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        with self._lock:
            return {
                'max_ops': self.max_ops,
                'window_seconds': self.window_seconds,
                'current_count': self._operation_count,
                'total_requests': self._total_requests,
                'rejected_requests': self._rejected_requests,
            }


__all__ = [
    'RateLimiter',
    'FixedWindowRateLimiter',
]

