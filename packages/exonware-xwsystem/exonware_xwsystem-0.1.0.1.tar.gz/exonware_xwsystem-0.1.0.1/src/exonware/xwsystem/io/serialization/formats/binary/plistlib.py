"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Plist serialization - Apple property list format.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: PlistSerializer
"""

import plistlib
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class PlistSerializer(ASerialization):
    """
    Plist serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: PlistSerializer
    
    Uses Python's built-in plistlib module for Apple plist files.
    
    Examples:
        >>> serializer = PlistSerializer()
        >>> 
        >>> # Encode data
        >>> plist_bytes = serializer.encode({"key": "value"})
        >>> 
        >>> # Decode data
        >>> data = serializer.decode(plist_bytes)
        >>> 
        >>> # Save to file
        >>> serializer.save_file(config, "config.plist")
        >>> 
        >>> # Load from file
        >>> config = serializer.load_file("config.plist")
    """
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "plist"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-plist", "application/plist"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".plist"]
    
    @property
    def format_name(self) -> str:
        return "Plist"
    
    @property
    def mime_type(self) -> str:
        return "application/x-plist"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # Plist can be binary or XML
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["plist", "Plist", "plistlib"]
    
    @property
    def codec_types(self) -> list[str]:
        """Plist is a config/serialization format (can be XML or binary)."""
        return ["config", "serialization"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using plistlib module)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to Plist bytes.
        
        Uses plistlib.dumps().
        
        Args:
            value: Data to serialize
            options: Plist options (fmt, sort_keys, etc.)
        
        Returns:
            Plist bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Get format (binary or XML)
            fmt = opts.get('fmt', plistlib.FMT_BINARY)
            if isinstance(fmt, str):
                fmt = plistlib.FMT_BINARY if fmt.lower() == 'binary' else plistlib.FMT_XML
            
            # Encode to Plist bytes
            plist_bytes = plistlib.dumps(
                value,
                fmt=fmt,
                sort_keys=opts.get('sort_keys', True),
                skipkeys=opts.get('skipkeys', False)
            )
            
            return plist_bytes
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode Plist: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode Plist bytes to data.
        
        Uses plistlib.loads().
        
        Args:
            repr: Plist bytes
            options: Plist options
        
        Returns:
            Decoded Python object
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Plist requires bytes
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            # Decode from Plist bytes
            data = plistlib.loads(repr)
            
            return data
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode Plist: {e}",
                format_name=self.format_name,
                original_error=e
            )

