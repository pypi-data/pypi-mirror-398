"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

ConfigParser serialization - INI file format.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: ConfigParserSerializer
"""

import configparser
import io
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class ConfigParserSerializer(ASerialization):
    """
    ConfigParser serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: ConfigParserSerializer
    
    Uses Python's built-in configparser module for INI files.
    
    Examples:
        >>> serializer = ConfigParserSerializer()
        >>> 
        >>> # Encode data
        >>> ini_str = serializer.encode({
        ...     "database": {"host": "localhost", "port": "5432"}
        ... })
        >>> 
        >>> # Decode data
        >>> data = serializer.decode("[database]\\nhost = localhost")
        >>> 
        >>> # Save to file
        >>> serializer.save_file(config_dict, "config.ini")
        >>> 
        >>> # Load from file
        >>> config = serializer.load_file("config.ini")
    """
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "ini"
    
    @property
    def media_types(self) -> list[str]:
        return ["text/plain", "application/x-ini"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".ini", ".cfg", ".conf"]
    
    @property
    def format_name(self) -> str:
        return "INI"
    
    @property
    def mime_type(self) -> str:
        return "text/plain"
    
    @property
    def is_binary_format(self) -> bool:
        return False  # INI is text-based
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["ini", "INI", "cfg", "conf", "configparser"]
    
    @property
    def codec_types(self) -> list[str]:
        """INI/ConfigParser is a configuration file format."""
        return ["config"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using configparser module)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to INI string.
        
        Uses configparser.ConfigParser.
        
        Args:
            value: Data to serialize (dict of dicts)
            options: ConfigParser options
        
        Returns:
            INI string
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            if not isinstance(value, dict):
                raise TypeError("ConfigParser requires dict of dicts")
            
            # Create ConfigParser
            config = configparser.ConfigParser()
            
            # Add sections and values
            for section, items in value.items():
                if isinstance(items, dict):
                    config[section] = items
                else:
                    # Handle non-dict values in DEFAULT section
                    if 'DEFAULT' not in config:
                        config['DEFAULT'] = {}
                    config['DEFAULT'][section] = str(items)
            
            # Write to string
            output = io.StringIO()
            config.write(output)
            
            return output.getvalue()
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode INI: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode INI string to data.
        
        Uses configparser.ConfigParser.
        
        Args:
            repr: INI string (bytes or str)
            options: ConfigParser options
        
        Returns:
            Decoded dict of dicts
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Convert bytes to str if needed
            if isinstance(repr, bytes):
                repr = repr.decode('utf-8')
            
            # Create ConfigParser
            config = configparser.ConfigParser()
            
            # Read from string
            config.read_string(repr)
            
            # Convert to dict
            result = {}
            for section in config.sections():
                result[section] = dict(config[section])
            
            # Include DEFAULT section if it has items
            if config.defaults():
                result['DEFAULT'] = dict(config.defaults())
            
            return result
            
        except (configparser.Error, UnicodeDecodeError) as e:
            raise SerializationError(
                f"Failed to decode INI: {e}",
                format_name=self.format_name,
                original_error=e
            )

