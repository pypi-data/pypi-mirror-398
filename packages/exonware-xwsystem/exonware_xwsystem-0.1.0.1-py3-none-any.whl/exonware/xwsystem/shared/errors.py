#exonware/xwsystem/shared/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Shared exceptions (merged from the former core module).
"""


class CoreError(Exception):
    """Base exception for core errors."""

    pass


class CoreInitializationError(CoreError):
    """Raised when core initialization fails."""

    pass


class CoreShutdownError(CoreError):
    """Raised when core shutdown fails."""

    pass


class CoreStateError(CoreError):
    """Raised when core state is invalid."""

    pass


class CoreDependencyError(CoreError):
    """Raised when core dependency is missing or invalid."""

    pass


class CoreConfigurationError(CoreError):
    """Raised when core configuration is invalid."""

    pass


class CoreResourceError(CoreError):
    """Raised when core resource operation fails."""

    pass


class CoreTimeoutError(CoreError):
    """Raised when core operation times out."""

    pass


class CorePermissionError(CoreError):
    """Raised when core permission is denied."""

    pass


class CoreValidationError(CoreError):
    """Raised when core validation fails."""

    pass


class CoreOperationError(CoreError):
    """Raised when core operation fails."""

    pass

