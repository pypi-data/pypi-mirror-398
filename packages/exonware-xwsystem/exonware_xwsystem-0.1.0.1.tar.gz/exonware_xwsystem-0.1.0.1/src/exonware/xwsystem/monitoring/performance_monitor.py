"""
Performance Monitoring Utilities for XSystem

These utilities provide performance monitoring, metrics collection, and analysis
capabilities. They were previously embedded in xData and have been extracted for
framework-wide reusability.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, ContextManager, Optional

logger = logging.getLogger(__name__)

# ======================
# Performance Statistics
# ======================


class PerformanceStats:
    """
    Container for performance statistics and metrics.

    This class holds all performance data collected during monitoring,
    providing methods for analysis and reporting.
    """

    def __init__(self) -> None:
        """Initialize empty performance statistics."""
        self.operations_count = 0
        self.total_processing_time = 0.0
        self.memory_usage_samples: list[dict[str, Any]] = []
        self.operation_history: list[dict[str, Any]] = []
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def reset(self) -> None:
        """Reset all statistics to initial state."""
        self.operations_count = 0
        self.total_processing_time = 0.0
        self.memory_usage_samples.clear()
        self.operation_history.clear()
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def to_native(self) -> dict[str, Any]:
        """Convert statistics to dictionary format."""
        return {
            "operations_count": self.operations_count,
            "total_processing_time": self.total_processing_time,
            "memory_usage_samples": self.memory_usage_samples,
            "operation_history": self.operation_history,
            "error_count": self.error_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }

    def from_native(self, data: dict[str, Any]) -> None:
        """Load statistics from dictionary format."""
        self.operations_count = data.get("operations_count", 0)
        self.total_processing_time = data.get("total_processing_time", 0.0)
        self.memory_usage_samples = data.get("memory_usage_samples", [])
        self.operation_history = data.get("operation_history", [])
        self.error_count = data.get("error_count", 0)
        self.cache_hits = data.get("cache_hits", 0)
        self.cache_misses = data.get("cache_misses", 0)

    def add_operation(
        self,
        operation_name: str,
        duration: float,
        success: bool = True,
        memory_usage: Optional[dict[str, Any]] = None,
        **context_data: Any,
    ) -> None:
        """Add operation data to statistics."""
        self.operations_count += 1
        self.total_processing_time += duration

        operation_data = {
            "operation": operation_name,
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
            **context_data,
        }

        self.operation_history.append(operation_data)

        if not success:
            self.error_count += 1

        if memory_usage:
            self.memory_usage_samples.append(memory_usage)

        # Keep only last 100 operations for memory efficiency
        if len(self.operation_history) > 100:
            self.operation_history = self.operation_history[-100:]

    def get_average_processing_time(self) -> float:
        """Get average processing time per operation."""
        if self.operations_count == 0:
            return 0.0
        return self.total_processing_time / self.operations_count

    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.operations_count == 0:
            return 100.0
        successful_operations = self.operations_count - self.error_count
        return (successful_operations / self.operations_count) * 100.0

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        total_cache_operations = self.cache_hits + self.cache_misses
        if total_cache_operations == 0:
            return 0.0
        return (self.cache_hits / total_cache_operations) * 100.0


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection.

    This class provides context managers and methods for monitoring
    performance of operations, collecting metrics, and analyzing results.
    """

    def __init__(self, name: str = "default") -> None:
        """Initialize performance monitor."""
        self.name = name
        self.stats = PerformanceStats()
        self._enabled = True

    def enable(self) -> None:
        """Enable performance monitoring."""
        self._enabled = True

    def disable(self) -> None:
        """Disable performance monitoring."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self._enabled

    def reset_stats(self) -> None:
        """Reset all performance statistics."""
        self.stats.reset()

    def get_stats(self) -> PerformanceStats:
        """Get current performance statistics."""
        return self.stats

    def get_stats_dict(self) -> dict[str, Any]:
        """Get performance statistics as dictionary."""
        return self.stats.to_native()

    def monitor_operation(
        self, operation_name: str, **context_data: Any
    ) -> ContextManager[None]:
        """
        Create a context manager for monitoring an operation.

        Args:
            operation_name: Name of the operation being monitored
            **context_data: Additional context data to store

        Returns:
            Context manager that measures operation duration
        """
        return performance_context(self, operation_name, **context_data)

    def record_operation(
        self,
        operation_name: str,
        duration: float,
        success: bool = True,
        memory_usage: Optional[dict[str, Any]] = None,
        **context_data: Any,
    ) -> None:
        """Record an operation manually."""
        if not self._enabled:
            return

        self.stats.add_operation(
            operation_name, duration, success, memory_usage, **context_data
        )

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        if self._enabled:
            self.stats.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        if self._enabled:
            self.stats.cache_misses += 1

    def get_summary(self) -> dict[str, Any]:
        """Get performance summary."""
        return {
            "monitor_name": self.name,
            "operations_count": self.stats.operations_count,
            "total_processing_time": self.stats.total_processing_time,
            "average_processing_time": self.stats.get_average_processing_time(),
            "success_rate": self.stats.get_success_rate(),
            "error_count": self.stats.error_count,
            "cache_hit_rate": self.stats.get_cache_hit_rate(),
            "cache_hits": self.stats.cache_hits,
            "cache_misses": self.stats.cache_misses,
        }

    def __call__(self, operation_name: str, **context_data: Any) -> ContextManager[None]:
        """Allow using monitor as a callable for context management."""
        return self.monitor_operation(operation_name, **context_data)


def create_performance_monitor(name: str = "default") -> PerformanceMonitor:
    """
    Create a new performance monitor instance.

    Args:
        name: Name for the monitor instance

    Returns:
        New PerformanceMonitor instance
    """
    return PerformanceMonitor(name)


@contextmanager
def performance_context(monitor: PerformanceMonitor, operation_name: str, **context_data: Any):
    """
    Context manager for performance monitoring.

    Args:
        monitor: Performance monitor instance
        operation_name: Name of the operation being monitored
        **context_data: Additional context data to store

    Yields:
        None
    """
    if not monitor.is_enabled():
        yield
        return

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
        monitor.record_operation(
            operation_name,
            duration,
            success=success,
            error=str(error) if error else None,
            **context_data,
        )


def enhanced_error_context(operation: str, **context_data: Any) -> ContextManager[None]:
    """
    Enhanced error context with performance monitoring.

    Args:
        operation: Name of the operation
        **context_data: Additional context data

    Returns:
        Context manager that provides error handling and performance monitoring
    """
    start_time = time.time()

    class ErrorContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - start_time
            if exc_type is not None:
                logger.error(
                    f"Operation '{operation}' failed after {duration:.3f}s: {exc_val}",
                    extra={"operation": operation, "duration": duration, **context_data},
                )
            else:
                logger.debug(
                    f"Operation '{operation}' completed in {duration:.3f}s",
                    extra={"operation": operation, "duration": duration, **context_data},
                )

    return ErrorContext()


def calculate_performance_summary(stats: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate performance summary from statistics.

    Args:
        stats: Performance statistics dictionary

    Returns:
        Calculated performance summary
    """
    operations_count = stats.get("operations_count", 0)
    total_time = stats.get("total_processing_time", 0.0)
    error_count = stats.get("error_count", 0)

    summary = {
        "operations_count": operations_count,
        "total_processing_time": total_time,
        "average_processing_time": total_time / operations_count if operations_count > 0 else 0.0,
        "success_rate": ((operations_count - error_count) / operations_count * 100) if operations_count > 0 else 100.0,
        "error_count": error_count,
    }

    # Add cache statistics if available
    cache_hits = stats.get("cache_hits", 0)
    cache_misses = stats.get("cache_misses", 0)
    total_cache_ops = cache_hits + cache_misses

    if total_cache_ops > 0:
        summary.update({
            "cache_hit_rate": (cache_hits / total_cache_ops) * 100,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
        })

    return summary


