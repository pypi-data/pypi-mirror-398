#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Monitoring protocol interfaces for XWSystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Iterator, Callable, Protocol
from typing_extensions import runtime_checkable
import time

# Import enums from types module
from .defs import (
    MetricType,
    HealthStatus,
    AlertLevel,
    MonitoringMode,
    PerformanceLevel,
    CircuitState
)


# ============================================================================
# PERFORMANCE INTERFACES
# ============================================================================

class IPerformance(ABC):
    """
    Interface for performance monitoring.
    
    Enforces consistent performance monitoring across XWSystem.
    """
    
    @abstractmethod
    def start_timer(self, operation: str) -> str:
        """
        Start performance timer.
        
        Args:
            operation: Operation name
            
        Returns:
            Timer ID
        """
        pass
    
    @abstractmethod
    def end_timer(self, timer_id: str) -> float:
        """
        End performance timer.
        
        Args:
            timer_id: Timer ID
            
        Returns:
            Elapsed time in seconds
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        pass
    
    @abstractmethod
    def reset_metrics(self) -> None:
        """
        Reset performance metrics.
        """
        pass
    
    @abstractmethod
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE) -> None:
        """
        Record performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
        """
        pass
    
    @abstractmethod
    def get_metric(self, name: str) -> Optional[float]:
        """
        Get performance metric value.
        
        Args:
            name: Metric name
            
        Returns:
            Metric value or None
        """
        pass
    
    @abstractmethod
    def get_performance_level(self) -> PerformanceLevel:
        """
        Get current performance level.
        
        Returns:
            Current performance level
        """
        pass
    
    @abstractmethod
    def set_performance_threshold(self, metric: str, threshold: float) -> None:
        """
        Set performance threshold.
        
        Args:
            metric: Metric name
            threshold: Threshold value
        """
        pass
    
    @abstractmethod
    def is_performance_acceptable(self) -> bool:
        """
        Check if performance is acceptable.
        
        Returns:
            True if performance is acceptable
        """
        pass


# ============================================================================
# MONITORABLE INTERFACES
# ============================================================================

class IMonitorable(ABC):
    """
    Interface for monitorable objects.
    
    Enforces consistent monitoring behavior across XWSystem.
    """
    
    @abstractmethod
    def start_monitoring(self) -> None:
        """
        Start monitoring.
        """
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> None:
        """
        Stop monitoring.
        """
        pass
    
    @abstractmethod
    def get_status(self) -> HealthStatus:
        """
        Get current status.
        
        Returns:
            Current health status
        """
        pass
    
    @abstractmethod
    def get_health(self) -> dict[str, Any]:
        """
        Get health information.
        
        Returns:
            Health information dictionary
        """
        pass
    
    @abstractmethod
    def is_monitoring(self) -> bool:
        """
        Check if monitoring is active.
        
        Returns:
            True if monitoring is active
        """
        pass
    
    @abstractmethod
    def get_monitoring_info(self) -> dict[str, Any]:
        """
        Get monitoring information.
        
        Returns:
            Monitoring information dictionary
        """
        pass
    
    @abstractmethod
    def set_monitoring_interval(self, interval: float) -> None:
        """
        Set monitoring interval.
        
        Args:
            interval: Monitoring interval in seconds
        """
        pass
    
    @abstractmethod
    def get_monitoring_interval(self) -> float:
        """
        Get monitoring interval.
        
        Returns:
            Monitoring interval in seconds
        """
        pass


# ============================================================================
# METRICS INTERFACES
# ============================================================================

class IMetrics(ABC):
    """
    Interface for metrics collection.
    
    Enforces consistent metrics behavior across XWSystem.
    """
    
    @abstractmethod
    def collect_metrics(self) -> dict[str, Any]:
        """
        Collect all metrics.
        
        Returns:
            Dictionary of collected metrics
        """
        pass
    
    @abstractmethod
    def add_metric(self, name: str, value: Any, labels: Optional[dict[str, str]] = None) -> None:
        """
        Add metric.
        
        Args:
            name: Metric name
            value: Metric value
            labels: Optional metric labels
        """
        pass
    
    @abstractmethod
    def get_metric(self, name: str) -> Optional[Any]:
        """
        Get metric value.
        
        Args:
            name: Metric name
            
        Returns:
            Metric value or None
        """
        pass
    
    @abstractmethod
    def remove_metric(self, name: str) -> bool:
        """
        Remove metric.
        
        Args:
            name: Metric name to remove
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def list_metrics(self) -> list[str]:
        """
        List all metric names.
        
        Returns:
            List of metric names
        """
        pass
    
    @abstractmethod
    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in specified format.
        
        Args:
            format: Export format
            
        Returns:
            Exported metrics string
        """
        pass
    
    @abstractmethod
    def clear_metrics(self) -> None:
        """
        Clear all metrics.
        """
        pass
    
    @abstractmethod
    def get_metrics_summary(self) -> dict[str, Any]:
        """
        Get metrics summary.
        
        Returns:
            Metrics summary dictionary
        """
        pass


# ============================================================================
# HEALTH CHECK INTERFACES
# ============================================================================

class IHealthCheck(ABC):
    """
    Interface for health checks.
    
    Enforces consistent health checking across XWSystem.
    """
    
    @abstractmethod
    def check_health(self) -> HealthStatus:
        """
        Perform health check.
        
        Returns:
            Health status
        """
        pass
    
    @abstractmethod
    def get_health_details(self) -> dict[str, Any]:
        """
        Get detailed health information.
        
        Returns:
            Health details dictionary
        """
        pass
    
    @abstractmethod
    def add_health_check(self, name: str, check_func: Callable[[], HealthStatus]) -> None:
        """
        Add health check function.
        
        Args:
            name: Health check name
            check_func: Health check function
        """
        pass
    
    @abstractmethod
    def remove_health_check(self, name: str) -> bool:
        """
        Remove health check.
        
        Args:
            name: Health check name
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def list_health_checks(self) -> list[str]:
        """
        List all health check names.
        
        Returns:
            List of health check names
        """
        pass
    
    @abstractmethod
    def run_health_checks(self) -> dict[str, HealthStatus]:
        """
        Run all health checks.
        
        Returns:
            Dictionary of health check results
        """
        pass
    
    @abstractmethod
    def get_overall_health(self) -> HealthStatus:
        """
        Get overall health status.
        
        Returns:
            Overall health status
        """
        pass
    
    @abstractmethod
    def set_health_threshold(self, check_name: str, threshold: float) -> None:
        """
        Set health check threshold.
        
        Args:
            check_name: Health check name
            threshold: Threshold value
        """
        pass


