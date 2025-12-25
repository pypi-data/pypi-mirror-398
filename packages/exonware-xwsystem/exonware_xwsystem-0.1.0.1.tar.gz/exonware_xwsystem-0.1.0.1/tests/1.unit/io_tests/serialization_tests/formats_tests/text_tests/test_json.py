"""
Unit tests for JSON serializer

Tests XWJsonSerializer implementation.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
from exonware.xwsystem.io.serialization.base import ASerialization


@pytest.mark.xwsystem_unit
class TestJsonSerializer:
    """Test JsonSerializer implementation."""
    
    def test_json_serializer_can_be_instantiated(self):
        """Test that JsonSerializer can be created."""
        serializer = JsonSerializer()
        assert serializer is not None
    
    def test_json_serializer_extends_aserialization(self):
        """Test JsonSerializer extends ASerialization."""
        assert issubclass(JsonSerializer, ASerialization)
    
    def test_json_serializer_has_encode_decode(self):
        """Test JsonSerializer has codec methods."""
        serializer = JsonSerializer()
        assert hasattr(serializer, 'encode')
        assert hasattr(serializer, 'decode')
        assert callable(serializer.encode)
        assert callable(serializer.decode)

