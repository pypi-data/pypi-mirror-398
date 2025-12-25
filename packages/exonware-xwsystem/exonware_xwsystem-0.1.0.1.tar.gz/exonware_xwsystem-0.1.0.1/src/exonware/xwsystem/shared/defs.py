#!/usr/bin/env python3
#exonware/xwsystem/shared/defs.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 10-Sep-2025

Shared types and enums for XWSystem modules.
"""

from enum import Enum


# ============================================================================
# SHARED ENUMS
# ============================================================================

class ValidationLevel(Enum):
    """Standard validation levels used across XWSystem modules."""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"
    COMPREHENSIVE = "comprehensive"  # For structures module


class PerformanceLevel(Enum):
    """Standard performance levels used across XWSystem modules."""
    # Performance module levels
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    
    # Monitoring module levels
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


class AuthType(Enum):
    """Standard authentication types used across XWSystem modules."""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    SAML = "saml"


class LockType(Enum):
    """Standard lock types used across XWSystem modules."""
    # IO module lock types
    SHARED = "shared"
    EXCLUSIVE = "exclusive"
    NON_BLOCKING = "non_blocking"
    
    # Threading module lock types
    MUTEX = "mutex"
    RWLOCK = "rwlock"
    SEMAPHORE = "semaphore"
    CONDITION = "condition"
    EVENT = "event"
    BARRIER = "barrier"


class PathType(Enum):
    """Standard path types used across XWSystem modules."""
    # IO module path types
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    MOUNT = "mount"
    SOCKET = "socket"
    PIPE = "pipe"
    DEVICE = "device"
    
    # Utils module path types
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    RESOLVED = "resolved"
    NORMALIZED = "normalized"


class LogLevel(Enum):
    """Standard logging levels used across XWSystem modules."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OperationResult(Enum):
    """Standard operation result status used across XWSystem modules."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"
    WARNING = "warning"


# ============================================================================
# CORE ENUMS (merged from former xwsystem.core)
# ============================================================================


class DataType(Enum):
    """Core data types supported by XWSystem."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    BYTES = "bytes"
    NONE = "none"
    CUSTOM = "custom"


class CloneMode(Enum):
    """Cloning modes for object duplication."""

    SHALLOW = "shallow"
    DEEP = "deep"
    REFERENCE = "reference"


class CoreState(Enum):
    """Core system states."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


class CoreMode(Enum):
    """Core system modes."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEBUG = "debug"
    PERFORMANCE = "performance"


class CorePriority(Enum):
    """Core system priorities."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"