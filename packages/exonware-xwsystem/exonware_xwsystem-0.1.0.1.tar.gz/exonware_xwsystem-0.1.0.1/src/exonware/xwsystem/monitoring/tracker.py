#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 26, 2025

Operation tracker for monitoring operations with context management.
"""

import threading
import time
from contextlib import contextmanager
from typing import Any, Optional, Callable
from .metrics import OperationMetrics, MetricSnapshot
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.monitoring.tracker")


class OperationTracker:
    """
    Operation tracker for monitoring operations with automatic timing.
    
    Features:
    - Context manager for automatic timing
    - Success/error count tracking
    - Duration statistics (min, max, avg, recent)
    - Thread-safe metrics collection
    - Operation type categorization
    - Custom callback support
    """
    
    def __init__(self, max_recent_samples: int = 100):
        """
        Initialize operation tracker.
        
        Args:
            max_recent_samples: Maximum number of recent samples to keep
        """
        self.max_recent_samples = max_recent_samples
        self._lock = threading.RLock()
        self._metrics: dict[str, OperationMetrics] = {}
        self._callbacks: list[Callable[[str, float, bool], None]] = []
    
    def track_operation(
        self,
        operation_name: str,
        duration: float,
        success: bool = True,
        error: Optional[Exception] = None
    ):
        """
        Track a completed operation.
        
        Args:
            operation_name: Name of the operation
            duration: Operation duration in seconds
            success: Whether the operation succeeded
            error: Exception if operation failed
        """
        with self._lock:
            if operation_name not in self._metrics:
                self._metrics[operation_name] = OperationMetrics()
            
            metrics = self._metrics[operation_name]
            metrics.add_timing(duration)
            
            if not success:
                metrics.add_error()
                if error:
                    logger.warning(f"Operation {operation_name} failed: {error}")
            
            # Call registered callbacks
            for callback in self._callbacks:
                try:
                    callback(operation_name, duration, success)
                except Exception as e:
                    logger.error(f"Callback failed for operation {operation_name}: {e}")
    
    @contextmanager
    def track(self, operation_name: str):
        """
        Context manager for tracking operations.
        
        Args:
            operation_name: Name of the operation to track
            
        Example:
            with tracker.track("database_query"):
                # Perform operation
                result = database.query("SELECT * FROM users")
        """
        start_time = time.time()
        success = True
        error = None
        
        try:
            yield
        except Exception as e:
            success = False
            error = e
            raise
        finally:
            duration = time.time() - start_time
            self.track_operation(operation_name, duration, success, error)
    
    def get_operation_stats(self, operation_name: str) -> Optional[OperationMetrics]:
        """Get statistics for a specific operation."""
        with self._lock:
            return self._metrics.get(operation_name)
    
    def get_all_stats(self) -> dict[str, OperationMetrics]:
        """Get statistics for all operations."""
        with self._lock:
            return self._metrics.copy()
    
    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics across all operations."""
        with self._lock:
            if not self._metrics:
                return {
                    'total_operations': 0,
                    'total_calls': 0,
                    'total_time': 0.0,
                    'total_errors': 0,
                    'operation_count': 0,
                }
            
            total_calls = sum(m.total_calls for m in self._metrics.values())
            total_time = sum(m.total_time for m in self._metrics.values())
            total_errors = sum(m.error_count for m in self._metrics.values())
            
            return {
                'total_operations': len(self._metrics),
                'total_calls': total_calls,
                'total_time': total_time,
                'total_errors': total_errors,
                'operation_count': len(self._metrics),
                'average_time_per_call': total_time / max(1, total_calls),
                'error_rate': total_errors / max(1, total_calls),
            }
    
    def get_top_operations(self, limit: int = 10, sort_by: str = 'total_calls') -> list[dict[str, Any]]:
        """
        Get top operations by specified metric.
        
        Args:
            limit: Maximum number of operations to return
            sort_by: Metric to sort by ('total_calls', 'total_time', 'average_time', 'error_count')
            
        Returns:
            List of operation statistics sorted by specified metric
        """
        with self._lock:
            operations = []
            
            for name, metrics in self._metrics.items():
                operations.append({
                    'name': name,
                    'total_calls': metrics.total_calls,
                    'total_time': metrics.total_time,
                    'average_time': metrics.average_time,
                    'min_time': metrics.min_time if metrics.min_time != float('inf') else 0,
                    'max_time': metrics.max_time,
                    'error_count': metrics.error_count,
                    'error_rate': metrics.error_count / max(1, metrics.total_calls),
                    'recent_average': metrics.recent_average,
                })
            
            # Sort by specified metric
            if sort_by == 'total_calls':
                operations.sort(key=lambda x: x['total_calls'], reverse=True)
            elif sort_by == 'total_time':
                operations.sort(key=lambda x: x['total_time'], reverse=True)
            elif sort_by == 'average_time':
                operations.sort(key=lambda x: x['average_time'], reverse=True)
            elif sort_by == 'error_count':
                operations.sort(key=lambda x: x['error_count'], reverse=True)
            else:
                operations.sort(key=lambda x: x['total_calls'], reverse=True)
            
            return operations[:limit]
    
    def add_callback(self, callback: Callable[[str, float, bool], None]):
        """
        Add a callback to be called for each tracked operation.
        
        Args:
            callback: Function that takes (operation_name, duration, success)
        """
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, float, bool], None]):
        """Remove a callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def clear_stats(self, operation_name: Optional[str] = None):
        """
        Clear statistics for an operation or all operations.
        
        Args:
            operation_name: Specific operation to clear, or None to clear all
        """
        with self._lock:
            if operation_name:
                if operation_name in self._metrics:
                    del self._metrics[operation_name]
            else:
                self._metrics.clear()
    
    def reset_stats(self):
        """Reset all statistics."""
        with self._lock:
            for metrics in self._metrics.values():
                metrics.total_calls = 0
                metrics.total_time = 0.0
                metrics.min_time = float('inf')
                metrics.max_time = 0.0
                metrics.recent_times.clear()
                metrics.error_count = 0
    
    def get_metric_snapshot(self) -> MetricSnapshot:
        """Get a snapshot of current metrics."""
        with self._lock:
            summary = self.get_summary_stats()
            
            return MetricSnapshot(
                timestamp=time.time(),
                total_operations=summary['total_operations'],
                total_calls=summary['total_calls'],
                total_time=summary['total_time'],
                total_errors=summary['total_errors'],
                average_time_per_call=summary['average_time_per_call'],
                error_rate=summary['error_rate'],
                operation_details=self._metrics.copy()
            )


# Global operation tracker instance
_global_tracker = OperationTracker()


def get_global_tracker() -> OperationTracker:
    """Get the global operation tracker instance."""
    return _global_tracker


def track_operation(operation_name: str):
    """
    Decorator for tracking operations.
    
    Args:
        operation_name: Name of the operation to track
        
    Example:
        @track_operation("expensive_calculation")
        def calculate_something():
            # Perform calculation
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with _global_tracker.track(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    "OperationTracker",
    "get_global_tracker",
    "track_operation",
]
