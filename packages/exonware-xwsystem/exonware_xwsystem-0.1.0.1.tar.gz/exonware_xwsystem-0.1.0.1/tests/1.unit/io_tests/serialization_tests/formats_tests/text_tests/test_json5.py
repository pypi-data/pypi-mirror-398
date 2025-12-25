#!/usr/bin/env python3
#exonware/xwsystem/tests/1.unit/io_tests/serialization_tests/formats_tests/text_tests/test_json5.py
"""
Unit tests for JSON5 serializer.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: 02-Nov-2025
"""

import pytest
from exonware.xwsystem.io.serialization.formats.text.json5 import Json5Serializer


@pytest.mark.xwsystem_unit
class TestJSON5Serializer:
    """Unit tests for JSON5 serializer."""
    
    def test_serializer_initialization(self):
        """Test JSON5 serializer can be initialized."""
        serializer = Json5Serializer()
        assert serializer is not None
        assert serializer.codec_id == "json5"
        assert serializer.format_name == "JSON5"
    
    def test_encode_simple_dict(self):
        """Test encoding simple dictionary."""
        serializer = Json5Serializer()
        data = {"name": "Alice", "age": 30}
        
        result = serializer.encode(data)
        assert result is not None
        assert isinstance(result, str)
        assert "name" in result
        assert "Alice" in result
    
    def test_decode_simple_json5(self):
        """Test decoding simple JSON5 string."""
        serializer = Json5Serializer()
        json5_str = '{"name": "Alice", "age": 30}'
        
        result = serializer.decode(json5_str)
        assert result == {"name": "Alice", "age": 30}
    
    def test_decode_json5_with_comments(self):
        """Test decoding JSON5 with comments."""
        serializer = Json5Serializer()
        json5_str = '''
        {
            // User information
            "name": "Alice",
            "age": 30  // trailing comma is OK
        }
        '''
        
        result = serializer.decode(json5_str)
        assert result["name"] == "Alice"
        assert result["age"] == 30
    
    def test_decode_json5_with_trailing_commas(self):
        """Test decoding JSON5 with trailing commas."""
        serializer = Json5Serializer()
        json5_str = '{"name": "Alice", "age": 30,}'  # trailing comma
        
        result = serializer.decode(json5_str)
        assert result == {"name": "Alice", "age": 30}
    
    def test_roundtrip_encoding(self):
        """Test encoding and decoding preserves data."""
        serializer = Json5Serializer()
        original_data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        encoded = serializer.encode(original_data)
        decoded = serializer.decode(encoded)
        
        assert decoded == original_data
    
    def test_decode_bytes_input(self):
        """Test decoding from bytes input."""
        serializer = Json5Serializer()
        json5_bytes = b'{"name": "Alice", "age": 30}'
        
        result = serializer.decode(json5_bytes)
        assert result == {"name": "Alice", "age": 30}
    
    def test_encode_with_indent_option(self):
        """Test encoding with custom indent."""
        serializer = XWJson5Serializer()
        data = {"name": "Alice"}
        
        result = serializer.encode(data, options={"indent": 4})
        assert result is not None
        assert "\n" in result  # Should be formatted
    
    def test_mime_types(self):
        """Test JSON5 MIME types are correct."""
        serializer = XWJson5Serializer()
        assert "application/json5" in serializer.media_types
        assert "application/json" in serializer.media_types
    
    def test_file_extensions(self):
        """Test JSON5 file extensions are correct."""
        serializer = XWJson5Serializer()
        assert ".json5" in serializer.file_extensions
        assert ".json" in serializer.file_extensions

