#exonware/xwsystem/config/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Config module base classes - abstract classes for configuration functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from .contracts import ConfigType, LogLevel, PerformanceMode


class AConfigBase(ABC):
    """Abstract base class for configuration management."""
    
    def __init__(self, config_type: ConfigType = ConfigType.DICT):
        """
        Initialize configuration base.
        
        Args:
            config_type: Configuration type
        """
        self.config_type = config_type
        self._config: dict[str, Any] = {}
        self._defaults: dict[str, Any] = {}
    
    @abstractmethod
    def load(self, source: Union[str, dict[str, Any]]) -> None:
        """Load configuration from source."""
        pass
    
    @abstractmethod
    def save(self, destination: str) -> None:
        """Save configuration to destination."""
        pass
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete configuration key."""
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if configuration key exists."""
        pass
    
    @abstractmethod
    def keys(self) -> list[str]:
        """Get all configuration keys."""
        pass
    
    @abstractmethod
    def values(self) -> list[Any]:
        """Get all configuration values."""
        pass
    
    @abstractmethod
    def items(self) -> list[tuple[str, Any]]:
        """Get all configuration items."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all configuration."""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate configuration."""
        pass


class ALoggingConfigBase(ABC):
    """Abstract base class for logging configuration."""
    
    @abstractmethod
    def setup_logging(self, level: LogLevel = LogLevel.INFO, **kwargs) -> None:
        """Setup logging configuration."""
        pass
    
    @abstractmethod
    def get_logger(self, name: str) -> Any:
        """Get logger instance."""
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """Set logging level."""
        pass
    
    @abstractmethod
    def add_handler(self, handler: Any) -> None:
        """Add logging handler."""
        pass
    
    @abstractmethod
    def remove_handler(self, handler: Any) -> None:
        """Remove logging handler."""
        pass
    
    @abstractmethod
    def configure_formatter(self, format_string: str) -> None:
        """Configure log formatter."""
        pass


class APerformanceConfigBase(ABC):
    """Abstract base class for performance configuration."""
    
    def __init__(self, mode: PerformanceMode = PerformanceMode.BALANCED):
        """
        Initialize performance configuration.
        
        Args:
            mode: Performance mode
        """
        self.mode = mode
        self._settings: dict[str, Any] = {}
    
    @abstractmethod
    def set_mode(self, mode: PerformanceMode) -> None:
        """Set performance mode."""
        pass
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get performance setting."""
        pass
    
    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """Set performance setting."""
        pass
    
    @abstractmethod
    def optimize_for_mode(self) -> None:
        """Optimize settings for current mode."""
        pass
    
    @abstractmethod
    def get_benchmark_config(self) -> dict[str, Any]:
        """Get benchmark configuration."""
        pass
    
    @abstractmethod
    def validate_settings(self) -> bool:
        """Validate performance settings."""
        pass


class AConfigValidatorBase(ABC):
    """Abstract base class for configuration validation."""
    
    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate configuration dictionary."""
        pass
    
    @abstractmethod
    def validate_key(self, key: str, value: Any) -> bool:
        """Validate configuration key-value pair."""
        pass
    
    @abstractmethod
    def get_validation_errors(self) -> list[str]:
        """Get validation errors."""
        pass
    
    @abstractmethod
    def clear_errors(self) -> None:
        """Clear validation errors."""
        pass
    
    @abstractmethod
    def add_validation_rule(self, key: str, rule: callable) -> None:
        """Add validation rule for key."""
        pass
    
    @abstractmethod
    def remove_validation_rule(self, key: str) -> None:
        """Remove validation rule for key."""
        pass


class AConfigManagerBase(ABC):
    """Abstract base class for configuration management."""
    
    @abstractmethod
    def create_config(self, name: str, config_type: ConfigType) -> AConfigBase:
        """Create new configuration instance."""
        pass
    
    @abstractmethod
    def get_config(self, name: str) -> Optional[AConfigBase]:
        """Get configuration instance by name."""
        pass
    
    @abstractmethod
    def remove_config(self, name: str) -> bool:
        """Remove configuration instance."""
        pass
    
    @abstractmethod
    def list_configs(self) -> list[str]:
        """List all configuration names."""
        pass
    
    @abstractmethod
    def backup_config(self, name: str, backup_path: str) -> None:
        """Backup configuration."""
        pass
    
    @abstractmethod
    def restore_config(self, name: str, backup_path: str) -> None:
        """Restore configuration from backup."""
        pass


# Concrete implementation for backward compatibility
class BaseConfig(AConfigBase):
    """Concrete implementation of AConfigBase for backward compatibility."""
    
    def load(self, source: Any = None) -> None:
        """Load configuration from source."""
        if isinstance(source, dict):
            self._config.update(source)
        elif isinstance(source, str):
            # Could implement file loading here
            pass
    
    def save(self, destination: str = None) -> None:
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
        return True