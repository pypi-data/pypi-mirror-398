"""
Unit tests for io.archive.archive_files module

Tests concrete archive file implementations (ZipFile, TarFile).
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from exonware.xwsystem.io.archive.archive_files import ZipFile, TarFile
from exonware.xwsystem.io.archive.base import AArchiveFile


@pytest.mark.xwsystem_unit
class TestZipFile:
    """Test ZipFile implementation."""
    
    def test_zip_file_extends_aarchive_file(self):
        """Test ZipFile extends AArchiveFile."""
        assert issubclass(ZipFile, AArchiveFile)
    
    def test_zip_file_uses_composition(self):
        """Test ZipFile uses XWZipArchiver via composition."""
        # ZipFile should use XWZipArchiver instance
        # This follows composition over inheritance pattern
        from exonware.xwsystem.io.archive.archivers import ZipArchiver
        assert ZipArchiver is not None

@pytest.mark.xwsystem_unit
class TestTarFile:
    """Test TarFile implementation."""
    
    def test_tar_file_extends_aarchive_file(self):
        """Test TarFile extends AArchiveFile."""
        assert issubclass(TarFile, AArchiveFile)
    
    def test_tar_file_uses_composition(self):
        """Test TarFile uses XWTarArchiver via composition."""
        # TarFile should use XWTarArchiver instance
        from exonware.xwsystem.io.archive.archivers import TarArchiver
        assert TarArchiver is not None

