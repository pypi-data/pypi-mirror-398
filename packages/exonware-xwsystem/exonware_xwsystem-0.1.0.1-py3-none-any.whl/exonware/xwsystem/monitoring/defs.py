#!/usr/bin/env python3
#exonware/xwsystem/monitoring/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Monitoring types and enums for XWSystem.
"""

from enum import Enum
from ..shared.defs import PerformanceLevel


# ============================================================================
# MONITORING ENUMS
# ============================================================================

class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"
    RATE = "rate"


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


class AlertLevel(Enum):
    """Alert levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MonitoringMode(Enum):
    """Monitoring modes."""
    PASSIVE = "passive"
    ACTIVE = "active"
    CONTINUOUS = "continuous"
    ON_DEMAND = "on_demand"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class SpanKind(Enum):
    """Span kinds for different operation types."""
    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"