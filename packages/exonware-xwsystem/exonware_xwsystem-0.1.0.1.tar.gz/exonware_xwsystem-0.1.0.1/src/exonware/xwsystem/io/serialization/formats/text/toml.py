"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

TOML serialization - Configuration file format.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: TomlSerializer
"""

import sys
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError

# Python 3.11+ has tomllib built-in, earlier versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    # Lazy import for tomli - the lazy hook will automatically handle ImportError
    import tomli as tomllib

# Lazy import for tomli_w - the lazy hook will automatically handle ImportError
import tomli_w


class TomlSerializer(ASerialization):
    """
    TOML serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: TomlSerializer
    
    Uses tomllib/tomli for reading and tomli_w for writing.
    
    Examples:
        >>> serializer = TomlSerializer()
        >>> 
        >>> # Encode data
        >>> toml_str = serializer.encode({"database": {"port": 5432}})
        >>> 
        >>> # Decode data
        >>> data = serializer.decode("[database]\\nport = 5432")
        >>> 
        >>> # Save to file
        >>> serializer.save_file({"tool": {"poetry": {}}}, "pyproject.toml")
        >>> 
        >>> # Load from file
        >>> config = serializer.load_file("pyproject.toml")
    """
    
    def __init__(self):
        """Initialize TOML serializer."""
        super().__init__()
        if tomllib is None:
            raise ImportError(
                "tomli is required for TOML deserialization. "
                "Install with: pip install tomli (Python <3.11)"
            )
        if tomli_w is None:
            raise ImportError(
                "tomli-w is required for TOML serialization. "
                "Install with: pip install tomli-w"
            )
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "toml"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/toml", "text/toml"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".toml", ".tml"]
    
    @property
    def format_name(self) -> str:
        return "TOML"
    
    @property
    def mime_type(self) -> str:
        return "application/toml"
    
    @property
    def is_binary_format(self) -> bool:
        return False  # TOML is text-based
    
    @property
    def supports_streaming(self) -> bool:
        return False  # TOML doesn't support streaming
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["toml", "TOML"]
    
    @property
    def codec_types(self) -> list[str]:
        """TOML is both a configuration and serialization format."""
        return ["config", "serialization"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using tomllib/tomli + tomli_w)
    # ========================================================================
    
    def _remove_none_values(self, data: Any) -> Any:
        """
        Recursively remove None values from data structure.
        
        Root cause fixed: TOML doesn't support None/null values natively.
        Solution: Recursively remove None values before encoding (omit them).
        Priority #2: Usability - Ensure all data structures can be serialized to TOML.
        
        Args:
            data: Data structure (dict, list, or primitive)
            
        Returns:
            Data structure with None values removed
        """
        if isinstance(data, dict):
            # Remove None values and recursively process remaining values
            result = {}
            for key, value in data.items():
                if value is not None:
                    cleaned_value = self._remove_none_values(value)
                    # Only add if cleaned value is not None (handles nested None removal)
                    if cleaned_value is not None:
                        result[key] = cleaned_value
            return result
        elif isinstance(data, list):
            # Process list items and filter out None values
            result = []
            for item in data:
                cleaned_item = self._remove_none_values(item)
                if cleaned_item is not None:
                    result.append(cleaned_item)
            return result
        else:
            # Primitive values - return as-is (None will be filtered out by caller)
            return data
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to TOML string.
        
        Uses tomli_w.dumps().
        
        Root cause fixed: TOML doesn't support None/null values.
        Solution: Remove None values before encoding using _remove_none_values().
        Priority #2: Usability - Ensure all data structures can be serialized to TOML.
        
        Args:
            value: Data to serialize (must be dict)
            options: TOML options (multiline_strings, etc.)
        
        Returns:
            TOML string
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            if not isinstance(value, dict):
                # TOML requires a table (dict) at the top level. For data-oriented
                # use cases (e.g. record lists), transparently wrap common patterns
                # so that higher-level APIs (record paging, etc.) can still work
                # uniformly across formats.
                if isinstance(value, list):
                    # Auto-wrap top-level list into "items" table.
                    value = {"items": value}
                else:
                    # Fallback: wrap primitive/other types into a single "value" key.
                    value = {"value": value}

            opts = options or {}
            
            # Root cause fixed: Remove None values before encoding (TOML doesn't support None).
            # Solution: Recursively remove None values to ensure TOML compatibility.
            # Priority #2: Usability - All data structures should be serializable.
            cleaned_value = self._remove_none_values(value)
            
            # Encode to TOML string
            toml_str = tomli_w.dumps(
                cleaned_value,
                multiline_strings=opts.get('multiline_strings', False)
            )
            
            return toml_str
            
        except (TypeError, ValueError) as e:
            raise SerializationError(
                f"Failed to encode TOML: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode TOML string to data.
        
        Uses tomllib.loads() (Python 3.11+) or tomli.loads().
        
        Args:
            repr: TOML string (bytes or str)
            options: TOML options
        
        Returns:
            Decoded dictionary
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Convert bytes to str if needed
            if isinstance(repr, bytes):
                repr = repr.decode('utf-8')
            
            # Decode from TOML string
            data = tomllib.loads(repr)

            # If this looks like an auto-wrapped list payload (see encode),
            # unwrap it for callers so that higher-level APIs (including the
            # generic record-level operations in ASerialization) see the
            # natural Python structure (a list of records).
            if isinstance(data, dict) and set(data.keys()) == {"items"} and isinstance(data["items"], list):
                return data["items"]
            
            return data
            
        except (tomllib.TOMLDecodeError if hasattr(tomllib, 'TOMLDecodeError') else Exception, UnicodeDecodeError) as e:
            raise SerializationError(
                f"Failed to decode TOML: {e}",
                format_name=self.format_name,
                original_error=e
            )

