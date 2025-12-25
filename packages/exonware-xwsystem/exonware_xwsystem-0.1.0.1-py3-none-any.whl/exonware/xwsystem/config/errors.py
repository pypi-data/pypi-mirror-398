#exonware/xwsystem/config/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Configuration module errors - exception classes for configuration functionality.
"""


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigNotFoundError(ConfigError):
    """Raised when configuration file is not found."""
    pass


class ConfigParseError(ConfigError):
    """Raised when configuration parsing fails."""
    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass


class ConfigKeyError(ConfigError):
    """Raised when configuration key is invalid or not found."""
    pass


class ConfigValueError(ConfigError):
    """Raised when configuration value is invalid."""
    pass


class ConfigTypeError(ConfigError):
    """Raised when configuration type is invalid."""
    pass


class ConfigPermissionError(ConfigError):
    """Raised when configuration permission is denied."""
    pass


class ConfigLockError(ConfigError):
    """Raised when configuration lock operation fails."""
    pass


class ConfigBackupError(ConfigError):
    """Raised when configuration backup operation fails."""
    pass


class ConfigRestoreError(ConfigError):
    """Raised when configuration restore operation fails."""
    pass


class LoggingConfigError(ConfigError):
    """Raised when logging configuration fails."""
    pass


class PerformanceConfigError(ConfigError):
    """Raised when performance configuration fails."""
    pass


# Aliases for backward compatibility
PerformanceError = PerformanceConfigError
LoggingError = LoggingConfigError