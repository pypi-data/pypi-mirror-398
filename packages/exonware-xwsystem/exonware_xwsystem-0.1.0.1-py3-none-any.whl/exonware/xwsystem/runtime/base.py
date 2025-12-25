#exonware/xwsystem/runtime/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Runtime module base classes - abstract classes for runtime functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Callable
from .contracts import RuntimeMode, PlatformType, PythonVersion, EnvironmentType


class ARuntimeBase(ABC):
    """Abstract base class for runtime operations."""
    
    def __init__(self, mode: RuntimeMode = RuntimeMode.NORMAL):
        """
        Initialize runtime base.
        
        Args:
            mode: Runtime mode
        """
        self.mode = mode
        self._initialized = False
        self._runtime_info: dict[str, Any] = {}
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize runtime environment."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown runtime environment."""
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        pass
    
    @abstractmethod
    def get_runtime_info(self) -> dict[str, Any]:
        """Get runtime information."""
        pass
    
    def get_platform_info(self) -> dict[str, Any]:
        """Get platform information."""
        return {}
    
    def get_python_info(self) -> dict[str, Any]:
        """Get Python information."""
        return {}
    
    def get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        return {}
    
    def get_memory_info(self) -> dict[str, Any]:
        """Get memory information."""
        return {}
    
    def get_cpu_info(self) -> dict[str, Any]:
        """Get CPU information."""
        return {}


class AEnvironmentBase(ABC):
    """Abstract base class for environment operations."""
    
    def __init__(self):
        """Initialize environment base."""
        self._environment_vars: dict[str, str] = {}
        self._environment_type: EnvironmentType = EnvironmentType.UNKNOWN
    
    @abstractmethod
    def detect_environment(self) -> EnvironmentType:
        """Detect current environment type."""
        pass
    
    @abstractmethod
    def get_environment_type(self) -> EnvironmentType:
        """Get environment type."""
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
    def unset_environment_variable(self, name: str) -> None:
        """Unset environment variable."""
        pass
    
    @abstractmethod
    def get_all_environment_variables(self) -> dict[str, str]:
        """Get all environment variables."""
        pass
    
    @abstractmethod
    def is_development(self) -> bool:
        """Check if in development environment."""
        pass
    
    @abstractmethod
    def is_production(self) -> bool:
        """Check if in production environment."""
        pass
    
    @abstractmethod
    def is_testing(self) -> bool:
        """Check if in testing environment."""
        pass
    
    @abstractmethod
    def get_environment_config(self) -> dict[str, Any]:
        """Get environment configuration."""
        pass


