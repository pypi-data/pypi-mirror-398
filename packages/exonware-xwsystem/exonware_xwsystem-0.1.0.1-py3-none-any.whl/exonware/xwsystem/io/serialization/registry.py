"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Serialization Registry - Delegates to UniversalCodecRegistry.

Provides serialization-specific convenience methods for format discovery.
"""

from typing import Optional, Union
from pathlib import Path

from ..codec.registry import UniversalCodecRegistry, get_registry
from .contracts import ISerialization


class SerializationRegistry:
    """
    Serialization registry - delegates to UniversalCodecRegistry.
    
    Provides serialization-focused API on top of the universal codec registry.
    
    Features:
    - Format detection from file paths
    - List all serialization formats
    - Get serializer by format ID
    - Get serializer by file extension
    
    Examples:
        >>> registry = SerializationRegistry()
        >>> 
        >>> # Get serializer by ID
        >>> json_ser = registry.get_by_format("json")
        >>> 
        >>> # Auto-detect from file path
        >>> ser = registry.detect_from_file("data.yaml")
        >>> 
        >>> # List all formats
        >>> formats = registry.list_formats()
    """
    
    def __init__(self, codec_registry: Optional[UniversalCodecRegistry] = None):
        """
        Initialize serialization registry.
        
        Args:
            codec_registry: Optional UniversalCodecRegistry instance
                           (defaults to global registry)
        """
        self._codec_registry = codec_registry or get_registry()
    
    def get_by_format(self, format_id: str) -> Optional[ISerialization]:
        """
        Get serializer by format ID.
        
        Args:
            format_id: Format identifier (e.g., 'json', 'yaml')
        
        Returns:
            Serializer instance or None
        
        Examples:
            >>> json_ser = registry.get_by_format("json")
            >>> yaml_ser = registry.get_by_format("yaml")
        """
        return self._codec_registry.get_by_id(format_id)
    
    def detect_from_file(self, file_path: Union[str, Path]) -> Optional[ISerialization]:
        """
        Auto-detect serializer from file path.
        
        Uses file extension to determine the appropriate serializer.
        
        Args:
            file_path: File path to detect from
        
        Returns:
            Serializer instance or None
        
        Examples:
            >>> ser = registry.detect_from_file("config.yaml")
            >>> data = ser.load_file("config.yaml")
        """
        return self._codec_registry.detect(file_path)
    
    def get_by_extension(self, extension: str) -> Optional[ISerialization]:
        """
        Get serializer by file extension.
        
        Args:
            extension: File extension (with or without dot)
        
        Returns:
            Serializer instance or None
        
        Examples:
            >>> json_ser = registry.get_by_extension(".json")
            >>> yaml_ser = registry.get_by_extension("yaml")
        """
        return self._codec_registry.get_by_extension(extension)
    
    def get_by_mime_type(self, mime_type: str) -> Optional[ISerialization]:
        """
        Get serializer by MIME type.
        
        Args:
            mime_type: MIME type string
        
        Returns:
            Serializer instance or None
        
        Examples:
            >>> json_ser = registry.get_by_mime_type("application/json")
        """
        return self._codec_registry.get_by_mime_type(mime_type)
    
    def list_formats(self) -> list[str]:
        """
        List all registered format IDs.
        
        Returns:
            List of format identifiers
        
        Examples:
            >>> formats = registry.list_formats()
            >>> # ['json', 'yaml', 'toml', 'xml', ...]
        """
        return self._codec_registry.list_codecs()
    
    def list_extensions(self) -> list[str]:
        """
        List all registered file extensions.
        
        Returns:
            List of file extensions
        
        Examples:
            >>> extensions = registry.list_extensions()
            >>> # ['.json', '.yaml', '.yml', '.toml', ...]
        """
        return self._codec_registry.list_extensions()
    
    def list_mime_types(self) -> list[str]:
        """
        List all registered MIME types.
        
        Returns:
            List of MIME types
        
        Examples:
            >>> mime_types = registry.list_mime_types()
            >>> # ['application/json', 'application/x-yaml', ...]
        """
        return self._codec_registry.list_mime_types()
    
    def register(self, serializer_class: type) -> None:
        """
        Register a serializer class.
        
        Args:
            serializer_class: Serializer class to register
        
        Examples:
            >>> registry.register(JsonSerializer)
        """
        self._codec_registry.register(serializer_class)


# Global serialization registry instance
_global_serialization_registry: Optional[SerializationRegistry] = None


def get_serialization_registry() -> SerializationRegistry:
    """
    Get the global serialization registry.
    
    Returns:
        Global SerializationRegistry instance
    """
    global _global_serialization_registry
    if _global_serialization_registry is None:
        _global_serialization_registry = SerializationRegistry()
    return _global_serialization_registry

