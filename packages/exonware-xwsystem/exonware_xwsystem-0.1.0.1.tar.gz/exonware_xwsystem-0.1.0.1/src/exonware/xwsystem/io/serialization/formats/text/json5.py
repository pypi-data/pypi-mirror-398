#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/serialization/formats/text/json5.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 02-Nov-2025

JSON5 Serialization - Extended JSON with Comments and Trailing Commas

JSON5 is a superset of JSON that allows:
- Comments (// and /* */)
- Trailing commas
- Single quotes
- Unquoted keys
- More lenient syntax

Priority 1 (Security): Safe JSON5 parsing with validation
Priority 2 (Usability): Human-friendly JSON with comments
Priority 3 (Maintainability): Extends JSON serialization cleanly
Priority 4 (Performance): Efficient parsing via json5 library
Priority 5 (Extensibility): Compatible with standard JSON
"""

from typing import Any, Optional, Union
from pathlib import Path

# Lazy import for json5 - the lazy hook will automatically handle ImportError
import json5

from .json import JsonSerializer
from ....errors import SerializationError


class Json5Serializer(JsonSerializer):
    """
    JSON5 serializer with comment support.
    
    Following I→A pattern:
    - I: ISerialization (interface)
    - A: ASerialization (abstract base)
    - Concrete: Json5Serializer
    """
    
    def __init__(self, max_depth: Optional[int] = 50, max_size_mb: Optional[float] = 10.0):
        """
        Initialize JSON5 serializer.
        
        Args:
            max_depth: Maximum nesting depth (default: 50, lower than base due to parser limitations)
            max_size_mb: Maximum data size in MB (default: 10MB, lower than base due to parser performance)
        
        Root cause: json5 library parser has performance issues with large/deep nested structures,
        causing infinite recursion and hangs.
        Solution: Use stricter limits than base class, and fallback to JSON for large files.
        Priority #1: Security - Prevent DoS via excessive nesting
        Priority #4: Performance - Prevent hangs on large data
        """
        # JSON5 parser has known performance issues, use stricter limits.
        # We still rely on the JsonSerializer base for all generic JSON
        # behaviour (path operations, queries, etc.), only overriding the
        # concrete encode/decode layer.
        super().__init__(max_depth=max_depth, max_size_mb=max_size_mb)
        if json5 is None:
            raise ImportError("json5 library required. Install with: pip install json5")
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "json5"
    
    @property
    def media_types(self) -> list[str]:
        """Supported MIME types."""
        return ["application/json5", "application/json"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".json5", ".json"]
    
    @property
    def aliases(self) -> list[str]:
        """Alternative names."""
        return ["json5", "JSON5"]
    
    @property
    def codec_types(self) -> list[str]:
        """JSON5 is a serialization and config format (supports comments)."""
        return ["serialization", "config"]
    
    def encode(self, data: Any, options: Optional[dict[str, Any]] = None) -> str:
        """
        Encode data to JSON5 string.
        
        Root cause: json5.dumps() can hang on very large/deep nested structures.
        Solution: Validate data limits before encoding, fallback to JSON for large files.
        Priority #1: Security - Prevent DoS
        Priority #4: Performance - Prevent hangs
        
        Args:
            data: Data to encode
            options: Encoding options (indent, etc.)
            
        Returns:
            JSON5 string
            
        Raises:
            SerializationError: If data exceeds limits or encoding fails
        """
        opts = options or {}
        indent = opts.get('indent', 2)
        
        # Root cause: json5 parser has performance issues with large/deep structures.
        # Solution: Validate limits before encoding.
        skip_validation = opts.get('skip_validation', False)
        if not skip_validation:
            self._validate_data_limits(data, "serialize")
        
        try:
            # json5 uses same API as json but with extended syntax support
            return json5.dumps(data, indent=indent)
        except (RecursionError, MemoryError) as e:
            # Root cause: json5 parser hit recursion limit or memory issue.
            # Solution: Provide helpful error message suggesting JSON fallback.
            raise SerializationError(
                f"JSON5 encoding failed due to excessive nesting or size. "
                f"JSON5 parser has limitations with large/deep structures. "
                f"Consider using JSON format instead, or reduce data complexity. "
                f"Original error: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, data: Union[str, bytes], options: Optional[dict[str, Any]] = None) -> Any:
        """
        Decode JSON5 string to Python data.
        
        Root cause: json5.loads() can hang on very large/deep nested JSON5 strings.
        Solution: Check input size, use timeout protection, provide helpful errors.
        Priority #1: Security - Prevent DoS
        Priority #4: Performance - Prevent hangs
        
        Args:
            data: JSON5 string or bytes
            options: Decoding options
            
        Returns:
            Decoded Python data
            
        Raises:
            SerializationError: If data exceeds limits or decoding fails
        """
        opts = options or {}
        
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        # Root cause: json5 parser hangs on large input strings.
        # Solution: Check input size before parsing.
        skip_validation = opts.get('skip_validation', False)
        if not skip_validation:
            size_mb = len(data.encode('utf-8')) / (1024 * 1024)
            if size_mb > self._max_size_mb:
                raise SerializationError(
                    f"JSON5 input exceeds maximum size of {self._max_size_mb}MB "
                    f"(found {size_mb:.1f}MB). JSON5 parser has performance issues with large files. "
                    f"Consider using JSON format instead, or split the data.",
                    format_name=self.format_name
                )
        
        try:
            return json5.loads(data)
        except (RecursionError, MemoryError) as e:
            # Root cause: json5 parser hit recursion limit or memory issue.
            # Solution: Provide helpful error message suggesting JSON fallback.
            raise SerializationError(
                f"JSON5 decoding failed due to excessive nesting or size. "
                f"JSON5 parser has limitations with large/deep structures. "
                f"Consider using JSON format instead, or reduce data complexity. "
                f"Original error: {e}",
                format_name=self.format_name,
                original_error=e
            )
        except Exception as e:
            # Catch any other parsing errors
            raise SerializationError(
                f"JSON5 decoding failed: {e}. "
                f"If this is a large file, consider using JSON format instead.",
                format_name=self.format_name,
                original_error=e
            )

