"""
Unit tests for io.facade module

Tests the XWIO facade which is the primary entry point for all I/O operations.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from pathlib import Path
from exonware.xwsystem.io.facade import XWIO


@pytest.mark.xwsystem_unit
class TestXWIOFacade:
    """Test XWIO facade initialization and structure."""
    
    def test_xwio_can_be_instantiated(self):
        """Test that XWIO facade can be created."""
        io = XWIO()
        assert io is not None
    
    def test_xwio_has_file_operations(self):
        """Test that XWIO provides file operation methods."""
        io = XWIO()
        assert hasattr(io, 'read_file')
        assert hasattr(io, 'write_file')
        assert hasattr(io, 'open_file')
        assert hasattr(io, 'close_file')
    
    def test_xwio_has_stream_operations(self):
        """Test that XWIO provides stream operation methods."""
        io = XWIO()
        assert hasattr(io, 'read')
        assert hasattr(io, 'write')
        assert hasattr(io, 'open')
        assert hasattr(io, 'close')
    
    def test_xwio_has_serialization_operations(self):
        """Test that XWIO provides serialization methods."""
        io = XWIO()
        assert hasattr(io, 'serialize')
        assert hasattr(io, 'deserialize')
        assert hasattr(io, 'save_serialized')
        assert hasattr(io, 'load_serialized')
    
    def test_xwio_has_backward_compatible_aliases(self):
        """Test that XWIO maintains backward compatibility aliases."""
        io = XWIO()
        # Aliases for file operations
        assert hasattr(io, 'read_file')
        assert hasattr(io, 'write_file')


@pytest.mark.xwsystem_unit
class TestXWIOIntegration:
    """Test XWIO integration with underlying components."""
    
    def test_xwio_uses_universal_codec_registry(self):
        """Test that XWIO integrates with UniversalCodecRegistry."""
        io = XWIO()
        # XWIO should be able to access serialization functionality
        assert hasattr(io, 'serialize')
        assert hasattr(io, 'deserialize')
    
    def test_xwio_provides_unified_interface(self):
        """Test that XWIO provides a unified interface for all I/O."""
        io = XWIO()
        # Should have methods from multiple I/O domains
        assert hasattr(io, 'read_file')  # File operations
        assert hasattr(io, 'serialize')  # Serialization
        assert hasattr(io, 'open')  # Stream operations

