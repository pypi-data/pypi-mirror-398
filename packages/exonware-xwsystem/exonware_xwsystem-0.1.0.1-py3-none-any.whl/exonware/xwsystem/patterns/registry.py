#!/usr/bin/env python3
#exonware/xwsystem/patterns/registry.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 26, 2025

Generic registry pattern for dynamic registration and discovery.
"""

import threading
import time
from typing import Any, Optional, Callable
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity
from abc import ABC, abstractmethod
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.patterns.registry")


class RegistryError(Exception):
    """Registry-specific error."""
    pass


class IRegistry[T](ABC):
    """
    Interface for registry implementations.
    
    Root cause: Adding generic type parameter for better type safety.
    Priority #3: Maintainability - Generic types improve code clarity and type checking.
    """
    
    @abstractmethod
    def register(self, name: str, item: T, metadata: Optional[dict[str, Any]] = None) -> bool:
        """Register an item with optional metadata."""
        pass
    
    @abstractmethod
    def unregister(self, name: str) -> bool:
        """Unregister an item."""
        pass
    
    @abstractmethod
    def get(self, name: str) -> Optional[T]:
        """Get an item by name."""
        pass
    
    @abstractmethod
    def list_names(self) -> list[str]:
        """List all registered names."""
        pass
    
    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if an item exists."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all registrations."""
        pass


