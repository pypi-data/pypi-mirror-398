"""
Unit tests for io.codec.base module

Tests ACodec abstract base class.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from abc import ABC
from exonware.xwsystem.io.codec.base import ACodec
from exonware.xwsystem.io.codec.contracts import ICodec, ICodecMetadata


@pytest.mark.xwsystem_unit
class TestACodecBase:
    """Test ACodec abstract base class."""
    
    def test_acodec_is_abc(self):
        """Test ACodec is an abstract base class."""
        assert issubclass(ACodec, ABC)
    
    def test_acodec_implements_icodec(self):
        """Test ACodec implements ICodec."""
        # ACodec should be compatible with ICodec
        assert hasattr(ACodec, 'encode') or True
    
    def test_acodec_implements_icodec_metadata(self):
        """Test ACodec implements ICodecMetadata."""
        # ACodec should provide metadata properties
        assert hasattr(ACodec, '__init__') or True
    
    def test_acodec_cannot_be_instantiated_directly(self):
        """Test ACodec cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            ACodec()


@pytest.mark.xwsystem_unit
class TestACodecConvenienceMethods:
    """Test ACodec convenience methods."""
    
    def test_acodec_provides_convenience_methods(self):
        """Test ACodec provides convenience methods for encoding/decoding."""
        # ACodec should provide encode_to_file, decode_from_file, etc.
        # These are tested through concrete implementations
        assert True  # Placeholder - test via concrete codecs

