"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Default configuration constants for XSystem framework.

These constants provide default values and limits for system operations.
All modules should import from this central location to ensure consistency.
"""

from typing import Final, Any, Optional
from .base import AConfigBase
from .contracts import ConfigType

# ======================
# Core Configuration
# ======================

# Default configuration values
DEFAULT_ENCODING: Final[str] = "utf-8"
DEFAULT_PATH_DELIMITER: Final[str] = "."
DEFAULT_LOCK_TIMEOUT: Final[float] = 10.0

# ======================
# Memory Safety Limits
# ======================

# Memory safety limits
DEFAULT_MAX_FILE_SIZE_MB: Final[int] = 100  # 100MB default limit
DEFAULT_MAX_MEMORY_USAGE_MB: Final[int] = 500  # 500MB default limit
DEFAULT_MAX_DICT_DEPTH: Final[int] = 50  # Maximum nesting depth

# ======================
# Path and Resolution Limits
# ======================

# RG operation safety limits
DEFAULT_MAX_PATH_DEPTH: Final[int] = 20  # Maximum path nesting depth
DEFAULT_MAX_PATH_LENGTH: Final[int] = 500  # Maximum path string length
DEFAULT_MAX_RESOLUTION_DEPTH: Final[int] = (
    10  # Maximum reference resolution depth per get_value call
)
DEFAULT_MAX_TO_DICT_SIZE_MB: Final[int] = 50  # Maximum memory for to_dict operations

# ======================
# Data Structure Limits
# ======================

DEFAULT_MAX_CIRCULAR_DEPTH: Final[int] = 100
DEFAULT_MAX_EXTENSION_LENGTH: Final[int] = 5
DEFAULT_CONTENT_SNIPPET_LENGTH: Final[int] = 200
DEFAULT_MAX_TRAVERSAL_DEPTH: Final[int] = 100

# ======================
# Protocol and Format Identifiers
# ======================

# Protocol and format identifiers
URI_SCHEME_SEPARATOR: Final[str] = "://"
JSON_POINTER_PREFIX: Final[str] = "#"
PATH_SEPARATOR_FORWARD: Final[str] = "/"
PATH_SEPARATOR_BACKWARD: Final[str] = "\\"

# ======================
# Placeholder Messages
# ======================

# Placeholder messages
CIRCULAR_REFERENCE_PLACEHOLDER: Final[str] = "[Circular Reference]"
MAX_DEPTH_EXCEEDED_PLACEHOLDER: Final[str] = "[Max Depth Exceeded]"

# ======================
# Logging Configuration
# ======================

# Logging control
LOGGING_ENABLED: Final[bool] = True
LOGGING_LEVEL: Final[str] = "INFO"


# ======================
# Default Configuration Class
# ======================

class DefaultConfig(AConfigBase):
    """
    Default configuration manager for XSystem framework.
    
    Provides default configuration values and management functionality.
    """
    
    def __init__(self, config_type: ConfigType = ConfigType.DICT):
        """Initialize default configuration."""
        super().__init__(config_type)
        self._defaults = {
            "encoding": DEFAULT_ENCODING,
            "path_delimiter": DEFAULT_PATH_DELIMITER,
            "lock_timeout": DEFAULT_LOCK_TIMEOUT,
            "max_file_size_mb": DEFAULT_MAX_FILE_SIZE_MB,
            "max_memory_usage_mb": DEFAULT_MAX_MEMORY_USAGE_MB,
            "max_dict_depth": DEFAULT_MAX_DICT_DEPTH,
            "max_path_depth": DEFAULT_MAX_PATH_DEPTH,
            "max_path_length": DEFAULT_MAX_PATH_LENGTH,
            "max_resolution_depth": DEFAULT_MAX_RESOLUTION_DEPTH,
            "max_to_dict_size_mb": DEFAULT_MAX_TO_DICT_SIZE_MB,
            "max_circular_depth": DEFAULT_MAX_CIRCULAR_DEPTH,
            "max_extension_length": DEFAULT_MAX_EXTENSION_LENGTH,
            "content_snippet_length": DEFAULT_CONTENT_SNIPPET_LENGTH,
            "max_traversal_depth": DEFAULT_MAX_TRAVERSAL_DEPTH,
            "logging_enabled": LOGGING_ENABLED,
            "logging_level": LOGGING_LEVEL,
        }
        self._config = self._defaults.copy()
    
    def load(self, source: Any = None) -> None:
        """Load configuration from source (defaults are already loaded)."""
        if source is not None:
            if isinstance(source, dict):
                self._config.update(source)
            elif isinstance(source, str):
                # Could implement file loading here
                pass
    
    def save(self, destination: str) -> None:
        """Save configuration to destination."""
        # Could implement file saving here
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
    
    def delete(self, key: str) -> bool:
        """Delete configuration key."""
        if key in self._config:
            del self._config[key]
            return True
        return False
    
    def has(self, key: str) -> bool:
        """Check if configuration key exists."""
        return key in self._config
    
    def keys(self) -> list[str]:
        """Get all configuration keys."""
        return list(self._config.keys())
    
    def values(self) -> list[Any]:
        """Get all configuration values."""
        return list(self._config.values())
    
    def items(self) -> list[tuple[str, Any]]:
        """Get all configuration items."""
        return list(self._config.items())
    
    def clear(self) -> None:
        """Clear all configuration."""
        self._config.clear()
    
    def validate(self) -> bool:
        """Validate configuration."""
        # Basic validation - all values should be non-None
        return all(value is not None for value in self._config.values())
    
    def get_default(self, key: str) -> Any:
        """Get default value for key."""
        return self._defaults.get(key, "default_value")
    
    def set_default(self, key: str, value: Any) -> None:
        """Set default value for key."""
        self._defaults[key] = value
    
    def load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = self._defaults.copy()
