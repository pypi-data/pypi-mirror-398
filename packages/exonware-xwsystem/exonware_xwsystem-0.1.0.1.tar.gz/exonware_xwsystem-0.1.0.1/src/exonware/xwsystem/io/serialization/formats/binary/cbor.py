"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

CBOR serialization - Concise Binary Object Representation.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: CborSerializer
"""

from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError

# Lazy import for cbor2 - the lazy hook will automatically handle ImportError
import cbor2


class CborSerializer(ASerialization):
    """
    CBOR serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: CborSerializer
    
    Uses cbor2 library for CBOR serialization.
    
    Examples:
        >>> serializer = CborSerializer()
        >>> 
        >>> # Encode data
        >>> cbor_bytes = serializer.encode({"key": "value"})
        >>> 
        >>> # Decode data
        >>> data = serializer.decode(cbor_bytes)
    """
    
    def __init__(self):
        """Initialize CBOR serializer."""
        super().__init__()
        if cbor2 is None:
            raise ImportError(
                "cbor2 is required for CBOR serialization. "
                "Install with: pip install cbor2"
            )
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "cbor"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/cbor"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".cbor"]
    
    @property
    def format_name(self) -> str:
        return "CBOR"
    
    @property
    def mime_type(self) -> str:
        return "application/cbor"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # CBOR is binary
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["cbor", "CBOR"]
    
    @property
    def codec_types(self) -> list[str]:
        """CBOR is a binary serialization format."""
        return ["binary", "serialization"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using cbor2 library)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to CBOR bytes.
        
        Uses cbor2.dumps().
        
        Args:
            value: Data to serialize
            options: CBOR options
        
        Returns:
            CBOR bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Encode to CBOR bytes
            cbor_bytes = cbor2.dumps(
                value,
                default=opts.get('default', None),
                timezone=opts.get('timezone', None)
            )
            
            return cbor_bytes
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode CBOR: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode CBOR bytes to data.
        
        Uses cbor2.loads().
        
        Args:
            repr: CBOR bytes
            options: CBOR options
        
        Returns:
            Decoded Python object
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # CBOR requires bytes
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            # Decode from CBOR bytes
            data = cbor2.loads(repr)
            
            return data
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode CBOR: {e}",
                format_name=self.format_name,
                original_error=e
            )

