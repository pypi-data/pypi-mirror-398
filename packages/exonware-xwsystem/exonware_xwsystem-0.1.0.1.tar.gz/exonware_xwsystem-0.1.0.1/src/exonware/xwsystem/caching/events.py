#!/usr/bin/env python3
#exonware/xwsystem/caching/events.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Event system for caching module.
Extensibility Priority #5 - Event-driven architecture for custom behaviors.
"""

from typing import Callable, Any, Optional
from enum import Enum
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.events")


class CacheEvent(Enum):
    """Cache events for hook registration."""
    HIT = "hit"
    MISS = "miss"
    PUT = "put"
    DELETE = "delete"
    EVICT = "evict"
    EXPIRE = "expire"
    CLEAR = "clear"
    ERROR = "error"


class CacheEventEmitter:
    """
    Mixin class for event emission in caches.
    
    Provides event hook registration and emission functionality.
    
    Example:
        class EventDrivenCache(CacheEventEmitter, LRUCache):
            def get(self, key):
                value = super().get(key)
                if value is not None:
                    self._emit(CacheEvent.HIT, key=key, value=value)
                else:
                    self._emit(CacheEvent.MISS, key=key)
                return value
    """
    
    def __init__(self):
        """Initialize event emitter."""
        self._hooks: dict[CacheEvent, list[Callable]] = {
            event: [] for event in CacheEvent
        }
        self._event_stats: dict[CacheEvent, int] = {
            event: 0 for event in CacheEvent
        }
    
    def on(self, event: CacheEvent, callback: Callable) -> None:
        """
        Register event callback.
        
        Args:
            event: Event to listen for
            callback: Callback function(event, **kwargs)
                     
        Example:
            def on_cache_hit(event, key, value):
                print(f"Cache hit for {key}")
            
            cache.on(CacheEvent.HIT, on_cache_hit)
        """
        if event not in self._hooks:
            raise ValueError(f"Invalid event: {event}. Valid events: {list(CacheEvent)}")
        
        if callback not in self._hooks[event]:
            self._hooks[event].append(callback)
            logger.debug(f"Registered callback for event: {event.value}")
    
    def off(self, event: CacheEvent, callback: Callable) -> bool:
        """
        Unregister event callback.
        
        Args:
            event: Event to stop listening for
            callback: Callback function to remove
            
        Returns:
            True if callback was removed
        """
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
            logger.debug(f"Unregistered callback for event: {event.value}")
            return True
        return False
    
    def clear_hooks(self, event: Optional[CacheEvent] = None) -> None:
        """
        Clear event hooks.
        
        Args:
            event: Specific event to clear (None = clear all)
        """
        if event:
            self._hooks[event].clear()
        else:
            for event_type in self._hooks:
                self._hooks[event_type].clear()
    
    def _emit(self, event: CacheEvent, **kwargs) -> None:
        """
        Emit event to registered callbacks.
        
        Args:
            event: Event to emit
            **kwargs: Event data passed to callbacks
        """
        self._event_stats[event] += 1
        
        for callback in self._hooks.get(event, []):
            try:
                callback(event=event, **kwargs)
            except Exception as e:
                logger.error(f"Event callback failed for {event.value}: {e}")
                self._emit(CacheEvent.ERROR, error=e, event=event, **kwargs)
    
    def get_event_stats(self) -> dict[str, int]:
        """
        Get event emission statistics.
        
        Returns:
            Dictionary of event counts
        """
        return {event.value: count for event, count in self._event_stats.items()}


class EventLogger:
    """
    Built-in event logger for debugging.
    
    Logs all cache events for debugging and monitoring.
    """
    
    def __init__(self, log_level: str = "DEBUG"):
        """
        Initialize event logger.
        
        Args:
            log_level: Logging level for events
        """
        self.log_level = log_level
        self.events_log: list[dict[str, Any]] = []
    
    def __call__(self, event: CacheEvent, **kwargs):
        """Log event."""
        import time
        
        log_entry = {
            'timestamp': time.time(),
            'event': event.value,
            'data': kwargs
        }
        
        self.events_log.append(log_entry)
        
        # Format message
        key = kwargs.get('key', '?')
        if event == CacheEvent.HIT:
            logger.debug(f"[EVENT] Cache HIT: {key}")
        elif event == CacheEvent.MISS:
            logger.debug(f"[EVENT] Cache MISS: {key}")
        elif event == CacheEvent.PUT:
            logger.debug(f"[EVENT] Cache PUT: {key}")
        elif event == CacheEvent.DELETE:
            logger.debug(f"[EVENT] Cache DELETE: {key}")
        elif event == CacheEvent.EVICT:
            logger.debug(f"[EVENT] Cache EVICT: {key}")
        elif event == CacheEvent.EXPIRE:
            logger.debug(f"[EVENT] Cache EXPIRE: {key}")
        elif event == CacheEvent.ERROR:
            logger.error(f"[EVENT] Cache ERROR: {kwargs.get('error', 'Unknown')}")
    
    def get_events(self, event_type: Optional[CacheEvent] = None) -> list[dict[str, Any]]:
        """Get logged events, optionally filtered by type."""
        if event_type:
            return [e for e in self.events_log if e['event'] == event_type.value]
        return self.events_log
    
    def clear(self) -> None:
        """Clear event log."""
        self.events_log.clear()


__all__ = [
    'CacheEvent',
    'CacheEventEmitter',
    'EventLogger',
]

