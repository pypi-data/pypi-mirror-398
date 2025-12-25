#exonware/xwsystem/plugins/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Plugin system base classes and management.
"""

import importlib
import importlib.util
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from importlib.metadata import entry_points

from ..config.logging_setup import get_logger
from ..runtime.reflection import ReflectionUtils
from .contracts import IPlugin, PluginState, PluginType, PluginPriority
from .errors import PluginError

logger = get_logger("xwsystem.plugins.base")


@dataclass
class APluginInfo:
    """Information about a plugin."""
    
    name: str
    version: str = "unknown"
    description: str = ""
    author: str = ""
    module_path: str = ""
    class_name: str = ""
    enabled: bool = True
    priority: int = 100
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class APlugin(IPlugin):
    """
    Abstract base class for all plugins.
    
    Plugins should inherit from this class and implement the required methods.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize plugin with optional configuration.

        Args:
            config: Plugin configuration dictionary
        """
        self.config = config or {}
        self.enabled = True
        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass

    @property
    def description(self) -> str:
        """Plugin description."""
        return ""

    @property
    def author(self) -> str:
        """Plugin author."""
        return ""

    @property
    def dependencies(self) -> list[str]:
        """List of plugin dependencies."""
        return []

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass

    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized

    def get_info(self) -> dict[str, Any]:
        """Get plugin information."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'dependencies': self.dependencies,
            'enabled': self.enabled,
            'state': self.get_state().value,
            'plugin_type': self.get_plugin_type().value,
            'priority': self.get_priority().value,
        }

    def get_state(self) -> PluginState:
        """Get plugin state."""
        if not self._initialized:
            return PluginState.UNLOADED
        elif self.enabled:
            return PluginState.RUNNING
        else:
            return PluginState.DISABLED

    def get_plugin_type(self) -> PluginType:
        """Get plugin type."""
        return PluginType.CUSTOM

    def get_priority(self) -> PluginPriority:
        """Get plugin priority."""
        return PluginPriority.NORMAL

    def get_dependencies(self) -> list[str]:
        """Get plugin dependencies."""
        return self.dependencies

    def get_version(self) -> str:
        """Get plugin version."""
        return self.version

    def get_author(self) -> str:
        """Get plugin author."""
        return self.author

    def get_description(self) -> str:
        """Get plugin description."""
        return self.description

    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self.enabled

    def enable(self) -> None:
        """Enable the plugin."""
        self.enabled = True

    def disable(self) -> None:
        """Disable the plugin."""
        self.enabled = False


