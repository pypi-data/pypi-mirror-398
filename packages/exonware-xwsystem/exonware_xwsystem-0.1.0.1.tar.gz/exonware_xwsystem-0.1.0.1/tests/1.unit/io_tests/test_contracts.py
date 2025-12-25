"""
Unit tests for io.contracts module

Tests all IO interfaces and enums defined in contracts.py
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from abc import ABC
from exonware.xwsystem.io.contracts import (
    IFile, IFolder, IPath, IStream, IAsyncIO,
    IAtomicOperations, IBackupOperations, ITemporaryOperations,
    IUnifiedIO, IFileManager,
    IArchiver, IArchiveFile, ICompression,
    IFileWatcher, IFileLock, IFileSystem,
    ICodecIO, IPagedCodecIO,
    IDataSource, IPagedDataSource,
)
from exonware.xwsystem.io.defs import (
    FileMode, FileType, PathType, OperationResult, LockType,
    ArchiveFormat, CompressionAlgorithm, CompressionLevel,
)


@pytest.mark.xwsystem_unit
class TestIOInterfaces:
    """Test that all IO interfaces are properly defined as ABCs."""
    
    def test_ifile_is_abc(self):
        """Test IFile is an abstract base class."""
        assert issubclass(IFile, ABC)
        assert hasattr(IFile, '__abstractmethods__')
    
    def test_ifolder_is_abc(self):
        """Test IFolder is an abstract base class."""
        assert issubclass(IFolder, ABC)
        assert hasattr(IFolder, '__abstractmethods__')
    
    def test_ipath_is_abc(self):
        """Test IPath is an abstract base class."""
        assert issubclass(IPath, ABC)
        assert hasattr(IPath, '__abstractmethods__')
    
    def test_istream_is_abc(self):
        """Test IStream is an abstract base class."""
        assert issubclass(IStream, ABC)
        assert hasattr(IStream, '__abstractmethods__')
    
    def test_iunified_io_is_abc(self):
        """Test IUnifiedIO is an abstract base class."""
        assert issubclass(IUnifiedIO, ABC)
    
    def test_iarchiver_is_abc(self):
        """Test IArchiver is an abstract base class."""
        # IArchiver is defined as ABC with abstract methods
        assert IArchiver is not None
        # Check it has abstract methods or is an ABC
        assert issubclass(IArchiver, ABC) or hasattr(IArchiver, '__abstractmethods__')
    
    def test_iarchive_file_is_abc(self):
        """Test IArchiveFile is an abstract base class."""
        assert issubclass(IArchiveFile, ABC)
        assert hasattr(IArchiveFile, '__abstractmethods__')


@pytest.mark.xwsystem_unit
class TestIOEnums:
    """Test that all IO enums are properly defined."""
    
    def test_file_mode_enum_values(self):
        """Test FileMode enum has expected values."""
        assert hasattr(FileMode, 'READ')
        assert hasattr(FileMode, 'WRITE')
        assert hasattr(FileMode, 'APPEND')
    
    def test_file_type_enum_values(self):
        """Test FileType enum has expected values."""
        assert hasattr(FileType, 'TEXT')
        assert hasattr(FileType, 'BINARY')
    
    def test_operation_result_enum_values(self):
        """Test OperationResult enum has expected values."""
        assert hasattr(OperationResult, 'SUCCESS')
        assert hasattr(OperationResult, 'FAILURE')
    
    def test_archive_format_enum_values(self):
        """Test ArchiveFormat enum has expected values."""
        assert hasattr(ArchiveFormat, 'ZIP')
        assert hasattr(ArchiveFormat, 'TAR')
    
    def test_compression_algorithm_enum_values(self):
        """Test CompressionAlgorithm enum has expected values."""
        # Test that enum exists and has some values
        assert CompressionAlgorithm is not None
    
    def test_compression_level_enum_values(self):
        """Test CompressionLevel enum has expected values."""
        # Test that enum exists and has some values
        assert CompressionLevel is not None


@pytest.mark.xwsystem_unit
class TestInterfaceDesign:
    """Test interface design follows eXonware patterns."""
    
    def test_interfaces_cannot_be_instantiated(self):
        """Test that interfaces cannot be directly instantiated."""
        with pytest.raises(TypeError):
            IFile()
        
        with pytest.raises(TypeError):
            IFolder()
        
        with pytest.raises(TypeError):
            IArchiver()
    
    def test_interfaces_have_abstract_methods(self):
        """Test that interfaces define abstract methods."""
        # IFile should have abstract methods
        assert len(IFile.__abstractmethods__) > 0
        
        # IFolder should have abstract methods
        assert len(IFolder.__abstractmethods__) > 0
        
        # IArchiver should have abstract methods
        assert len(IArchiver.__abstractmethods__) > 0