# ============================================================================
# ALERTING INTERFACES
# ============================================================================

class IAlerting(ABC):
    """
    Interface for alerting.
    
    Enforces consistent alerting behavior across XWSystem.
    """
    
    @abstractmethod
    def create_alert(self, message: str, level: AlertLevel, source: str = "") -> str:
        """
        Create alert.
        
        Args:
            message: Alert message
            level: Alert level
            source: Alert source
            
        Returns:
            Alert ID
        """
        pass
    
    @abstractmethod
    def get_alert(self, alert_id: str) -> Optional[dict[str, Any]]:
        """
        Get alert by ID.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Alert information or None
        """
        pass
    
    @abstractmethod
    def list_alerts(self, level: Optional[AlertLevel] = None) -> list[dict[str, Any]]:
        """
        List alerts.
        
        Args:
            level: Filter by alert level
            
        Returns:
            List of alert information
        """
        pass
    
    @abstractmethod
    def acknowledge_alert(self, alert_id: str, user: str = "") -> bool:
        """
        Acknowledge alert.
        
        Args:
            alert_id: Alert ID
            user: User acknowledging alert
            
        Returns:
            True if acknowledged
        """
        pass
    
    @abstractmethod
    def resolve_alert(self, alert_id: str, resolution: str = "") -> bool:
        """
        Resolve alert.
        
        Args:
            alert_id: Alert ID
            resolution: Resolution description
            
        Returns:
            True if resolved
        """
        pass
    
    @abstractmethod
    def clear_alert(self, alert_id: str) -> bool:
        """
        Clear alert.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if cleared
        """
        pass
    
    @abstractmethod
    def get_alert_stats(self) -> dict[str, int]:
        """
        Get alert statistics.
        
        Returns:
            Alert statistics dictionary
        """
        pass
    
    @abstractmethod
    def set_alert_threshold(self, metric: str, threshold: float, level: AlertLevel) -> None:
        """
        Set alert threshold.
        
        Args:
            metric: Metric name
            threshold: Threshold value
            level: Alert level
        """
        pass


# ============================================================================
# SYSTEM MONITORING INTERFACES
# ============================================================================

