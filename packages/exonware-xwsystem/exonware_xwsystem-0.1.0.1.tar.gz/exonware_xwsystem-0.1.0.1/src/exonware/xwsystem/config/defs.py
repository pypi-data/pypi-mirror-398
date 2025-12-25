#!/usr/bin/env python3
#exonware/xwsystem/config/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Config types and enums for XWSystem.
"""

from enum import Enum
from ..shared.defs import ValidationLevel, LogLevel


# ============================================================================
# CONFIGURATION ENUMS
# ============================================================================

class ConfigSource(Enum):
    """Configuration sources."""
    FILE = "file"
    ENVIRONMENT = "environment"
    DEFAULTS = "defaults"
    COMMAND_LINE = "command_line"
    DATABASE = "database"
    API = "api"
    MEMORY = "memory"


class ConfigFormat(Enum):
    """Configuration formats."""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    INI = "ini"
    ENV = "env"
    XML = "xml"
    PYTHON = "python"


class ConfigPriority(Enum):
    """Configuration priority levels."""
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4
    CRITICAL = 5


class ConfigType(Enum):
    """Configuration types."""
    DICT = "dict"
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    API = "api"




class PerformanceMode(Enum):
    """Performance modes."""
    FAST = "fast"
    BALANCED = "balanced"
    MEMORY_OPTIMIZED = "memory_optimized"


class AdvancedPerformanceMode(Enum):
    """Advanced performance optimization modes for system operations."""
    GLOBAL = "global"  # Follow global system settings
    AUTO = "auto"  # Automatic selection based on data characteristics
    PARENT = "parent"  # Inherit from parent object
    DEFAULT = "default"  # Use default balanced settings
    FAST = "fast"  # Prioritize speed over memory
    OPTIMIZED = "optimized"  # Prioritize memory efficiency
    MANUAL = "manual"  # Use specific custom settings
    ADAPTIVE = "adaptive"  # Runtime adaptation based on performance monitoring
    DUAL_ADAPTIVE = "dual_adaptive"  # Smart dual-phase: fast cruise + intelligent deep-dive
