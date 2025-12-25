"""
Unit tests for YAML serializer

Tests XWYamlSerializer implementation.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from exonware.xwsystem.io.serialization.formats.text.yaml import YamlSerializer
from exonware.xwsystem.io.serialization.base import ASerialization


@pytest.mark.xwsystem_unit
class TestYamlSerializer:
    """Test YamlSerializer implementation."""
    
    def test_yaml_serializer_can_be_instantiated(self):
        """Test that YamlSerializer can be created."""
        serializer = YamlSerializer()
        assert serializer is not None
    
    def test_yaml_serializer_extends_aserialization(self):
        """Test YamlSerializer extends ASerialization."""
        assert issubclass(YamlSerializer, ASerialization)
    
    def test_yaml_serializer_has_encode_decode(self):
        """Test YamlSerializer has codec methods."""
        serializer = YamlSerializer()
        assert hasattr(serializer, 'encode')
        assert hasattr(serializer, 'decode')

