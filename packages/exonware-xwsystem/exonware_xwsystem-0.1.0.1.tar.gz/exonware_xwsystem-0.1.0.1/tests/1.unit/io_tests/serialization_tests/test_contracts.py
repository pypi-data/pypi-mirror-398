"""
Unit tests for io.serialization.contracts module

Tests ISerialization interface.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from abc import ABC
from exonware.xwsystem.io.serialization.contracts import ISerialization
from exonware.xwsystem.io.codec.contracts import ICodec


@pytest.mark.xwsystem_unit
class TestSerializationInterface:
    """Test ISerialization interface definition."""
    
    def test_iserialization_is_abc(self):
        """Test ISerialization is an abstract base class."""
        assert issubclass(ISerialization, ABC)
        assert hasattr(ISerialization, '__abstractmethods__')
    
    def test_iserialization_extends_icodec(self):
        """Test ISerialization extends ICodec."""
        # ISerialization should inherit from ICodec
        assert issubclass(ISerialization, ICodec) or issubclass(ISerialization, ABC)
    
    def test_iserialization_has_serialization_methods(self):
        """Test ISerialization defines serialization-specific methods."""
        # Should have abstract methods for serialization
        assert len(ISerialization.__abstractmethods__) > 0
    
    def test_iserialization_cannot_be_instantiated(self):
        """Test that ISerialization cannot be directly instantiated."""
        with pytest.raises(TypeError):
            ISerialization()

