#!/usr/bin/env python3
#exonware/xwsystem/runtime/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Runtime types and enums for XWSystem.
"""

from enum import Enum


# ============================================================================
# RUNTIME ENUMS
# ============================================================================

class EnvironmentType(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    UNKNOWN = "unknown"


class PlatformType(Enum):
    """Platform types."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class PythonVersion(Enum):
    """Python version types."""
    PYTHON_3_8 = "3.8"
    PYTHON_3_9 = "3.9"
    PYTHON_3_10 = "3.10"
    PYTHON_3_11 = "3.11"
    PYTHON_3_12 = "3.12"
    UNKNOWN = "unknown"


class RuntimeMode(Enum):
    """Runtime modes."""
    NORMAL = "normal"
    DEBUG = "debug"
    RELEASE = "release"
    PROFILE = "profile"
    OPTIMIZED = "optimized"
