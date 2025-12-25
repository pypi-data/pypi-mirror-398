"""
Unit tests for io.archive.base module

Tests abstract base classes for archive formats and operations.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from abc import ABC
from exonware.xwsystem.io.archive.base import (
    AArchiveFormat,
    ACompressor,
    AArchiver,
    AArchiveFile,
)


@pytest.mark.xwsystem_unit
class TestArchiveAbstractBases:
    """Test archive abstract base classes."""
    
    def test_aarchive_format_is_abc(self):
        """Test AArchiveFormat is an abstract base class."""
        assert issubclass(AArchiveFormat, ABC)
    
    def test_acompressor_is_abc(self):
        """Test ACompressor is an abstract base class."""
        assert issubclass(ACompressor, ABC)
    
    def test_aarchiver_is_abc(self):
        """Test AArchiver is an abstract base class."""
        assert issubclass(AArchiver, ABC)
    
    def test_aarchive_file_is_abc(self):
        """Test AArchiveFile is an abstract base class."""
        assert issubclass(AArchiveFile, ABC)
    
    def test_aarchiver_extends_acodec(self):
        """Test AArchiver extends ACodec following I→A→XW pattern."""
        from exonware.xwsystem.io.codec.base import ACodec
        assert issubclass(AArchiver, ACodec)

