"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Utils module contracts - interfaces and enums for utility functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Callable
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity
from pathlib import Path

# Import enums from types module
from .defs import (
    LazyLoadStrategy,
    LazyLoadMode,
    UtilityType,
    ResourceType,
    PathType
)


class ILazyLoader[T](ABC):
    """Interface for lazy loading operations."""
    
    @abstractmethod
    def load(self) -> T:
        """Load the object."""
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if object is loaded."""
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """Unload the object."""
        pass
    
    @abstractmethod
    def reload(self) -> T:
        """Reload the object."""
        pass
    
    @abstractmethod
    def get_loader_function(self) -> Callable[[], T]:
        """Get the loader function."""
        pass


class IPathUtils(ABC):
    """Interface for path utility operations."""
    
    @abstractmethod
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path."""
        pass
    
    @abstractmethod
    def resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve path to absolute."""
        pass
    
    @abstractmethod
    def get_path_type(self, path: Union[str, Path]) -> PathType:
        """Get path type."""
        pass
    
    @abstractmethod
    def is_safe_path(self, path: Union[str, Path]) -> bool:
        """Check if path is safe."""
        pass
    
    @abstractmethod
    def sanitize_path(self, path: Union[str, Path]) -> Path:
        """Sanitize path."""
        pass
    
    @abstractmethod
    def get_relative_path(self, path: Union[str, Path], base: Union[str, Path]) -> Path:
        """Get relative path."""
        pass
    
    @abstractmethod
    def ensure_path_exists(self, path: Union[str, Path]) -> None:
        """Ensure path exists."""
        pass


class IUtilityRegistry(ABC):
    """Interface for utility registry operations."""
    
    @abstractmethod
    def register_utility(self, name: str, utility: Any) -> None:
        """Register utility."""
        pass
    
    @abstractmethod
    def get_utility(self, name: str) -> Optional[Any]:
        """Get utility by name."""
        pass
    
    @abstractmethod
    def unregister_utility(self, name: str) -> None:
        """Unregister utility."""
        pass
    
    @abstractmethod
    def list_utilities(self) -> list[str]:
        """List all registered utilities."""
        pass
    
    @abstractmethod
    def has_utility(self, name: str) -> bool:
        """Check if utility is registered."""
        pass


class IConfigManager(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get_config(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def load_config(self, source: Union[str, Path, dict[str, Any]]) -> None:
        """Load configuration from source."""
        pass
    
    @abstractmethod
    def save_config(self, destination: Union[str, Path]) -> None:
        """Save configuration to destination."""
        pass
    
    @abstractmethod
    def get_all_config(self) -> dict[str, Any]:
        """Get all configuration."""
        pass
    
    @abstractmethod
    def clear_config(self) -> None:
        """Clear all configuration."""
        pass


class IResourceManager(ABC):
    """Interface for resource management."""
    
    @abstractmethod
    def acquire_resource(self, resource_id: str) -> Any:
        """Acquire resource."""
        pass
    
    @abstractmethod
    def release_resource(self, resource_id: str) -> None:
        """Release resource."""
        pass
    
    @abstractmethod
    def is_resource_available(self, resource_id: str) -> bool:
        """Check if resource is available."""
        pass
    
    @abstractmethod
    def get_resource_count(self) -> int:
        """Get total resource count."""
        pass
    
    @abstractmethod
    def get_available_resources(self) -> list[str]:
        """Get list of available resources."""
        pass
