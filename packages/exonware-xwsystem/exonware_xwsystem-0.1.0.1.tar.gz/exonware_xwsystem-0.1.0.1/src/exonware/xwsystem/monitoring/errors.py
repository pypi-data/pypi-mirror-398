#exonware/xwsystem/monitoring/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Monitoring module errors - exception classes for monitoring functionality.
"""


class MonitoringError(Exception):
    """Base exception for monitoring errors."""
    pass


class PerformanceMonitorError(MonitoringError):
    """Raised when performance monitoring fails."""
    pass


class PerformanceMetricError(PerformanceMonitorError):
    """Raised when performance metric operation fails."""
    pass


class PerformanceThresholdError(PerformanceMonitorError):
    """Raised when performance threshold is invalid."""
    pass


class PerformanceValidationError(PerformanceMonitorError):
    """Raised when performance validation fails."""
    pass


class MemoryMonitorError(MonitoringError):
    """Raised when memory monitoring fails."""
    pass


class MemoryLeakError(MemoryMonitorError):
    """Raised when memory leak is detected."""
    pass


class MemorySnapshotError(MemoryMonitorError):
    """Raised when memory snapshot operation fails."""
    pass


class MetricsError(MonitoringError):
    """Raised when metrics operation fails."""
    pass


class MetricsCollectionError(MetricsError):
    """Raised when metrics collection fails."""
    pass


class MetricsStorageError(MetricsError):
    """Raised when metrics storage fails."""
    pass


class ErrorRecoveryError(MonitoringError):
    """Raised when error recovery fails."""
    pass


class CircuitBreakerError(ErrorRecoveryError):
    """Raised when circuit breaker operation fails."""
    pass


class CircuitBreakerStateError(CircuitBreakerError):
    """Raised when circuit breaker state is invalid."""
    pass


class SystemMonitorError(MonitoringError):
    """Raised when system monitoring fails."""
    pass


class SystemResourceError(SystemMonitorError):
    """Raised when system resource monitoring fails."""
    pass


class SystemHealthError(SystemMonitorError):
    """Raised when system health check fails."""
    pass


# ============================================================================
# TRACING ERRORS (Moved from enterprise)
# ============================================================================


class TracingError(MonitoringError):
    """Base exception for tracing operations."""
    pass


class SpanError(TracingError):
    """Raised when span operation fails."""
    pass


class TraceContextError(TracingError):
    """Raised when trace context is invalid."""
    pass


class DistributedTracingError(MonitoringError):
    """Raised when distributed tracing fails."""
    pass