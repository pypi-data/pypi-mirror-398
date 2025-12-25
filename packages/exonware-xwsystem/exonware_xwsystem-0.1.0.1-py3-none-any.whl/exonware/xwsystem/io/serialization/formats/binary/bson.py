"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

BSON serialization - Binary JSON format (MongoDB).

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: BsonSerializer
"""

from importlib import import_module
from typing import Any, Optional, Union

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class BsonSerializer(ASerialization):
    """
    BSON serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: BsonSerializer
    
    Uses pymongo's bson library for MongoDB-compatible binary JSON.
    
    Examples:
        >>> serializer = BsonSerializer()
        >>> 
        >>> # Encode data
        >>> bson_bytes = serializer.encode({"key": "value"})
        >>> 
        >>> # Decode data
        >>> data = serializer.decode(bson_bytes)
        >>> 
        >>> # Save to file
        >>> serializer.save_file(document, "data.bson")
        >>> 
        >>> # Load from file
        >>> doc = serializer.load_file("data.bson")
    """
    
    def __init__(self):
        """Initialize BSON serializer."""
        super().__init__()
        self._bson = import_module("bson")
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "bson"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/bson"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".bson"]
    
    @property
    def format_name(self) -> str:
        return "BSON"
    
    @property
    def mime_type(self) -> str:
        return "application/bson"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # BSON is binary
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["bson", "BSON"]
    
    @property
    def codec_types(self) -> list[str]:
        """BSON is a binary serialization format."""
        return ["binary", "serialization"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using bson library)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to BSON bytes.
        
        Uses bson.encode().
        
        Args:
            value: Data to serialize (must be dict for BSON)
            options: BSON options
        
        Returns:
            BSON bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            if not isinstance(value, dict):
                # BSON requires dict, wrap if needed
                value = {"data": value}
            
            # Encode to BSON bytes
            bson_bytes = self._bson.encode(value)
            
            return bson_bytes
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode BSON: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode BSON bytes to data.
        
        Uses bson.decode().
        
        Args:
            repr: BSON bytes
            options: BSON options
        
        Returns:
            Decoded dict
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # BSON requires bytes
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            # Decode from BSON bytes
            data = self._bson.decode(repr)
            
            return data
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode BSON: {e}",
                format_name=self.format_name,
                original_error=e
            )

