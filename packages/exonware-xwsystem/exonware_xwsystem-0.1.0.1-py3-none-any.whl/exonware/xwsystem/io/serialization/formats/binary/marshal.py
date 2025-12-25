"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Marshal serialization - Python internal serialization.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: MarshalSerializer
"""

import marshal
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class MarshalSerializer(ASerialization):
    """
    Marshal serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: MarshalSerializer
    
    Uses Python's built-in marshal module.
    
    ⚠️ WARNING: Marshal is for internal Python use. Not suitable for persistent
    storage across Python versions!
    
    Examples:
        >>> serializer = MarshalSerializer()
        >>> 
        >>> # Encode data
        >>> marshal_bytes = serializer.encode([1, 2, 3, "hello"])
        >>> 
        >>> # Decode data
        >>> data = serializer.decode(marshal_bytes)
    """
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "marshal"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-python-marshal"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".marshal", ".pyc"]
    
    @property
    def format_name(self) -> str:
        return "Marshal"
    
    @property
    def mime_type(self) -> str:
        return "application/x-python-marshal"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # Marshal is binary
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["marshal", "Marshal"]
    
    @property
    def codec_types(self) -> list[str]:
        """Marshal is a binary serialization format."""
        return ["binary", "serialization"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using marshal module)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to Marshal bytes.
        
        Uses marshal.dumps().
        
        Args:
            value: Data to serialize
            options: Marshal options (version)
        
        Returns:
            Marshal bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Encode to Marshal bytes
            version = opts.get('version', marshal.version)
            marshal_bytes = marshal.dumps(value, version)
            
            return marshal_bytes
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode Marshal: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode Marshal bytes to data.
        
        Uses marshal.loads().
        
        Args:
            repr: Marshal bytes
            options: Marshal options
        
        Returns:
            Decoded Python object
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Marshal requires bytes
            if isinstance(repr, str):
                repr = repr.encode('latin1')
            
            # Decode from Marshal bytes
            data = marshal.loads(repr)
            
            return data
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode Marshal: {e}",
                format_name=self.format_name,
                original_error=e
            )

