#!/usr/bin/env python3
#exonware/xwsystem/tests/1.unit/io_tests/serialization_tests/formats_tests/text_tests/test_jsonlines.py
"""
Unit tests for JSONL/NDJSON serializer.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: 02-Nov-2025
"""

import pytest
from exonware.xwsystem.io.serialization.formats.text.jsonlines import JsonLinesSerializer


@pytest.mark.xwsystem_unit
class TestJSONLinesSerializer:
    """Unit tests for JSONL/NDJSON serializer."""
    
    def test_serializer_initialization(self):
        """Test JSONL serializer can be initialized."""
        serializer = JsonLinesSerializer()
        assert serializer is not None
        assert serializer.codec_id == "jsonl"
        assert "JSON" in serializer.format_name
    
    def test_encode_list_of_objects(self):
        """Test encoding list of objects."""
        serializer = JsonLinesSerializer()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        
        result = serializer.encode(data)
        assert result is not None
        assert isinstance(result, str)
        lines = result.strip().split('\n')
        assert len(lines) == 2
        assert "Alice" in lines[0]
        assert "Bob" in lines[1]
    
    def test_encode_single_object(self):
        """Test encoding single object wraps in list."""
        serializer = JsonLinesSerializer()
        data = {"name": "Alice", "age": 30}
        
        result = serializer.encode(data)
        lines = result.strip().split('\n')
        assert len(lines) == 1
        assert "Alice" in result
    
    def test_decode_jsonlines_string(self):
        """Test decoding JSONL string."""
        serializer = JsonLinesSerializer()
        jsonl_str = '{"name": "Alice", "age": 30}\n{"name": "Bob", "age": 25}'
        
        result = serializer.decode(jsonl_str)
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": 30}
        assert result[1] == {"name": "Bob", "age": 25}
    
    def test_decode_bytes_input(self):
        """Test decoding from bytes input."""
        serializer = JsonLinesSerializer()
        jsonl_bytes = b'{"name": "Alice"}\n{"name": "Bob"}'
        
        result = serializer.decode(jsonl_bytes)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
    
    def test_roundtrip_encoding(self):
        """Test encoding and decoding preserves data."""
        serializer = JsonLinesSerializer()
        original_data = [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"},
            {"id": 3, "value": "third"}
        ]
        
        encoded = serializer.encode(original_data)
        decoded = serializer.decode(encoded)
        
        assert decoded == original_data
    
    def test_decode_with_empty_lines(self):
        """Test decoding skips empty lines."""
        serializer = XWJsonLinesSerializer()
        jsonl_str = '{"name": "Alice"}\n\n{"name": "Bob"}\n'
        
        result = serializer.decode(jsonl_str)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
    
    def test_mime_types(self):
        """Test JSONL MIME types are correct."""
        serializer = XWJsonLinesSerializer()
        assert "application/x-ndjson" in serializer.media_types
        assert "application/jsonl" in serializer.media_types
    
    def test_file_extensions(self):
        """Test JSONL file extensions are correct."""
        serializer = XWJsonLinesSerializer()
        assert ".jsonl" in serializer.file_extensions
        assert ".ndjson" in serializer.file_extensions
        assert ".jsonlines" in serializer.file_extensions
    
    def test_streaming_friendly_format(self):
        """Test format is suitable for streaming (one object per line)."""
        serializer = XWJsonLinesSerializer()
        data = [{"log": f"entry_{i}"} for i in range(100)]
        
        encoded = serializer.encode(data)
        lines = encoded.strip().split('\n')
        
        # Each line should be independently parseable
        assert len(lines) == 100
        for line in lines:
            assert line.startswith('{"log"')
            assert line.endswith('}')

