#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Configuration protocol interfaces for XWSystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Iterator, Callable, Protocol
from typing_extensions import runtime_checkable
from pathlib import Path
import os

# Import enums from types module
from .defs import (
    ConfigSource,
    ConfigFormat,
    ConfigPriority,
    ValidationLevel,
    ConfigType,
    LogLevel,
    PerformanceMode,
    AdvancedPerformanceMode
)


# ============================================================================
# CONFIGURATION INTERFACES
# ============================================================================

class IConfigurable(ABC):
    """
    Interface for configurable objects.
    
    Enforces consistent configuration behavior across XWSystem.
    """
    
    @abstractmethod
    def configure(self, **options: Any) -> None:
        """
        Configure object with options.
        
        Args:
            **options: Configuration options
        """
        pass
    
    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        pass
    
    @abstractmethod
    def reset_config(self) -> None:
        """
        Reset configuration to defaults.
        """
        pass
    
    @abstractmethod
    def update_config(self, key: str, value: Any) -> None:
        """
        Update single configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        pass
    
    @abstractmethod
    def has_config(self, key: str) -> bool:
        """
        Check if configuration key exists.
        
        Args:
            key: Configuration key
            
        Returns:
            True if key exists
        """
        pass
    
    @abstractmethod
    def remove_config(self, key: str) -> bool:
        """
        Remove configuration key.
        
        Args:
            key: Configuration key to remove
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def merge_config(self, config: dict[str, Any], priority: ConfigPriority = ConfigPriority.NORMAL) -> None:
        """
        Merge configuration with existing.
        
        Args:
            config: Configuration to merge
            priority: Merge priority
        """
        pass


# ============================================================================
# SETTINGS INTERFACES
# ============================================================================

class ISettings(ABC):
    """
    Interface for settings management.
    
    Enforces consistent settings behavior across XWSystem.
    """
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get setting value.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value
        """
        pass
    
    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        pass
    
    @abstractmethod
    def has_setting(self, key: str) -> bool:
        """
        Check if setting exists.
        
        Args:
            key: Setting key
            
        Returns:
            True if setting exists
        """
        pass
    
    @abstractmethod
    def remove_setting(self, key: str) -> bool:
        """
        Remove setting.
        
        Args:
            key: Setting key to remove
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def get_all_settings(self) -> dict[str, Any]:
        """
        Get all settings.
        
        Returns:
            Dictionary of all settings
        """
        pass
    
    @abstractmethod
    def clear_settings(self) -> None:
        """
        Clear all settings.
        """
        pass
    
    @abstractmethod
    def load_settings(self, source: Union[str, Path, dict[str, Any]]) -> None:
        """
        Load settings from source.
        
        Args:
            source: Settings source (file path, dict, etc.)
        """
        pass
    
    @abstractmethod
    def save_settings(self, destination: Union[str, Path]) -> bool:
        """
        Save settings to destination.
        
        Args:
            destination: Save destination
            
        Returns:
            True if saved successfully
        """
        pass


# ============================================================================
# ENVIRONMENT INTERFACES
# ============================================================================

class IEnvironment(ABC):
    """
    Interface for environment variable management.
    
    Enforces consistent environment behavior across XWSystem.
    """
    
    @abstractmethod
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get environment variable.
        
        Args:
            key: Environment variable key
            default: Default value if not found
            
        Returns:
            Environment variable value
        """
        pass
    
    @abstractmethod
    def set_env(self, key: str, value: Any) -> None:
        """
        Set environment variable.
        
        Args:
            key: Environment variable key
            value: Environment variable value
        """
        pass
    
    @abstractmethod
    def has_env(self, key: str) -> bool:
        """
        Check if environment variable exists.
        
        Args:
            key: Environment variable key
            
        Returns:
            True if exists
        """
        pass
    
    @abstractmethod
    def remove_env(self, key: str) -> bool:
        """
        Remove environment variable.
        
        Args:
            key: Environment variable key to remove
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def load_env(self, file_path: Union[str, Path]) -> None:
        """
        Load environment variables from file.
        
        Args:
            file_path: Environment file path
        """
        pass
    
    @abstractmethod
    def save_env(self, file_path: Union[str, Path]) -> bool:
        """
        Save environment variables to file.
        
        Args:
            file_path: Environment file path
            
        Returns:
            True if saved successfully
        """
        pass
    
    @abstractmethod
    def get_all_env(self) -> dict[str, str]:
        """
        Get all environment variables.
        
        Returns:
            Dictionary of environment variables
        """
        pass
    
    @abstractmethod
    def clear_env(self) -> None:
        """
        Clear all environment variables.
        """
        pass


