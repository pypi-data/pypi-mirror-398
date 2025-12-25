"""
Unit tests for io.archive.archivers module

Tests concrete archiver implementations (XWZipArchiver, XWTarArchiver).
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from exonware.xwsystem.io.archive.archivers import ZipArchiver, TarArchiver
from exonware.xwsystem.io.archive.base import AArchiver


@pytest.mark.xwsystem_unit
class TestZipArchiver:
    """Test XWZipArchiver implementation."""
    
    def test_zip_archiver_can_be_instantiated(self):
        """Test that XWZipArchiver can be created."""
        archiver = ZipArchiver()
        assert archiver is not None
    
    def test_zip_archiver_extends_aarchiver(self):
        """Test XWZipArchiver extends AArchiver."""
        assert issubclass(ZipArchiver, AArchiver)
    
    def test_zip_archiver_has_encode_decode(self):
        """Test XWZipArchiver has codec methods."""
        archiver = ZipArchiver()
        assert hasattr(archiver, 'encode')
        assert hasattr(archiver, 'decode')


@pytest.mark.xwsystem_unit
class TestTarArchiver:
    """Test XWTarArchiver implementation."""
    
    def test_tar_archiver_can_be_instantiated(self):
        """Test that XWTarArchiver can be created."""
        archiver = TarArchiver()
        assert archiver is not None
    
    def test_tar_archiver_extends_aarchiver(self):
        """Test XWTarArchiver extends AArchiver."""
        assert issubclass(TarArchiver, AArchiver)
    
    def test_tar_archiver_has_encode_decode(self):
        """Test XWTarArchiver has codec methods."""
        archiver = TarArchiver()
        assert hasattr(archiver, 'encode')
        assert hasattr(archiver, 'decode')


@pytest.mark.xwsystem_unit
class TestBackwardCompatibility:
    """Test backward compatibility aliases."""
    
    def test_ziparchiver_alias_exists(self):
        """Test ZipArchiver alias exists for backward compatibility."""
        from exonware.xwsystem.io.archive import ZipArchiver
        assert ZipArchiver is ZipArchiver
    
    def test_tararchiver_alias_exists(self):
        """Test TarArchiver alias exists for backward compatibility."""
        from exonware.xwsystem.io.archive import TarArchiver
        assert TarArchiver is TarArchiver

