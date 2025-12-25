"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Multipart serialization - Multipart form data format.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: MultipartSerializer
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.parser import BytesParser
from email.policy import default
import io
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class MultipartSerializer(ASerialization):
    """
    Multipart serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: MultipartSerializer
    
    Uses Python's built-in email.mime modules for multipart handling.
    
    Examples:
        >>> serializer = MultipartSerializer()
        >>> 
        >>> # Encode data with files
        >>> data = {
        ...     "field1": "value1",
        ...     "file1": {"filename": "test.txt", "content": b"file content"}
        ... }
        >>> multipart_bytes = serializer.encode(data)
        >>> 
        >>> # Decode multipart data
        >>> decoded = serializer.decode(multipart_bytes)
    """
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "multipart"
    
    @property
    def media_types(self) -> list[str]:
        return ["multipart/form-data", "multipart/mixed"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".multipart"]
    
    @property
    def format_name(self) -> str:
        return "Multipart"
    
    @property
    def mime_type(self) -> str:
        return "multipart/form-data"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # Multipart is binary (contains boundaries)
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["multipart", "multipart-form"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using email.mime modules)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to multipart format.
        
        Uses email.mime modules.
        
        Args:
            value: Data to serialize (dict of fields and files)
            options: Multipart options (boundary, etc.)
        
        Returns:
            Multipart bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            if not isinstance(value, dict):
                raise TypeError("Multipart requires dict")
            
            opts = options or {}
            
            # Create multipart message
            msg = MIMEMultipart('form-data', boundary=opts.get('boundary', None))
            
            # Add fields
            for key, val in value.items():
                if isinstance(val, dict) and 'filename' in val:
                    # File field
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(val.get('content', b''))
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'form-data; name="{key}"; filename="{val["filename"]}"'
                    )
                    msg.attach(part)
                else:
                    # Text field
                    part = MIMEText(str(val), 'plain')
                    part.add_header('Content-Disposition', f'form-data; name="{key}"')
                    msg.attach(part)
            
            # Convert to bytes
            return msg.as_bytes()
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode Multipart: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode multipart data.
        
        Uses email.parser.BytesParser.
        
        Args:
            repr: Multipart bytes
            options: Decoding options
        
        Returns:
            Decoded dict of fields
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Convert str to bytes if needed
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            # Parse multipart message
            parser = BytesParser(policy=default)
            msg = parser.parsebytes(repr)
            
            # Extract fields
            result = {}
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                
                # Get field name from Content-Disposition
                disposition = part.get('Content-Disposition', '')
                if 'name=' in disposition:
                    # Extract field name
                    name = disposition.split('name="')[1].split('"')[0]
                    
                    # Get content
                    content = part.get_payload(decode=True)
                    
                    # Check if it's a file
                    if 'filename=' in disposition:
                        filename = disposition.split('filename="')[1].split('"')[0]
                        result[name] = {
                            'filename': filename,
                            'content': content
                        }
                    else:
                        # Text field
                        result[name] = content.decode('utf-8') if isinstance(content, bytes) else content
            
            return result
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode Multipart: {e}",
                format_name=self.format_name,
                original_error=e
            )

