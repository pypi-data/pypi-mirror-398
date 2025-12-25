#exonware/xwsystem/utils/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Utils module errors - exception classes for utility functionality.
"""


class UtilsError(Exception):
    """Base exception for utils errors."""
    pass


class LazyLoaderError(UtilsError):
    """Raised when lazy loader operation fails."""
    pass


class LazyLoadError(LazyLoaderError):
    """Raised when lazy loading fails."""
    pass


class LazyUnloadError(LazyLoaderError):
    """Raised when lazy unloading fails."""
    pass


class LazyReloadError(LazyLoaderError):
    """Raised when lazy reloading fails."""
    pass


class PathUtilsError(UtilsError):
    """Raised when path utility operation fails."""
    pass


class PathNormalizationError(PathUtilsError):
    """Raised when path normalization fails."""
    pass


class PathResolutionError(PathUtilsError):
    """Raised when path resolution fails."""
    pass


class PathValidationError(PathUtilsError):
    """Raised when path validation fails."""
    pass


class PathSanitizationError(PathUtilsError):
    """Raised when path sanitization fails."""
    pass


class UtilityRegistryError(UtilsError):
    """Raised when utility registry operation fails."""
    pass


class UtilityNotFoundError(UtilityRegistryError):
    """Raised when utility is not found."""
    pass


class UtilityRegistrationError(UtilityRegistryError):
    """Raised when utility registration fails."""
    pass


class UtilityUnregistrationError(UtilityRegistryError):
    """Raised when utility unregistration fails."""
    pass


class ConfigManagerError(UtilsError):
    """Raised when config manager operation fails."""
    pass


class ConfigLoadError(ConfigManagerError):
    """Raised when config loading fails."""
    pass


class ConfigSaveError(ConfigManagerError):
    """Raised when config saving fails."""
    pass


class ConfigValidationError(ConfigManagerError):
    """Raised when config validation fails."""
    pass


class ResourceManagerError(UtilsError):
    """Raised when resource manager operation fails."""
    pass


class ResourceAcquisitionError(ResourceManagerError):
    """Raised when resource acquisition fails."""
    pass


class ResourceReleaseError(ResourceManagerError):
    """Raised when resource release fails."""
    pass


class ResourceNotFoundError(ResourceManagerError):
    """Raised when resource is not found."""
    pass


class ResourceExhaustionError(ResourceManagerError):
    """Raised when resources are exhausted."""
    pass


# Aliases for backward compatibility
PathError = PathUtilsError