class APluginRegistry:
    """
    Thread-safe registry for plugin management.
    """

    def __init__(self) -> None:
        """Initialize plugin registry."""
        self._plugins: dict[str, APlugin] = {}
        self._plugin_info: dict[str, APluginInfo] = {}
        self._enabled_plugins: set[str] = set()
        self._lock = threading.RLock()

    def register(self, plugin: APlugin) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            PluginError: If plugin with same name already exists
        """
        with self._lock:
            if plugin.name in self._plugins:
                raise PluginError(f"Plugin '{plugin.name}' is already registered")

            self._plugins[plugin.name] = plugin
            self._plugin_info[plugin.name] = plugin.get_info()
            
            if plugin.enabled:
                self._enabled_plugins.add(plugin.name)

            logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")

    def unregister(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.

        Args:
            plugin_name: Name of plugin to unregister

        Returns:
            True if plugin was unregistered, False if not found
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            plugin = self._plugins[plugin_name]
            if plugin.is_initialized():
                plugin.shutdown()

            del self._plugins[plugin_name]
            del self._plugin_info[plugin_name]
            self._enabled_plugins.discard(plugin_name)

            logger.info(f"Unregistered plugin: {plugin_name}")
            return True

    def get(self, plugin_name: str) -> Optional[APlugin]:
        """
        Get plugin by name.

        Args:
            plugin_name: Name of plugin

        Returns:
            Plugin instance or None if not found
        """
        with self._lock:
            return self._plugins.get(plugin_name)

    def get_all(self) -> dict[str, APlugin]:
        """Get all registered plugins."""
        with self._lock:
            return self._plugins.copy()

    def get_enabled(self) -> dict[str, APlugin]:
        """Get all enabled plugins."""
        with self._lock:
            return {name: plugin for name, plugin in self._plugins.items() 
                    if name in self._enabled_plugins}

    def enable(self, plugin_name: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_name: Name of plugin to enable

        Returns:
            True if plugin was enabled, False if not found
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            plugin = self._plugins[plugin_name]
            plugin.enable()
            self._enabled_plugins.add(plugin_name)
            
            logger.info(f"Enabled plugin: {plugin_name}")
            return True

    def disable(self, plugin_name: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_name: Name of plugin to disable

        Returns:
            True if plugin was disabled, False if not found
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            plugin = self._plugins[plugin_name]
            if plugin.is_initialized():
                plugin.shutdown()
            
            plugin.disable()
            self._enabled_plugins.discard(plugin_name)
            
            logger.info(f"Disabled plugin: {plugin_name}")
            return True

    def list_plugins(self) -> list[APluginInfo]:
        """Get information about all registered plugins."""
        with self._lock:
            return list(self._plugin_info.values())

    def clear(self) -> None:
        """Clear all registered plugins."""
        with self._lock:
            # Shutdown all initialized plugins
            for plugin in self._plugins.values():
                if plugin.is_initialized():
                    try:
                        plugin.shutdown()
                    except Exception as e:
                        logger.error(f"Error shutting down plugin {plugin.name}: {e}")

            self._plugins.clear()
            self._plugin_info.clear()
            self._enabled_plugins.clear()
            
            logger.info("Cleared all plugins")


class APluginManager:
    """
    Plugin manager for loading, discovering and managing plugins.
    """

    def __init__(self, registry: Optional[APluginRegistry] = None) -> None:
        """
        Initialize plugin manager.

        Args:
            registry: Optional plugin registry to use
        """
        self.registry = registry or APluginRegistry()
        self._discovered_plugins: dict[str, dict[str, Any]] = {}

    def load_plugin_from_module(self, module_path: str, class_name: str, config: Optional[dict[str, Any]] = None) -> APlugin:
        """
        Load plugin from module path and class name.

        Args:
            module_path: Python module path
            class_name: Plugin class name
            config: Optional plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginError: If plugin cannot be loaded
        """
        try:
            plugin_class = ReflectionUtils.get_class_from_string(f"{module_path}.{class_name}")
            
            if not issubclass(plugin_class, APlugin):
                raise PluginError(f"Class {class_name} is not a APlugin subclass")

            plugin = plugin_class(config)
            self.registry.register(plugin)
            
            return plugin
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin {module_path}.{class_name}: {e}") from e

    def load_plugin_from_file(self, file_path: Union[str, Path], class_name: str, config: Optional[dict[str, Any]] = None) -> APlugin:
        """
        Load plugin from Python file.

        Args:
            file_path: Path to Python file
            class_name: Plugin class name
            config: Optional plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginError: If plugin cannot be loaded
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise PluginError(f"Plugin file not found: {file_path}")

        try:
            # Import module from file
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec is None or spec.loader is None:
                raise PluginError(f"Cannot create module spec for {file_path}")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get plugin class
            if not hasattr(module, class_name):
                raise PluginError(f"Class {class_name} not found in {file_path}")
                
            plugin_class = getattr(module, class_name)
            
            if not issubclass(plugin_class, APlugin):
                raise PluginError(f"Class {class_name} is not a APlugin subclass")

            plugin = plugin_class(config)
            self.registry.register(plugin)
            
            return plugin
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin from {file_path}: {e}") from e

    def discover_entry_points(self, group: str = "xwsystem.plugins") -> dict[str, dict[str, Any]]:
        """
        Discover plugins through entry points.

        Args:
            group: Entry point group name

        Returns:
            Dictionary of discovered plugins

        Raises:
            PluginError: If entry points are not available
        """
        # importlib.metadata is now required

        discovered = {}
        
        try:
            eps = entry_points(group=group)
            for ep in eps:
                discovered[ep.name] = {
                    'name': ep.name,
                    'module': ep.module,
                    'attr': ep.attr,
                    'group': group,
                    'entry_point': ep,
                }
                
            self._discovered_plugins.update(discovered)
            logger.info(f"Discovered {len(discovered)} plugins from entry points")
            
        except Exception as e:
            logger.error(f"Error discovering entry points: {e}")
            
        return discovered

    def discover_directory(self, directory: Union[str, Path], pattern: str = "*.py") -> dict[str, dict[str, Any]]:
        """
        Discover plugins in a directory.

        Args:
            directory: Directory to search
            pattern: File pattern to match

        Returns:
            Dictionary of discovered plugins
        """
        directory = Path(directory)
        discovered = {}
        
        if not directory.exists():
            logger.warning(f"Plugin directory not found: {directory}")
            return discovered

        try:
            for file_path in directory.glob(pattern):
                if file_path.is_file() and file_path.suffix == '.py':
                    # Try to find APlugin subclasses in the file
                    try:
                        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
                        if spec is None or spec.loader is None:
                            continue
                            
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Find plugin classes
                        plugin_classes = ReflectionUtils.find_classes_in_module(module, APlugin)
                        
                        for plugin_class in plugin_classes:
                            if plugin_class != APlugin:  # Skip the base class itself
                                discovered[plugin_class.__name__] = {
                                    'name': plugin_class.__name__,
                                    'file': str(file_path),
                                    'class': plugin_class,
                                    'module': module,
                                }
                                
                    except Exception as e:
                        logger.warning(f"Error scanning plugin file {file_path}: {e}")
                        
            self._discovered_plugins.update(discovered)
            logger.info(f"Discovered {len(discovered)} plugins from directory {directory}")
            
        except Exception as e:
            logger.error(f"Error discovering plugins in directory {directory}: {e}")
            
        return discovered

    def load_discovered_plugins(self, plugin_names: Optional[list[str]] = None, config: Optional[dict[str, dict[str, Any]]] = None) -> list[APlugin]:
        """
        Load discovered plugins.

        Args:
            plugin_names: Optional list of specific plugins to load
            config: Optional configuration for plugins

        Returns:
            List of loaded plugin instances
        """
        loaded = []
        config = config or {}
        
        plugins_to_load = plugin_names or list(self._discovered_plugins.keys())
        
        for plugin_name in plugins_to_load:
            if plugin_name not in self._discovered_plugins:
                logger.warning(f"Plugin {plugin_name} not discovered")
                continue
                
            plugin_info = self._discovered_plugins[plugin_name]
            plugin_config = config.get(plugin_name, {})
            
            try:
                if 'class' in plugin_info:
                    # Direct class reference
                    plugin_class = plugin_info['class']
                    plugin = plugin_class(plugin_config)
                elif 'entry_point' in plugin_info:
                    # Entry point
                    ep = plugin_info['entry_point']
                    plugin_class = ep.load()
                    plugin = plugin_class(plugin_config)
                else:
                    logger.warning(f"Cannot load plugin {plugin_name}: no class or entry point")
                    continue
                    
                self.registry.register(plugin)
                loaded.append(plugin)
                
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                
        logger.info(f"Loaded {len(loaded)} plugins")
        return loaded

    def initialize_plugins(self, plugin_names: Optional[list[str]] = None) -> None:
        """
        Initialize plugins with dependency resolution.

        Args:
            plugin_names: Optional list of specific plugins to initialize
        """
        plugins_to_init = plugin_names or list(self.registry.get_enabled().keys())
        initialized = set()
        
        def init_plugin(name: str) -> None:
            if name in initialized:
                return
                
            plugin = self.registry.get(name)
            if not plugin or not plugin.enabled:
                return
                
            # Initialize dependencies first
            for dep in plugin.dependencies:
                if dep in plugins_to_init:
                    init_plugin(dep)
                    
            # Initialize this plugin
            try:
                plugin.initialize()
                plugin._initialized = True
                initialized.add(name)
                logger.info(f"Initialized plugin: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin {name}: {e}")
                
        for plugin_name in plugins_to_init:
            init_plugin(plugin_name)

    def shutdown_plugins(self) -> None:
        """Shutdown all initialized plugins."""
        for plugin in self.registry.get_all().values():
            if plugin.is_initialized():
                try:
                    plugin.shutdown()
                    plugin._initialized = False
                    logger.info(f"Shutdown plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Error shutting down plugin {plugin.name}: {e}")

    def get_discovered_plugins(self) -> dict[str, dict[str, Any]]:
        """Get all discovered plugins."""
        return self._discovered_plugins.copy()


# Global plugin manager instance
_plugin_manager: Optional[APluginManager] = None


def get_plugin_manager() -> APluginManager:
    """Get global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = APluginManager()
    return _plugin_manager


class BasePlugin(APlugin):
    """Base plugin class for backward compatibility."""
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize base plugin."""
        super().__init__(config)
        self._name = "BasePlugin"
        self._version = "1.0.0"
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return self._version
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        self._initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._initialized = False