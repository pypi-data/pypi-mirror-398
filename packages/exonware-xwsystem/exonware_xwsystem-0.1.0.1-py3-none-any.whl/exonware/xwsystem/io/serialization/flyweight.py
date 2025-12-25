#exonware\xwsystem\serialization\flyweight.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 05, 2025

Flyweight Pattern Implementation for Serializers

Optimizes memory usage by sharing serializer instances with identical configurations.
This prevents creating multiple instances of the same serializer type with the same
configuration, which is especially important for high-throughput applications.
"""

import threading
from typing import Any, Hashable, Optional, Union
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity
from weakref import WeakValueDictionary

from ...config.logging_setup import get_logger
from .contracts import ISerialization

logger = get_logger("xwsystem.serialization.flyweight")


class SerializerFlyweight:
    """
    Flyweight factory for serializer instances.
    
    Manages shared serializer instances to reduce memory footprint and
    improve performance by avoiding redundant object creation.
    """
    
    def __init__(self):
        """Initialize the flyweight factory."""
        self._instances: WeakValueDictionary[str, ISerialization] = WeakValueDictionary()
        self._lock = threading.RLock()
        self._stats = {
            'created': 0,
            'reused': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def get_serializer[T: ISerialization](
        self, 
        serializer_class: type[T],
        **config: Any
    ) -> T:
        """
        Get a serializer instance, creating or reusing based on configuration.
        
        Args:
            serializer_class: The serializer class to instantiate
            **config: Configuration parameters for the serializer
            
        Returns:
            Shared serializer instance
        """
        # Create a hashable key from the class and configuration
        cache_key = self._create_cache_key(serializer_class, config)
        
        with self._lock:
            # Check if we already have this instance
            if cache_key in self._instances:
                self._stats['cache_hits'] += 1
                self._stats['reused'] += 1
                # Removed expensive debug logging from hot path for performance
                return self._instances[cache_key]
            
            # Create new instance
            self._stats['cache_misses'] += 1
            self._stats['created'] += 1
            
            try:
                instance = serializer_class(**config)
                self._instances[cache_key] = instance
                # Removed expensive debug logging from hot path for performance
                return instance
                
            except Exception as e:
                # Keep error logging as it's not in hot path
                logger.error(f"Failed to create {serializer_class.__name__} instance: {e}")
                raise
    
    def _create_cache_key[T: ISerialization](self, serializer_class: type[T], config: dict[str, Any]) -> str:
        """
        Create a hashable cache key from class and configuration.
        
        Args:
            serializer_class: The serializer class
            config: Configuration dictionary
            
        Returns:
            String cache key
        """
        # Start with class name and module
        key_parts = [f"{serializer_class.__module__}.{serializer_class.__name__}"]
        
        # Add sorted configuration parameters
        # Only include hashable values to avoid issues
        for key, value in sorted(config.items()):
            if self._is_hashable(value):
                key_parts.append(f"{key}={repr(value)}")
            else:
                # For non-hashable values, use their string representation
                key_parts.append(f"{key}={str(type(value).__name__)}:{str(value)}")
        
        return "|".join(key_parts)
    
    def _is_hashable(self, obj: Any) -> bool:
        """Check if an object is hashable."""
        try:
            hash(obj)
            return True
        except TypeError:
            return False
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get flyweight usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        with self._lock:
            return {
                **self._stats,
                'active_instances': len(self._instances),
                'hit_rate': (
                    self._stats['cache_hits'] / 
                    (self._stats['cache_hits'] + self._stats['cache_misses'])
                    if (self._stats['cache_hits'] + self._stats['cache_misses']) > 0 
                    else 0.0
                ),
                'reuse_rate': (
                    self._stats['reused'] / 
                    (self._stats['created'] + self._stats['reused'])
                    if (self._stats['created'] + self._stats['reused']) > 0
                    else 0.0
                )
            }
    
    def clear_cache(self) -> None:
        """Clear the serializer cache."""
        with self._lock:
            cleared_count = len(self._instances)
            self._instances.clear()
            logger.info(f"Cleared {cleared_count} serializer instances from cache")
    
    def get_cache_info(self) -> dict[str, Any]:
        """
        Get detailed cache information.
        
        Returns:
            Dictionary with cache details
        """
        with self._lock:
            cache_info = {}
            for key, instance in self._instances.items():
                cache_info[key[:32] + "..." if len(key) > 32 else key] = {
                    'class': instance.__class__.__name__,
                    'format_name': getattr(instance, 'format_name', 'unknown'),
                    'memory_address': hex(id(instance))
                }
            return cache_info


# Global flyweight instance
_serializer_flyweight = SerializerFlyweight()


def get_serializer[T: ISerialization](serializer_class: type[T], **config: Any) -> T:
    """
    Get a serializer instance using the flyweight pattern.
    
    This is the main entry point for getting serializer instances with
    automatic memory optimization through instance sharing.
    
    Args:
        serializer_class: The serializer class to instantiate
        **config: Configuration parameters for the serializer
        
    Returns:
        Shared serializer instance
        
    Example:
        >>> from xwsystem.serialization import JsonSerializer
        >>> # These will return the same instance
        >>> json1 = get_serializer(JsonSerializer, validate_input=True)
        >>> json2 = get_serializer(JsonSerializer, validate_input=True)
        >>> assert json1 is json2  # Same instance
    """
    return _serializer_flyweight.get_serializer(serializer_class, **config)


def get_flyweight_stats() -> dict[str, Any]:
    """
    Get flyweight usage statistics.
    
    Returns:
        Dictionary with usage statistics including:
        - created: Number of new instances created
        - reused: Number of times existing instances were reused
        - cache_hits: Number of successful cache lookups
        - cache_misses: Number of failed cache lookups
        - active_instances: Current number of cached instances
        - hit_rate: Cache hit rate (0.0 to 1.0)
        - reuse_rate: Instance reuse rate (0.0 to 1.0)
    """
    return _serializer_flyweight.get_stats()


def clear_serializer_cache() -> None:
    """Clear the global serializer cache."""
    _serializer_flyweight.clear_cache()


def get_cache_info() -> dict[str, Any]:
    """Get detailed information about cached serializer instances."""
    return _serializer_flyweight.get_cache_info()


class SerializerPool:
    """
    Advanced serializer pool with size limits and eviction policies.
    
    Provides more advanced caching with configurable size limits and
    eviction strategies for high-throughput applications.
    """
    
    def __init__(self, max_size: int = 100, eviction_policy: str = "LRU"):
        """
        Initialize serializer pool.
        
        Args:
            max_size: Maximum number of cached instances
            eviction_policy: Eviction policy ("LRU", "LFU", "FIFO")
        """
        self.max_size = max_size
        self.eviction_policy = eviction_policy
        self._instances: dict[str, ISerialization] = {}
        self._access_order: dict[str, int] = {}  # For LRU
        self._access_count: dict[str, int] = {}  # For LFU
        self._insertion_order: dict[str, int] = {}  # For FIFO
        self._counter = 0
        self._lock = threading.RLock()
    
    def get_serializer[T: ISerialization](self, serializer_class: type[T], **config: Any) -> T:
        """Get serializer from pool with size-limited caching."""
        cache_key = self._create_cache_key(serializer_class, config)
        
        with self._lock:
            if cache_key in self._instances:
                # Update access tracking
                self._counter += 1
                self._access_order[cache_key] = self._counter
                self._access_count[cache_key] = self._access_count.get(cache_key, 0) + 1
                return self._instances[cache_key]
            
            # Create new instance
            instance = serializer_class(**config)
            
            # Check if we need to evict
            if len(self._instances) >= self.max_size:
                self._evict_instance()
            
            # Add new instance
            self._counter += 1
            self._instances[cache_key] = instance
            self._access_order[cache_key] = self._counter
            self._access_count[cache_key] = 1
            self._insertion_order[cache_key] = self._counter
            
            return instance
    
    def _evict_instance(self) -> None:
        """Evict an instance based on the configured policy."""
        if not self._instances:
            return
        
        if self.eviction_policy == "LRU":
            # Evict least recently used
            lru_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])
        elif self.eviction_policy == "LFU":
            # Evict least frequently used
            lru_key = min(self._access_count.keys(), key=lambda k: self._access_count[k])
        elif self.eviction_policy == "FIFO":
            # Evict first inserted
            lru_key = min(self._insertion_order.keys(), key=lambda k: self._insertion_order[k])
        else:
            # Default to LRU
            lru_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])
        
        # Remove from all tracking dictionaries
        del self._instances[lru_key]
        del self._access_order[lru_key]
        del self._access_count[lru_key]
        del self._insertion_order[lru_key]
        
        logger.debug(f"Evicted serializer instance: {lru_key[:32]}...")
    
    def _create_cache_key[T: ISerialization](self, serializer_class: type[T], config: dict[str, Any]) -> str:
        """Create cache key (same as flyweight implementation)."""
        return _serializer_flyweight._create_cache_key(serializer_class, config)
    
    def get_pool_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                'size': len(self._instances),
                'max_size': self.max_size,
                'eviction_policy': self.eviction_policy,
                'total_accesses': sum(self._access_count.values()),
                'unique_instances': len(self._instances)
            }


# Factory function for easy serializer creation with flyweight optimization
def create_serializer(format_name: str, **config: Any) -> ISerialization:
    """
    Create a serializer instance by format name using flyweight pattern.
    
    Args:
        format_name: Name of the serialization format
        **config: Configuration parameters
        
    Returns:
        Serializer instance
        
    Raises:
        ValueError: If format is not supported
    """
    # Import here to avoid circular imports
    # Core formats (always available)
    from . import (
        JsonSerializer, YamlSerializer, TomlSerializer, XmlSerializer,
        CsvSerializer, ConfigParserSerializer, PickleSerializer, MarshalSerializer,
        BsonSerializer, MsgPackSerializer, CborSerializer,
        DbmSerializer, ShelveSerializer, PlistSerializer,
        FormDataSerializer, MultipartSerializer
    )
    
    # NOTE: Enterprise formats moved to exonware-xwformats per DEV_GUIDELINES.md
    # Users should explicitly import from xwformats:
    # from exonware.xwformats import AvroSerializer, ProtobufSerializer, ...
    # Then use them directly or via registry
    
    # Core formats (17 formats)
    format_map = {
        'json': JsonSerializer,
        'yaml': YamlSerializer, 
        'toml': TomlSerializer,
        'xml': XmlSerializer,
        'csv': CsvSerializer,
        'ini': ConfigParserSerializer,
        'configparser': ConfigParserSerializer,
        'pickle': PickleSerializer,
        'marshal': MarshalSerializer,
        'bson': BsonSerializer,
        'msgpack': MsgPackSerializer,
        'cbor': CborSerializer,
        'dbm': DbmSerializer,
        'shelve': ShelveSerializer,
        'plist': PlistSerializer,
        'formdata': FormDataSerializer,
        'multipart': MultipartSerializer,
    }
    
    # Check for enterprise formats (available in xwformats)
    enterprise_formats = {
        'avro', 'protobuf', 'thrift', 'parquet', 'orc', 'capnproto', 'flatbuffers',
        'hdf5', 'feather', 'zarr', 'netcdf', 'mat',
        'lmdb', 'graphdb', 'leveldb', 'ubjson'
    }
    
    format_lower = format_name.lower()
    
    if format_lower in enterprise_formats:
        # Try to get from xwformats registry
        from ..codec.registry import get_registry
        registry = get_registry()
        serializer_class = registry.get_by_id(format_lower)
        
        if serializer_class:
            return get_serializer(serializer_class, **config)
        else:
            raise ValueError(
                f"Enterprise format '{format_name}' requires exonware-xwformats.\n"
                f"Install with: pip install exonware-xwformats\n"
                f"Or use lazy install: pip install exonware-xwsystem[lazy]\n"
                f"Then import: from exonware.xwformats import {format_name.capitalize()}Serializer"
            )
    
    serializer_class = format_map.get(format_lower)
    if not serializer_class:
        available_formats = list(format_map.keys())
        raise ValueError(
            f"Unsupported format: {format_name}. "
            f"Available core formats: {', '.join(sorted(available_formats))}\n"
            f"Enterprise formats available in exonware-xwformats: {', '.join(sorted(enterprise_formats))}"
        )
    
    return get_serializer(serializer_class, **config)