class ISystemMonitor(ABC):
    """
    Interface for system monitoring.
    
    Enforces consistent system monitoring across XWSystem.
    """
    
    @abstractmethod
    def get_cpu_usage(self) -> float:
        """
        Get CPU usage percentage.
        
        Returns:
            CPU usage percentage
        """
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> dict[str, Any]:
        """
        Get memory usage information.
        
        Returns:
            Memory usage dictionary
        """
        pass
    
    @abstractmethod
    def get_disk_usage(self) -> dict[str, Any]:
        """
        Get disk usage information.
        
        Returns:
            Disk usage dictionary
        """
        pass
    
    @abstractmethod
    def get_network_usage(self) -> dict[str, Any]:
        """
        Get network usage information.
        
        Returns:
            Network usage dictionary
        """
        pass
    
    @abstractmethod
    def get_process_info(self) -> list[dict[str, Any]]:
        """
        Get process information.
        
        Returns:
            List of process information
        """
        pass
    
    @abstractmethod
    def get_system_load(self) -> float:
        """
        Get system load average.
        
        Returns:
            System load average
        """
        pass
    
    @abstractmethod
    def get_uptime(self) -> float:
        """
        Get system uptime.
        
        Returns:
            Uptime in seconds
        """
        pass
    
    @abstractmethod
    def get_system_info(self) -> dict[str, Any]:
        """
        Get system information.
        
        Returns:
            System information dictionary
        """
        pass


# ============================================================================
# PERFORMANCE PROFILING INTERFACES
# ============================================================================

class IProfiler(ABC):
    """
    Interface for performance profiling.
    
    Enforces consistent profiling behavior across XWSystem.
    """
    
    @abstractmethod
    def start_profiling(self, name: str) -> str:
        """
        Start profiling session.
        
        Args:
            name: Profiling session name
            
        Returns:
            Profiling session ID
        """
        pass
    
    @abstractmethod
    def stop_profiling(self, session_id: str) -> dict[str, Any]:
        """
        Stop profiling session.
        
        Args:
            session_id: Profiling session ID
            
        Returns:
            Profiling results
        """
        pass
    
    @abstractmethod
    def profile_function(self, func: Callable, *args, **kwargs) -> tuple[Any, dict[str, Any]]:
        """
        Profile function execution.
        
        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (result, profiling_data)
        """
        pass
    
    @abstractmethod
    def get_profiling_results(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Get profiling results.
        
        Args:
            session_id: Profiling session ID
            
        Returns:
            Profiling results or None
        """
        pass
    
    @abstractmethod
    def list_profiling_sessions(self) -> list[str]:
        """
        List profiling sessions.
        
        Returns:
            List of session IDs
        """
        pass
    
    @abstractmethod
    def clear_profiling_data(self) -> None:
        """
        Clear profiling data.
        """
        pass
    
    @abstractmethod
    def export_profiling_data(self, session_id: str, format: str = "json") -> str:
        """
        Export profiling data.
        
        Args:
            session_id: Profiling session ID
            format: Export format
            
        Returns:
            Exported profiling data
        """
        pass


# ============================================================================
# MONITORING CONFIGURATION INTERFACES
# ============================================================================

class IMonitoringConfig(ABC):
    """
    Interface for monitoring configuration.
    
    Enforces consistent monitoring configuration across XWSystem.
    """
    
    @abstractmethod
    def set_monitoring_mode(self, mode: MonitoringMode) -> None:
        """
        Set monitoring mode.
        
        Args:
            mode: Monitoring mode
        """
        pass
    
    @abstractmethod
    def get_monitoring_mode(self) -> MonitoringMode:
        """
        Get monitoring mode.
        
        Returns:
            Current monitoring mode
        """
        pass
    
    @abstractmethod
    def set_metric_interval(self, metric: str, interval: float) -> None:
        """
        Set metric collection interval.
        
        Args:
            metric: Metric name
            interval: Collection interval in seconds
        """
        pass
    
    @abstractmethod
    def get_metric_interval(self, metric: str) -> Optional[float]:
        """
        Get metric collection interval.
        
        Args:
            metric: Metric name
            
        Returns:
            Collection interval or None
        """
        pass
    
    @abstractmethod
    def enable_metric(self, metric: str) -> None:
        """
        Enable metric collection.
        
        Args:
            metric: Metric name
        """
        pass
    
    @abstractmethod
    def disable_metric(self, metric: str) -> None:
        """
        Disable metric collection.
        
        Args:
            metric: Metric name
        """
        pass
    
    @abstractmethod
    def is_metric_enabled(self, metric: str) -> bool:
        """
        Check if metric is enabled.
        
        Args:
            metric: Metric name
            
        Returns:
            True if enabled
        """
        pass
    
    @abstractmethod
    def get_monitoring_config(self) -> dict[str, Any]:
        """
        Get monitoring configuration.
        
        Returns:
            Monitoring configuration dictionary
        """
        pass
    
    @abstractmethod
    def set_monitoring_config(self, config: dict[str, Any]) -> None:
        """
        Set monitoring configuration.
        
        Args:
            config: Monitoring configuration
        """
        pass


# ============================================================================
# MONITORING PROTOCOLS
# ============================================================================

@runtime_checkable
class Monitorable(Protocol):
    """Protocol for objects that support performance monitoring."""
    
    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        ...
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        ...
    
    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics."""
        ...
