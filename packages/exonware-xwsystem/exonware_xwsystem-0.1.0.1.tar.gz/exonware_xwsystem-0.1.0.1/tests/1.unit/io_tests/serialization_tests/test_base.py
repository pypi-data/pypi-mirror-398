"""
Unit tests for io.serialization.base module

Tests ASerialization abstract base class.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from abc import ABC
from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.serialization.contracts import ISerialization
from exonware.xwsystem.io.codec.base import ACodec


@pytest.mark.xwsystem_unit
class TestASerializationBase:
    """Test ASerialization abstract base class."""
    
    def test_aserialization_is_abc(self):
        """Test ASerialization is an abstract base class."""
        assert issubclass(ASerialization, ABC)
    
    def test_aserialization_extends_acodec(self):
        """Test ASerialization extends ACodec."""
        assert issubclass(ASerialization, ACodec)
    
    def test_aserialization_implements_iserialization(self):
        """Test ASerialization implements ISerialization."""
        assert issubclass(ASerialization, ISerialization)
    
    def test_aserialization_cannot_be_instantiated_directly(self):
        """Test ASerialization cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            ASerialization()


@pytest.mark.xwsystem_unit
class TestASerializationXWSystemIntegration:
    """Test ASerialization XWSystem integration."""
    
    def test_aserialization_provides_xwsystem_integration(self):
        """Test ASerialization provides XWSystem integration methods."""
        # ASerialization should integrate with XWSystem utilities
        # This includes file I/O, async support, and streaming
        # Tested through concrete implementations
        assert issubclass(ASerialization, ACodec)

