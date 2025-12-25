"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Runtime module contracts - interfaces and enums for runtime environment functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Callable
import sys

# Import enums from types module
from .defs import (
    EnvironmentType,
    PlatformType,
    PythonVersion,
    RuntimeMode
)


class IEnvironmentManager(ABC):
    """Interface for environment management."""
    
    @abstractmethod
    def get_environment_type(self) -> EnvironmentType:
        """Get current environment type."""
        pass
    
    @abstractmethod
    def set_environment_type(self, env_type: EnvironmentType) -> None:
        """Set environment type."""
        pass
    
    @abstractmethod
    def get_environment_variable(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable."""
        pass
    
    @abstractmethod
    def set_environment_variable(self, name: str, value: str) -> None:
        """Set environment variable."""
        pass
    
    @abstractmethod
    def get_all_environment_variables(self) -> dict[str, str]:
        """Get all environment variables."""
        pass


class IPlatformInfo(ABC):
    """Interface for platform information."""
    
    @abstractmethod
    def get_platform_type(self) -> PlatformType:
        """Get platform type."""
        pass
    
    @abstractmethod
    def get_platform_version(self) -> str:
        """Get platform version."""
        pass
    
    @abstractmethod
    def get_architecture(self) -> str:
        """Get system architecture."""
        pass
    
    @abstractmethod
    def get_hostname(self) -> str:
        """Get system hostname."""
        pass
    
    @abstractmethod
    def get_username(self) -> str:
        """Get current username."""
        pass


class IPythonInfo(ABC):
    """Interface for Python information."""
    
    @abstractmethod
    def get_python_version(self) -> PythonVersion:
        """Get Python version."""
        pass
    
    @abstractmethod
    def get_python_executable(self) -> str:
        """Get Python executable path."""
        pass
    
    @abstractmethod
    def get_python_path(self) -> list[str]:
        """Get Python path."""
        pass
    
    @abstractmethod
    def get_installed_packages(self) -> dict[str, str]:
        """Get installed packages."""
        pass
    
    @abstractmethod
    def is_package_installed(self, package_name: str) -> bool:
        """Check if package is installed."""
        pass


class IReflectionUtils(ABC):
    """Interface for reflection utilities."""
    
    @abstractmethod
    def get_class_from_string(self, class_path: str) -> type:
        """Get class from string path."""
        pass
    
    @abstractmethod
    def get_function_from_string(self, function_path: str) -> Callable:
        """Get function from string path."""
        pass
    
    @abstractmethod
    def find_classes_in_module(self, module: Any, base_class: type) -> list[type]:
        """Find classes in module."""
        pass
    
    @abstractmethod
    def get_class_hierarchy(self, cls: type) -> list[type]:
        """Get class hierarchy."""
        pass
    
    @abstractmethod
    def get_class_attributes(self, cls: type) -> dict[str, Any]:
        """Get class attributes."""
        pass


class IRuntimeConfig(ABC):
    """Interface for runtime configuration."""
    
    @abstractmethod
    def get_runtime_mode(self) -> RuntimeMode:
        """Get runtime mode."""
        pass
    
    @abstractmethod
    def set_runtime_mode(self, mode: RuntimeMode) -> None:
        """Set runtime mode."""
        pass
    
    @abstractmethod
    def get_config_value(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set_config_value(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def load_config_from_file(self, file_path: str) -> None:
        """Load configuration from file."""
        pass
    
    @abstractmethod
    def save_config_to_file(self, file_path: str) -> None:
        """Save configuration to file."""
        pass
