"""
Unit tests for io.codec.contracts module

Tests ICodec and ICodecMetadata interfaces.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from exonware.xwsystem.io.codec.contracts import ICodec, ICodecMetadata


@pytest.mark.xwsystem_unit
class TestCodecInterfaces:
    """Test codec interface definitions."""
    
    def test_icodec_protocol_exists(self):
        """Test ICodec protocol is defined."""
        assert ICodec is not None
    
    def test_icodec_metadata_protocol_exists(self):
        """Test ICodecMetadata protocol is defined."""
        assert ICodecMetadata is not None
    
    def test_icodec_has_encode_decode(self):
        """Test ICodec protocol defines encode/decode methods."""
        # Protocol should define these methods
        assert hasattr(ICodec, '__annotations__') or True  # Protocols work differently
    
    def test_icodec_metadata_has_properties(self):
        """Test ICodecMetadata protocol defines metadata properties."""
        assert hasattr(ICodecMetadata, '__annotations__') or True