class APlatformBase(ABC):
    """Abstract base class for platform operations."""
    
    def __init__(self):
        """Initialize platform base."""
        self._platform_type: PlatformType = PlatformType.UNKNOWN
        self._platform_info: dict[str, Any] = {}
    
    @abstractmethod
    def detect_platform(self) -> PlatformType:
        """Detect platform type."""
        pass
    
    @abstractmethod
    def get_platform_type(self) -> PlatformType:
        """Get platform type."""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform name."""
        pass
    
    @abstractmethod
    def get_platform_version(self) -> str:
        """Get platform version."""
        pass
    
    @abstractmethod
    def get_platform_architecture(self) -> str:
        """Get platform architecture."""
        pass
    
    @abstractmethod
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        pass
    
    @abstractmethod
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        pass
    
    @abstractmethod
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        pass
    
    @abstractmethod
    def is_unix(self) -> bool:
        """Check if running on Unix-like system."""
        pass
    
    @abstractmethod
    def get_platform_specific_info(self) -> dict[str, Any]:
        """Get platform-specific information."""
        pass


class APythonBase(ABC):
    """Abstract base class for Python operations."""
    
    def __init__(self):
        """Initialize Python base."""
        self._python_version: PythonVersion = PythonVersion.UNKNOWN
        self._python_info: dict[str, Any] = {}
    
    @abstractmethod
    def get_python_version(self) -> PythonVersion:
        """Get Python version."""
        pass
    
    @abstractmethod
    def get_python_version_string(self) -> str:
        """Get Python version string."""
        pass
    
    @abstractmethod
    def get_python_implementation(self) -> str:
        """Get Python implementation."""
        pass
    
    @abstractmethod
    def get_python_path(self) -> str:
        """Get Python executable path."""
        pass
    
    @abstractmethod
    def get_python_paths(self) -> list[str]:
        """Get Python module search paths."""
        pass
    
    @abstractmethod
    def is_python_3(self) -> bool:
        """Check if running Python 3."""
        pass
    
    @abstractmethod
    def is_python_3_8_plus(self) -> bool:
        """Check if running Python 3.8 or higher."""
        pass
    
    @abstractmethod
    def is_python_3_9_plus(self) -> bool:
        """Check if running Python 3.9 or higher."""
        pass
    
    @abstractmethod
    def get_installed_packages(self) -> list[str]:
        """Get list of installed packages."""
        pass
    
    @abstractmethod
    def get_package_info(self, package_name: str) -> dict[str, Any]:
        """Get package information."""
        pass


class AReflectionBase(ABC):
    """Abstract base class for reflection operations."""
    
    def __init__(self):
        """Initialize reflection base."""
        self._module_cache: dict[str, Any] = {}
        self._class_cache: dict[str, type] = {}
    
    @abstractmethod
    def get_class(self, class_name: str, module_name: Optional[str] = None) -> Optional[type]:
        """Get class by name."""
        pass
    
    @abstractmethod
    def get_function(self, function_name: str, module_name: Optional[str] = None) -> Optional[Callable]:
        """Get function by name."""
        pass
    
    @abstractmethod
    def get_module(self, module_name: str) -> Optional[Any]:
        """Get module by name."""
        pass
    
    @abstractmethod
    def get_attribute(self, obj: Any, attribute_name: str) -> Optional[Any]:
        """Get object attribute."""
        pass
    
    @abstractmethod
    def set_attribute(self, obj: Any, attribute_name: str, value: Any) -> None:
        """Set object attribute."""
        pass
    
    @abstractmethod
    def has_attribute(self, obj: Any, attribute_name: str) -> bool:
        """Check if object has attribute."""
        pass
    
    @abstractmethod
    def get_methods(self, obj: Any) -> list[str]:
        """Get object methods."""
        pass
    
    @abstractmethod
    def get_attributes(self, obj: Any) -> list[str]:
        """Get object attributes."""
        pass
    
    @abstractmethod
    def get_class_hierarchy(self, cls: type) -> list[type]:
        """Get class hierarchy."""
        pass
    
    @abstractmethod
    def is_subclass(self, cls: type, parent_cls: type) -> bool:
        """Check if class is subclass of parent."""
        pass
    
    @abstractmethod
    def get_type_info(self, obj: Any) -> dict[str, Any]:
        """Get type information."""
        pass


class ARuntimeManagerBase(ABC):
    """Abstract base class for runtime management."""
    
    def __init__(self):
        """Initialize runtime manager."""
        self._runtime_components: dict[str, Any] = {}
        self._component_states: dict[str, bool] = {}
    
    @abstractmethod
    def register_component(self, name: str, component: Any) -> None:
        """Register runtime component."""
        pass
    
    @abstractmethod
    def unregister_component(self, name: str) -> None:
        """Unregister runtime component."""
        pass
    
    @abstractmethod
    def get_component(self, name: str) -> Optional[Any]:
        """Get runtime component."""
        pass
    
    @abstractmethod
    def list_components(self) -> list[str]:
        """List all registered components."""
        pass
    
    @abstractmethod
    def initialize_component(self, name: str) -> bool:
        """Initialize component."""
        pass
    
    @abstractmethod
    def shutdown_component(self, name: str) -> bool:
        """Shutdown component."""
        pass
    
    @abstractmethod
    def is_component_initialized(self, name: str) -> bool:
        """Check if component is initialized."""
        pass
    
    @abstractmethod
    def get_component_status(self) -> dict[str, bool]:
        """Get status of all components."""
        pass
    
    @abstractmethod
    def initialize_all_components(self) -> dict[str, bool]:
        """Initialize all components."""
        pass
    
    @abstractmethod
    def shutdown_all_components(self) -> dict[str, bool]:
        """Shutdown all components."""
        pass


class BaseRuntime(ARuntimeBase):
    """Base runtime implementation for backward compatibility."""
    
    def __init__(self, mode: RuntimeMode = RuntimeMode.NORMAL):
        """Initialize base runtime."""
        super().__init__(mode)
        self._components = {}
    
    def initialize(self) -> None:
        """Initialize runtime environment."""
        self._initialized = True
        self._runtime_info = {
            "mode": self.mode.value,
            "initialized": True,
            "components": len(self._components)
        }
    
    def shutdown(self) -> None:
        """Shutdown runtime environment."""
        self._initialized = False
        self._runtime_info = {}
        self._components.clear()
    
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        return self._initialized
    
    def get_runtime_info(self) -> dict[str, Any]:
        """Get runtime information."""
        return self._runtime_info.copy()
    
    def get_platform_info(self) -> dict[str, Any]:
        """Get platform information."""
        return {}
    
    def get_python_info(self) -> dict[str, Any]:
        """Get Python information."""
        return {}
    
    def get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        return {}
    
    def get_memory_info(self) -> dict[str, Any]:
        """Get memory information."""
        return {}
    
    def get_cpu_info(self) -> dict[str, Any]:
        """Get CPU information."""
        return {}
    
    def get_mode(self) -> RuntimeMode:
        """Get runtime mode."""
        return self.mode
    
    def set_mode(self, mode: RuntimeMode) -> None:
        """Set runtime mode."""
        self.mode = mode
    
    def register_component(self, name: str, component: Any) -> bool:
        """Register component."""
        self._components[name] = component
        return True
    
    def unregister_component(self, name: str) -> bool:
        """Unregister component."""
        if name in self._components:
            del self._components[name]
            return True
        return False
    
    def get_component(self, name: str) -> Optional[Any]:
        """Get component."""
        return self._components.get(name)
    
    def list_components(self) -> list[str]:
        """List all components."""
        return list(self._components.keys())
    
    def initialize_component(self, name: str) -> bool:
        """Initialize component."""
        component = self._components.get(name)
        if component and hasattr(component, 'initialize'):
            component.initialize()
            return True
        return False
    
    def shutdown_component(self, name: str) -> bool:
        """Shutdown component."""
        component = self._components.get(name)
        if component and hasattr(component, 'shutdown'):
            component.shutdown()
            return True
        return False
    
    def is_component_initialized(self, name: str) -> bool:
        """Check if component is initialized."""
        component = self._components.get(name)
        if component and hasattr(component, 'is_initialized'):
            return component.is_initialized()
        return False
    
    def get_component_status(self) -> dict[str, bool]:
        """Get status of all components."""
        return {name: self.is_component_initialized(name) for name in self._components.keys()}
    
    def initialize_all_components(self) -> dict[str, bool]:
        """Initialize all components."""
        return {name: self.initialize_component(name) for name in self._components.keys()}
    
    def shutdown_all_components(self) -> dict[str, bool]:
        """Shutdown all components."""
        return {name: self.shutdown_component(name) for name in self._components.keys()}