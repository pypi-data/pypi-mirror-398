"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

MessagePack serialization - Efficient binary serialization.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: MsgPackSerializer
"""

from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError

# Lazy import for msgpack - the lazy hook will automatically handle ImportError
import msgpack


class MsgPackSerializer(ASerialization):
    """
    MessagePack serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: MsgPackSerializer
    
    Uses msgpack library for efficient binary serialization.
    
    Examples:
        >>> serializer = MsgPackSerializer()
        >>> 
        >>> # Encode data
        >>> msgpack_bytes = serializer.encode({"key": "value"})
        >>> 
        >>> # Decode data
        >>> data = serializer.decode(msgpack_bytes)
        >>> 
        >>> # Save to file
        >>> serializer.save_file(data_dict, "data.msgpack")
        >>> 
        >>> # Load from file
        >>> data = serializer.load_file("data.msgpack")
    """
    
    def __init__(self):
        """Initialize MessagePack serializer."""
        super().__init__()
        if msgpack is None:
            raise ImportError(
                "msgpack is required for MessagePack serialization. "
                "Install with: pip install msgpack"
            )
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "msgpack"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/msgpack", "application/x-msgpack"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".msgpack", ".mp"]
    
    @property
    def format_name(self) -> str:
        return "MessagePack"
    
    @property
    def mime_type(self) -> str:
        return "application/msgpack"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # MessagePack is binary
    
    @property
    def supports_streaming(self) -> bool:
        return True  # MessagePack supports streaming
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["msgpack", "MessagePack", "mp"]
    
    @property
    def codec_types(self) -> list[str]:
        """MessagePack is a binary serialization format."""
        return ["binary", "serialization"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using msgpack library)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to MessagePack bytes.
        
        Uses msgpack.packb().
        
        Args:
            value: Data to serialize
            options: MessagePack options (use_bin_type, strict_types, etc.)
        
        Returns:
            MessagePack bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Encode to MessagePack bytes
            msgpack_bytes = msgpack.packb(
                value,
                use_bin_type=opts.get('use_bin_type', True),
                strict_types=opts.get('strict_types', False),
                default=opts.get('default', None)
            )
            
            return msgpack_bytes
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode MessagePack: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode MessagePack bytes to data.
        
        Uses msgpack.unpackb().
        
        Args:
            repr: MessagePack bytes
            options: MessagePack options (raw, strict_map_key, etc.)
        
        Returns:
            Decoded Python object
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # MessagePack requires bytes
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            opts = options or {}
            
            # Decode from MessagePack bytes
            data = msgpack.unpackb(
                repr,
                raw=opts.get('raw', False),
                strict_map_key=opts.get('strict_map_key', False),
                object_hook=opts.get('object_hook', None)
            )
            
            return data
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode MessagePack: {e}",
                format_name=self.format_name,
                original_error=e
            )

