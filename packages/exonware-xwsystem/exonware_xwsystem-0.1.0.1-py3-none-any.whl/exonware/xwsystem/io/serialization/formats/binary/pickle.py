"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Pickle serialization - Python object serialization.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: PickleSerializer
"""

import pickle
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class PickleSerializer(ASerialization):
    """
    Pickle serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: PickleSerializer
    
    Uses Python's built-in pickle module.
    
    ⚠️ SECURITY WARNING: Pickle can execute arbitrary code. Only unpickle
    data from trusted sources!
    
    Examples:
        >>> serializer = PickleSerializer()
        >>> 
        >>> # Encode data
        >>> pickle_bytes = serializer.encode({"key": "value"})
        >>> 
        >>> # Decode data
        >>> data = serializer.decode(pickle_bytes)
        >>> 
        >>> # Save to file
        >>> serializer.save_file(my_object, "data.pkl")
        >>> 
        >>> # Load from file
        >>> obj = serializer.load_file("data.pkl")
    """
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "pickle"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/python-pickle", "application/x-pickle"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".pkl", ".pickle"]
    
    @property
    def format_name(self) -> str:
        return "Pickle"
    
    @property
    def mime_type(self) -> str:
        return "application/python-pickle"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # Pickle is binary
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["pickle", "pkl"]
    
    @property
    def codec_types(self) -> list[str]:
        """Pickle is a binary serialization format."""
        return ["binary", "serialization"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using pickle module)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to Pickle bytes.
        
        Uses pickle.dumps().
        
        Args:
            value: Data to serialize
            options: Pickle options (protocol, fix_imports, etc.)
        
        Returns:
            Pickle bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Encode to Pickle bytes
            pickle_bytes = pickle.dumps(
                value,
                protocol=opts.get('protocol', pickle.HIGHEST_PROTOCOL),
                fix_imports=opts.get('fix_imports', True)
            )
            
            return pickle_bytes
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode Pickle: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode Pickle bytes to data.
        
        Uses pickle.loads().
        
        ⚠️ SECURITY WARNING: Only unpickle data from trusted sources!
        
        Args:
            repr: Pickle bytes
            options: Pickle options (fix_imports, encoding, errors, etc.)
        
        Returns:
            Decoded Python object
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Pickle requires bytes
            if isinstance(repr, str):
                repr = repr.encode('latin1')
            
            opts = options or {}
            
            # Decode from Pickle bytes
            data = pickle.loads(
                repr,
                fix_imports=opts.get('fix_imports', True),
                encoding=opts.get('encoding', 'ASCII'),
                errors=opts.get('errors', 'strict')
            )
            
            return data
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode Pickle: {e}",
                format_name=self.format_name,
                original_error=e
            )