# ============================================================================
# CONFIGURATION VALIDATION INTERFACES
# ============================================================================

class IConfigValidator(ABC):
    """
    Interface for configuration validation.
    
    Enforces consistent configuration validation across XWSystem.
    """
    
    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
        """
        pass
    
    @abstractmethod
    def get_validation_errors(self, config: dict[str, Any]) -> list[str]:
        """
        Get configuration validation errors.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation error messages
        """
        pass
    
    @abstractmethod
    def add_validation_rule(self, key: str, rule: Callable[[Any], bool], message: str = "") -> None:
        """
        Add validation rule for configuration key.
        
        Args:
            key: Configuration key
            rule: Validation function
            message: Error message if validation fails
        """
        pass
    
    @abstractmethod
    def remove_validation_rule(self, key: str) -> bool:
        """
        Remove validation rule for configuration key.
        
        Args:
            key: Configuration key
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def set_validation_level(self, level: ValidationLevel) -> None:
        """
        Set validation level.
        
        Args:
            level: Validation level
        """
        pass
    
    @abstractmethod
    def get_validation_level(self) -> ValidationLevel:
        """
        Get current validation level.
        
        Returns:
            Current validation level
        """
        pass


# ============================================================================
# CONFIGURATION SOURCE INTERFACES
# ============================================================================

class IConfigSource(ABC):
    """
    Interface for configuration sources.
    
    Enforces consistent configuration source behavior across XWSystem.
    """
    
    @abstractmethod
    def load_config(self) -> dict[str, Any]:
        """
        Load configuration from source.
        
        Returns:
            Configuration dictionary
        """
        pass
    
    @abstractmethod
    def save_config(self, config: dict[str, Any]) -> bool:
        """
        Save configuration to source.
        
        Args:
            config: Configuration to save
            
        Returns:
            True if saved successfully
        """
        pass
    
    @abstractmethod
    def get_source_type(self) -> ConfigSource:
        """
        Get configuration source type.
        
        Returns:
            Source type
        """
        pass
    
    @abstractmethod
    def get_source_info(self) -> dict[str, Any]:
        """
        Get source information.
        
        Returns:
            Source information dictionary
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if source is available.
        
        Returns:
            True if available
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> ConfigPriority:
        """
        Get source priority.
        
        Returns:
            Source priority
        """
        pass


# ============================================================================
# CONFIGURATION MANAGER INTERFACES
# ============================================================================

class IConfigManager(ABC):
    """
    Interface for configuration management.
    
    Enforces consistent configuration management across XWSystem.
    """
    
    @abstractmethod
    def add_source(self, source: IConfigSource) -> None:
        """
        Add configuration source.
        
        Args:
            source: Configuration source to add
        """
        pass
    
    @abstractmethod
    def remove_source(self, source_type: ConfigSource) -> bool:
        """
        Remove configuration source.
        
        Args:
            source_type: Source type to remove
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def load_all_configs(self) -> dict[str, Any]:
        """
        Load configuration from all sources.
        
        Returns:
            Merged configuration dictionary
        """
        pass
    
    @abstractmethod
    def save_all_configs(self, config: dict[str, Any]) -> bool:
        """
        Save configuration to all sources.
        
        Args:
            config: Configuration to save
            
        Returns:
            True if saved to all sources
        """
        pass
    
    @abstractmethod
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value from all sources.
        
        Args:
            key: Configuration key
            default: Default value
            
        Returns:
            Configuration value
        """
        pass
    
    @abstractmethod
    def set_config_value(self, key: str, value: Any) -> None:
        """
        Set configuration value in all sources.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        pass
    
    @abstractmethod
    def reload_config(self) -> None:
        """
        Reload configuration from all sources.
        """
        pass
    
    @abstractmethod
    def get_sources(self) -> list[IConfigSource]:
        """
        Get all configuration sources.
        
        Returns:
            List of configuration sources
        """
        pass


# ============================================================================
# CONFIGURATION WATCHER INTERFACES
# ============================================================================