def format_performance_report(
    stats: dict[str, Any], include_history: bool = False
) -> str:
    """
    Format performance statistics as a readable report.

    Args:
        stats: Performance statistics dictionary
        include_history: Whether to include operation history

    Returns:
        Formatted performance report string
    """
    summary = calculate_performance_summary(stats)

    report_lines = [
        "Performance Report",
        "=" * 50,
        f"Operations: {summary['operations_count']}",
        f"Total Time: {summary['total_processing_time']:.3f}s",
        f"Average Time: {summary['average_processing_time']:.3f}s",
        f"Success Rate: {summary['success_rate']:.1f}%",
        f"Errors: {summary['error_count']}",
    ]

    if "cache_hit_rate" in summary:
        report_lines.extend([
            f"Cache Hit Rate: {summary['cache_hit_rate']:.1f}%",
            f"Cache Hits: {summary['cache_hits']}",
            f"Cache Misses: {summary['cache_misses']}",
        ])

    if include_history and "operation_history" in stats:
        report_lines.extend([
            "",
            "Recent Operations:",
            "-" * 30,
        ])

        operation_history = stats["operation_history"]
        for op in operation_history[-5:]:
            status = "✓" if op.get("success", True) else "✗"
            report_lines.append(
                f"  {status} {op.get('operation', 'unknown')}: {op.get('duration', 0.0):.3f}s"
            )

    return "\n".join(report_lines)


# Global performance monitor instance
performance_monitor = PerformanceMonitor("global")