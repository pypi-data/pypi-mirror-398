"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

FormData serialization - URL-encoded form data.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: FormDataSerializer
"""

from urllib.parse import urlencode, parse_qs
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class FormDataSerializer(ASerialization):
    """
    FormData serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: FormDataSerializer
    
    Uses Python's built-in urllib.parse for form data encoding.
    
    Examples:
        >>> serializer = FormDataSerializer()
        >>> 
        >>> # Encode data
        >>> form_str = serializer.encode({"username": "john", "password": "secret"})
        >>> # 'username=john&password=secret'
        >>> 
        >>> # Decode data
        >>> data = serializer.decode("username=john&password=secret")
        >>> # {'username': ['john'], 'password': ['secret']}
    """
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "formdata"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-www-form-urlencoded"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".form"]
    
    @property
    def format_name(self) -> str:
        return "FormData"
    
    @property
    def mime_type(self) -> str:
        return "application/x-www-form-urlencoded"
    
    @property
    def is_binary_format(self) -> bool:
        return False  # FormData is text-based
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["formdata", "form", "urlencoded"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using urllib.parse)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to form-data string.
        
        Uses urllib.parse.urlencode().
        
        Args:
            value: Data to serialize (dict)
            options: Encoding options (doseq, safe, etc.)
        
        Returns:
            URL-encoded string
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            if not isinstance(value, dict):
                raise TypeError("FormData requires dict")
            
            opts = options or {}
            
            # Encode to URL-encoded string
            form_str = urlencode(
                value,
                doseq=opts.get('doseq', True),
                safe=opts.get('safe', ''),
                encoding=opts.get('encoding', 'utf-8'),
                errors=opts.get('errors', 'strict')
            )
            
            return form_str
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode FormData: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode form-data string to data.
        
        Uses urllib.parse.parse_qs().
        
        Args:
            repr: URL-encoded string (bytes or str)
            options: Decoding options (keep_blank_values, etc.)
        
        Returns:
            Decoded dict
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Convert bytes to str if needed
            if isinstance(repr, bytes):
                repr = repr.decode('utf-8')
            
            opts = options or {}
            
            # Decode from URL-encoded string
            data = parse_qs(
                repr,
                keep_blank_values=opts.get('keep_blank_values', True),
                encoding=opts.get('encoding', 'utf-8'),
                errors=opts.get('errors', 'strict')
            )
            
            # Flatten single-value lists if requested
            if opts.get('flatten', True):
                data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
            
            return data
            
        except (Exception, UnicodeDecodeError) as e:
            raise SerializationError(
                f"Failed to decode FormData: {e}",
                format_name=self.format_name,
                original_error=e
            )