class IConfigWatcher(ABC):
    """
    Interface for configuration change watching.
    
    Enforces consistent configuration watching across XWSystem.
    """
    
    @abstractmethod
    def start_watching(self) -> None:
        """
        Start watching for configuration changes.
        """
        pass
    
    @abstractmethod
    def stop_watching(self) -> None:
        """
        Stop watching for configuration changes.
        """
        pass
    
    @abstractmethod
    def is_watching(self) -> bool:
        """
        Check if currently watching.
        
        Returns:
            True if watching
        """
        pass
    
    @abstractmethod
    def add_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """
        Add callback for configuration changes.
        
        Args:
            callback: Function to call on changes (key, old_value, new_value)
        """
        pass
    
    @abstractmethod
    def remove_change_callback(self, callback: Callable[[str, Any, Any], None]) -> bool:
        """
        Remove change callback.
        
        Args:
            callback: Callback to remove
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def get_watched_keys(self) -> list[str]:
        """
        Get list of watched configuration keys.
        
        Returns:
            List of watched keys
        """
        pass
    
    @abstractmethod
    def watch_key(self, key: str) -> None:
        """
        Start watching specific configuration key.
        
        Args:
            key: Configuration key to watch
        """
        pass
    
    @abstractmethod
    def unwatch_key(self, key: str) -> None:
        """
        Stop watching specific configuration key.
        
        Args:
            key: Configuration key to stop watching
        """
        pass


# ============================================================================
# CONFIGURATION TEMPLATE INTERFACES
# ============================================================================

class IConfigTemplate(ABC):
    """
    Interface for configuration templates.
    
    Enforces consistent configuration templating across XWSystem.
    """
    
    @abstractmethod
    def create_template(self, config: dict[str, Any]) -> str:
        """
        Create configuration template.
        
        Args:
            config: Configuration to template
            
        Returns:
            Template string
        """
        pass
    
    @abstractmethod
    def apply_template(self, template: str, values: dict[str, Any]) -> dict[str, Any]:
        """
        Apply template with values.
        
        Args:
            template: Template string
            values: Values to apply
            
        Returns:
            Configuration dictionary
        """
        pass
    
    @abstractmethod
    def validate_template(self, template: str) -> bool:
        """
        Validate template syntax.
        
        Args:
            template: Template to validate
            
        Returns:
            True if valid
        """
        pass
    
    @abstractmethod
    def get_template_variables(self, template: str) -> list[str]:
        """
        Get template variables.
        
        Args:
            template: Template string
            
        Returns:
            List of variable names
        """
        pass
    
    @abstractmethod
    def save_template(self, template: str, path: Union[str, Path]) -> bool:
        """
        Save template to file.
        
        Args:
            template: Template string
            path: File path
            
        Returns:
            True if saved successfully
        """
        pass
    
    @abstractmethod
    def load_template(self, path: Union[str, Path]) -> str:
        """
        Load template from file.
        
        Args:
            path: File path
            
        Returns:
            Template string
        """
        pass


# ============================================================================
# CONFIGURATION SECRET INTERFACES
# ============================================================================

class IConfigSecrets(ABC):
    """
    Interface for configuration secrets management.
    
    Enforces consistent secrets handling across XWSystem.
    """
    
    @abstractmethod
    def encrypt_secret(self, value: str) -> str:
        """
        Encrypt secret value.
        
        Args:
            value: Secret value to encrypt
            
        Returns:
            Encrypted secret
        """
        pass
    
    @abstractmethod
    def decrypt_secret(self, encrypted_value: str) -> str:
        """
        Decrypt secret value.
        
        Args:
            encrypted_value: Encrypted secret
            
        Returns:
            Decrypted secret
        """
        pass
    
    @abstractmethod
    def is_secret(self, key: str) -> bool:
        """
        Check if configuration key is secret.
        
        Args:
            key: Configuration key
            
        Returns:
            True if secret
        """
        pass
    
    @abstractmethod
    def mark_as_secret(self, key: str) -> None:
        """
        Mark configuration key as secret.
        
        Args:
            key: Configuration key to mark
        """
        pass
    
    @abstractmethod
    def unmark_as_secret(self, key: str) -> None:
        """
        Unmark configuration key as secret.
        
        Args:
            key: Configuration key to unmark
        """
        pass
    
    @abstractmethod
    def get_secret_keys(self) -> list[str]:
        """
        Get list of secret configuration keys.
        
        Returns:
            List of secret keys
        """
        pass
    
    @abstractmethod
    def sanitize_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize configuration by hiding secrets.
        
        Args:
            config: Configuration to sanitize
            
        Returns:
            Sanitized configuration
        """
        pass


# ============================================================================
# CONFIGURATION PROTOCOLS
# ============================================================================

@runtime_checkable
class Configurable(Protocol):
    """Protocol for objects that support configuration."""
    
    def configure(self, **config: Any) -> None:
        """Configure object with parameters."""
        ...
    
    def get_config(self) -> dict[str, Any]:
        """Get current configuration."""
        ...


# Aliases for backward compatibility
IConfig = IConfigurable
IPerformanceConfig = IConfigurable
ILoggingConfig = IConfigurable
