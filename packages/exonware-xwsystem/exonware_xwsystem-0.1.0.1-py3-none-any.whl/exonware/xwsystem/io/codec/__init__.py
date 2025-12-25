#!/usr/bin/env python3
# exonware/xwsystem/io/codec/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 30, 2025

Universal Codec Abstraction for eXonware.

Provides unified interface for all encoding/decoding operations
across serialization (bytes) and syntax (strings).

Core Principle:
    ICodec[T, R] - Universal bidirectional transformation
        - Serializer = ICodec[T, bytes] for persistence/wire
        - Formatter = ICodec[T, str] for language/syntax

Public API:
    Core Abstractions:
        - ICodec[T, R]          Universal encoder/decoder
        - Serializer[T]         Type alias for ICodec[T, bytes]
        - Formatter[T]          Type alias for ICodec[T, str]
    
    Metadata:
        - ICodecMetadata        Self-describing codec protocol
        - CodecCapability       Capability flags
    
    Registry:
        - MediaKey              Media type wrapper (RFC 2046)
        - CodecRegistry         Codec lookup by media-type/extension/id
        - get_codec()           Get codec by media type
        - get_codec_for_file()  Get codec by file extension
        - get_codec_by_id()     Get codec by ID
    
    Adapters:
        - FormatterToSerializer str → bytes via UTF-8
        - SerializerToFormatter bytes → str via UTF-8
    
    Base Classes:
        - ACodec[T, R]       Base implementation with all convenience methods
    
    Errors:
        - CodecError            Base codec error
        - EncodeError           Encoding failure
        - DecodeError           Decoding failure
        - CodecNotFoundError    Registry lookup failure

Examples:
    >>> # Get codec by media type
    >>> codec = get_codec(MediaKey("application/json"))
    >>> data = codec.encode({"key": "value"})
    >>> 
    >>> # Auto-detect from file
    >>> codec = get_codec_for_file("data.json")
    >>> result = codec.decode(data)
    >>> 
    >>> # Use adapters
    >>> formatter = SqlFormatter()  # Returns str
    >>> serializer = FormatterToSerializer(formatter)  # Now returns bytes
"""

from ..defs import CodecCapability
from ..errors import CodecError, EncodeError, DecodeError, CodecNotFoundError
from ..contracts import (
    ICodec,
    Serializer,
    Formatter,
    EncodeOptions,
    DecodeOptions,
    ICodecMetadata,
)
from .base import (
    ACodec,
    MediaKey,
    CodecRegistry,
    get_global_registry,
    FormatterToSerializer,
    SerializerToFormatter,
)

# Convenience functions using global registry
def get_codec(key: MediaKey):
    """
    Get codec by media type.
    
    Args:
        key: Media type key (e.g., MediaKey("application/json"))
    
    Returns:
        Codec instance or None if not found
    
    Example:
        >>> codec = get_codec(MediaKey("application/json"))
        >>> codec.encode({"key": "value"})
    """
    return get_global_registry().get(key)


def get_codec_for_file(path: str):
    """
    Get codec by file extension.
    
    Args:
        path: File path (extension used for detection)
    
    Returns:
        Codec instance or None if not found
    
    Example:
        >>> codec = get_codec_for_file("data.json")
        >>> codec = get_codec_for_file("query.sql")
    """
    return get_global_registry().get_by_extension(path)


def get_codec_by_id(codec_id: str):
    """
    Get codec by ID or alias.
    
    Args:
        codec_id: Codec identifier (e.g., "json", "sql")
    
    Returns:
        Codec instance or None if not found
    
    Example:
        >>> codec = get_codec_by_id("json")
        >>> codec = get_codec_by_id("SQL")  # Case insensitive
    """
    return get_global_registry().get_by_id(codec_id)


def register_codec(codec_class):
    """
    Register a codec with the global registry.
    
    Args:
        codec_class: Codec class implementing ICodecMetadata
    
    Example:
        >>> @register_codec
        ... class MyCodec(ACodec[dict, bytes]):
        ...     codec_id = "myformat"
        ...     media_types = ["application/x-myformat"]
    """
    get_global_registry().register(codec_class)
    return codec_class


def list_codecs() -> list[str]:
    """
    List all registered codec IDs.
    
    Returns:
        List of codec identifiers
    """
    return get_global_registry().list_codec_ids()


__all__ = [
    # Core abstractions
    'ICodec',
    'Serializer',
    'Formatter',
    'EncodeOptions',
    'DecodeOptions',
    'ICodecMetadata',
    
    # Capabilities
    'CodecCapability',
    
    # Registry
    'MediaKey',
    'CodecRegistry',
    'get_codec',
    'get_codec_for_file',
    'get_codec_by_id',
    'register_codec',
    'list_codecs',
    
    # Base classes
    'ACodec',
    
    # Adapters
    'FormatterToSerializer',
    'SerializerToFormatter',
    
    # Errors
    'CodecError',
    'EncodeError',
    'DecodeError',
    'CodecNotFoundError',
]