class GenericRegistry[T](IRegistry[T]):
    """
    Generic registry for dynamic registration and discovery.
    
    Features:
    - Thread-safe registration/lookup
    - Support for factories
    - Automatic discovery hooks
    - Metadata storage per registered item
    - Type validation
    - Callback support for registration events
    """
    
    def __init__(
        self,
        name: str = "generic",
        item_type: Optional[type] = None,
        allow_overwrite: bool = False,
        auto_discovery: bool = False
    ):
        """
        Initialize generic registry.
        
        Args:
            name: Registry name for identification
            item_type: Expected type for registered items
            allow_overwrite: Whether to allow overwriting existing items
            auto_discovery: Enable automatic discovery of items
        """
        self.name = name
        self.item_type = item_type
        self.allow_overwrite = allow_overwrite
        self.auto_discovery = auto_discovery
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Storage
        self._items: dict[str, T] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._factories: dict[str, Callable[[], T]] = {}
        
        # Callbacks
        self._registration_callbacks: list[Callable[[str, T, dict[str, Any]], None]] = []
        self._unregistration_callbacks: list[Callable[[str, T], None]] = []
        
        # Statistics
        self._stats = {
            'registrations': 0,
            'unregistrations': 0,
            'lookups': 0,
            'hits': 0,
            'misses': 0,
        }
        
        logger.debug(f"Initialized registry '{name}'")
    
    def register(
        self,
        name: str,
        item: T,
        metadata: Optional[dict[str, Any]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> bool:
        """
        Register an item with optional metadata and factory.
        
        Args:
            name: Unique name for the item
            item: Item to register (can be None if factory is provided)
            metadata: Optional metadata for the item
            factory: Optional factory function for lazy creation
            
        Returns:
            True if registration successful
            
        Raises:
            RegistryError: If registration fails
        """
        with self._lock:
            try:
                # Validate name
                if not name or not isinstance(name, str):
                    raise RegistryError("Name must be a non-empty string")
                
                # Check if already exists
                if name in self._items and not self.allow_overwrite:
                    raise RegistryError(f"Item '{name}' already registered")
                
                # Type validation
                if self.item_type and item is not None:
                    if not isinstance(item, self.item_type):
                        raise RegistryError(f"Item must be of type {self.item_type.__name__}")
                
                # Register item
                self._items[name] = item
                
                # Store metadata
                if metadata is None:
                    metadata = {}
                
                metadata.update({
                    'registered_at': time.time(),
                    'has_factory': factory is not None,
                })
                
                self._metadata[name] = metadata
                
                # Store factory if provided
                if factory:
                    self._factories[name] = factory
                
                # Update statistics
                self._stats['registrations'] += 1
                
                # Call registration callbacks
                for callback in self._registration_callbacks:
                    try:
                        callback(name, item, metadata)
                    except Exception as e:
                        logger.warning(f"Registration callback failed: {e}")
                
                logger.debug(f"Registered item '{name}' in registry '{self.name}'")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register item '{name}': {e}")
                raise RegistryError(f"Registration failed: {e}")
    
    def unregister(self, name: str) -> bool:
        """
        Unregister an item.
        
        Args:
            name: Name of item to unregister
            
        Returns:
            True if unregistration successful
        """
        with self._lock:
            try:
                if name not in self._items:
                    return False
                
                item = self._items[name]
                
                # Remove from storage
                del self._items[name]
                if name in self._metadata:
                    del self._metadata[name]
                if name in self._factories:
                    del self._factories[name]
                
                # Update statistics
                self._stats['unregistrations'] += 1
                
                # Call unregistration callbacks
                for callback in self._unregistration_callbacks:
                    try:
                        callback(name, item)
                    except Exception as e:
                        logger.warning(f"Unregistration callback failed: {e}")
                
                logger.debug(f"Unregistered item '{name}' from registry '{self.name}'")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unregister item '{name}': {e}")
                return False
    
    def get(self, name: str) -> Optional[T]:
        """
        Get an item by name.
        
        Args:
            name: Name of item to retrieve
            
        Returns:
            Registered item or None if not found
        """
        with self._lock:
            try:
                self._stats['lookups'] += 1
                
                # Check if item exists
                if name not in self._items:
                    self._stats['misses'] += 1
                    return None
                
                # Check if we have a factory for lazy creation
                if name in self._factories and self._items[name] is None:
                    try:
                        self._items[name] = self._factories[name]()
                        logger.debug(f"Created item '{name}' using factory")
                    except Exception as e:
                        logger.error(f"Factory failed for item '{name}': {e}")
                        return None
                
                self._stats['hits'] += 1
                return self._items[name]
                
            except Exception as e:
                logger.error(f"Failed to get item '{name}': {e}")
                self._stats['misses'] += 1
                return None
    
    def list_names(self) -> list[str]:
        """List all registered names."""
        with self._lock:
            return list(self._items.keys())
    
    def exists(self, name: str) -> bool:
        """Check if an item exists."""
        with self._lock:
            return name in self._items
    
    def clear(self) -> bool:
        """Clear all registrations."""
        with self._lock:
            try:
                # Call unregistration callbacks for all items
                for name, item in self._items.items():
                    for callback in self._unregistration_callbacks:
                        try:
                            callback(name, item)
                        except Exception as e:
                            logger.warning(f"Unregistration callback failed: {e}")
                
                # Clear storage
                self._items.clear()
                self._metadata.clear()
                self._factories.clear()
                
                logger.debug(f"Cleared registry '{self.name}'")
                return True
                
            except Exception as e:
                logger.error(f"Failed to clear registry '{self.name}': {e}")
                return False
    
    def get_metadata(self, name: str) -> Optional[dict[str, Any]]:
        """Get metadata for an item."""
        with self._lock:
            return self._metadata.get(name)
    
    def update_metadata(self, name: str, metadata: dict[str, Any]) -> bool:
        """Update metadata for an item."""
        with self._lock:
            if name not in self._items:
                return False
            
            if name not in self._metadata:
                self._metadata[name] = {}
            
            self._metadata[name].update(metadata)
            return True
    
    def add_registration_callback(self, callback: Callable[[str, T, dict[str, Any]], None]):
        """Add callback for registration events."""
        with self._lock:
            self._registration_callbacks.append(callback)
    
    def add_unregistration_callback(self, callback: Callable[[str, T], None]):
        """Add callback for unregistration events."""
        with self._lock:
            self._unregistration_callbacks.append(callback)
    
    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        with self._lock:
            total_lookups = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / max(1, total_lookups)
            
            return {
                'name': self.name,
                'item_type': self.item_type.__name__ if self.item_type else None,
                'size': len(self._items),
                'registrations': self._stats['registrations'],
                'unregistrations': self._stats['unregistrations'],
                'lookups': self._stats['lookups'],
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': hit_rate,
                'allow_overwrite': self.allow_overwrite,
                'auto_discovery': self.auto_discovery,
            }
    
    def discover_items(self, discovery_func: Callable[[], list[tuple[str, T, dict[str, Any]]]]) -> int:
        """
        Discover and register items using a discovery function.
        
        Args:
            discovery_func: Function that returns list of (name, item, metadata) tuples
            
        Returns:
            Number of items discovered and registered
        """
        with self._lock:
            try:
                discovered_items = discovery_func()
                registered_count = 0
                
                for name, item, metadata in discovered_items:
                    if self.register(name, item, metadata):
                        registered_count += 1
                
                logger.info(f"Discovered and registered {registered_count} items in registry '{self.name}'")
                return registered_count
                
            except Exception as e:
                logger.error(f"Discovery failed for registry '{self.name}': {e}")
                return 0


# Global registry manager
_registries: dict[str, GenericRegistry[Any]] = {}
_registry_lock = threading.RLock()


def get_registry(name: str, **kwargs) -> GenericRegistry[Any]:
    """
    Get or create a registry by name.
    
    Root cause: Global registry storage uses GenericRegistry[Any] for flexibility.
    Users can create typed registries directly: GenericRegistry[MyType]().
    Priority #3: Maintainability - Clear API design.
    
    Args:
        name: Registry name
        **kwargs: Additional arguments for registry creation
        
    Returns:
        Registry instance (untyped for global registry flexibility)
        
    Note:
        For type-safe registries, create directly: GenericRegistry[MyType]()
    """
    with _registry_lock:
        if name not in _registries:
            _registries[name] = GenericRegistry[Any](name=name, **kwargs)
        return _registries[name]


def list_registries() -> list[str]:
    """List all registry names."""
    with _registry_lock:
        return list(_registries.keys())


def clear_registry(name: str) -> bool:
    """Clear a specific registry."""
    with _registry_lock:
        if name in _registries:
            return _registries[name].clear()
        return False


def clear_all_registries() -> bool:
    """Clear all registries."""
    with _registry_lock:
        try:
            for registry in _registries.values():
                registry.clear()
            _registries.clear()
            return True
        except Exception as e:
            logger.error(f"Failed to clear all registries: {e}")
            return False


__all__ = [
    "RegistryError",
    "IRegistry",
    "GenericRegistry",
    "get_registry",
    "list_registries",
    "clear_registry",
    "clear_all_registries",
]
