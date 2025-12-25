"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

XSystem Runtime Package

Provides runtime utilities for environment detection, path management,
and reflection capabilities.
"""

from .env import EnvironmentManager
from .reflection import ReflectionUtils
from .base import (
    ARuntimeBase,
    AEnvironmentBase,
    APlatformBase,
    APythonBase,
    AReflectionBase,
    ARuntimeManagerBase,
    BaseRuntime,
)
from .contracts import (
    EnvironmentType,
    PlatformType,
    PythonVersion,
    RuntimeMode,
    IEnvironmentManager,
    IPlatformInfo,
    IPythonInfo,
    IReflectionUtils,
    IRuntimeConfig,
)
from .errors import (
    RuntimeError,
    EnvironmentError,
    EnvironmentVariableError,
    EnvironmentTypeError,
    PlatformError,
    PlatformNotSupportedError,
    PlatformInfoError,
    PythonError,
    PythonVersionError,
    PythonPackageError,
    ReflectionError,
    ClassNotFoundError,
    FunctionNotFoundError,
    ModuleNotFoundError,
    AttributeNotFoundError,
    RuntimeConfigError,
    RuntimeModeError,
    RuntimeInitializationError,
    RuntimeShutdownError,
)

__all__ = [
    # Main classes
    "EnvironmentManager",
    "ReflectionUtils",
    "BaseRuntime",
    
    # Abstract base classes
    "ARuntimeBase",
    "AEnvironmentBase",
    "APlatformBase",
    "APythonBase",
    "AReflectionBase",
    "ARuntimeManagerBase",
    
    # Enums
    "EnvironmentType",
    "PlatformType",
    "PythonVersion",
    "RuntimeMode",
    
    # Interfaces
    "IEnvironmentManager",
    "IPlatformInfo",
    "IPythonInfo",
    "IReflectionUtils",
    "IRuntimeConfig",
    
    # Exceptions
    "RuntimeError",
    "EnvironmentError",
    "EnvironmentVariableError",
    "EnvironmentTypeError",
    "PlatformError",
    "PlatformNotSupportedError",
    "PlatformInfoError",
    "PythonError",
    "PythonVersionError",
    "PythonPackageError",
    "ReflectionError",
    "ClassNotFoundError",
    "FunctionNotFoundError",
    "ModuleNotFoundError",
    "AttributeNotFoundError",
    "RuntimeConfigError",
    "RuntimeModeError",
    "RuntimeInitializationError",
    "RuntimeShutdownError",
]
