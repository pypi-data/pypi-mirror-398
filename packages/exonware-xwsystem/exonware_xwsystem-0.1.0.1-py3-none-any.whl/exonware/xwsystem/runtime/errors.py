#exonware/xwsystem/runtime/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Runtime module errors - exception classes for runtime functionality.
"""


class RuntimeError(Exception):
    """Base exception for runtime errors."""
    pass


class EnvironmentError(RuntimeError):
    """Raised when environment operation fails."""
    pass


class EnvironmentVariableError(EnvironmentError):
    """Raised when environment variable operation fails."""
    pass


class EnvironmentTypeError(EnvironmentError):
    """Raised when environment type is invalid."""
    pass


class PlatformError(RuntimeError):
    """Raised when platform operation fails."""
    pass


class PlatformNotSupportedError(PlatformError):
    """Raised when platform is not supported."""
    pass


class PlatformInfoError(PlatformError):
    """Raised when platform information retrieval fails."""
    pass


class PythonError(RuntimeError):
    """Raised when Python operation fails."""
    pass


class PythonVersionError(PythonError):
    """Raised when Python version is invalid."""
    pass


class PythonPackageError(PythonError):
    """Raised when Python package operation fails."""
    pass


class ReflectionError(RuntimeError):
    """Raised when reflection operation fails."""
    pass


class ClassNotFoundError(ReflectionError):
    """Raised when class is not found."""
    pass


class FunctionNotFoundError(ReflectionError):
    """Raised when function is not found."""
    pass


class ModuleNotFoundError(ReflectionError):
    """Raised when module is not found."""
    pass


class AttributeNotFoundError(ReflectionError):
    """Raised when attribute is not found."""
    pass


class RuntimeConfigError(RuntimeError):
    """Raised when runtime configuration fails."""
    pass


class RuntimeModeError(RuntimeConfigError):
    """Raised when runtime mode is invalid."""
    pass


class RuntimeInitializationError(RuntimeError):
    """Raised when runtime initialization fails."""
    pass


class RuntimeShutdownError(RuntimeError):
    """Raised when runtime shutdown fails."""
    pass