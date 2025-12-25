"""
Unit tests for io.base module

Tests abstract base classes for IO operations.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from abc import ABC
from exonware.xwsystem.io.base import (
    AFile,
    AFolder,
    APath,
    AStream,
    AAsyncIO,
    AAtomicOperations,
    ABackupOperations,
    ATemporaryOperations,
)
from exonware.xwsystem.io.contracts import (
    IFile,
    IFolder,
    IPath,
    IStream,
    IAsyncIO,
    IAtomicOperations,
    IBackupOperations,
    ITemporaryOperations,
)


@pytest.mark.xwsystem_unit
class TestAbstractFileBase:
    """Test AFile abstract base class."""
    
    def test_afile_is_abc(self):
        """Test AFile is an abstract base class."""
        assert issubclass(AFile, ABC)
    
    def test_afile_implements_ifile(self):
        """Test AFile implements IFile interface."""
        assert issubclass(AFile, IFile)
    
    def test_afile_cannot_be_instantiated_directly(self):
        """Test AFile cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            AFile("/tmp/test.txt")


@pytest.mark.xwsystem_unit
class TestAbstractFolderBase:
    """Test AFolder abstract base class."""
    
    def test_afolder_is_abc(self):
        """Test AFolder is an abstract base class."""
        assert issubclass(AFolder, ABC)
    
    def test_afolder_implements_ifolder(self):
        """Test AFolder implements IFolder interface."""
        assert issubclass(AFolder, IFolder)
    
    def test_afolder_cannot_be_instantiated_directly(self):
        """Test AFolder cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            AFolder("/tmp/testdir")


@pytest.mark.xwsystem_unit
class TestAbstractStreamBase:
    """Test AStream abstract base class."""
    
    def test_astream_is_abc(self):
        """Test AStream is an abstract base class."""
        assert issubclass(AStream, ABC)
    
    def test_astream_implements_istream(self):
        """Test AStream implements IStream interface."""
        assert issubclass(AStream, IStream)


@pytest.mark.xwsystem_unit
class TestAbstractOperationsBase:
    """Test operation abstract base classes."""
    
    def test_aatomic_operations_is_abc(self):
        """Test AAtomicOperations is an abstract base class."""
        assert issubclass(AAtomicOperations, ABC)
        assert issubclass(AAtomicOperations, IAtomicOperations)
    
    def test_abackup_operations_is_abc(self):
        """Test ABackupOperations is an abstract base class."""
        assert issubclass(ABackupOperations, ABC)
        assert issubclass(ABackupOperations, IBackupOperations)
    
    def test_atemporary_operations_is_abc(self):
        """Test ATemporaryOperations is an abstract base class."""
        assert issubclass(ATemporaryOperations, ABC)
        assert issubclass(ATemporaryOperations, ITemporaryOperations)


@pytest.mark.xwsystem_unit
class TestIAXWPattern:
    """Test I→A→XW pattern implementation."""
    
    def test_interface_to_abstract_hierarchy(self):
        """Test that abstract classes properly extend interfaces."""
        # File hierarchy
        assert issubclass(AFile, IFile)
        assert issubclass(AFile, ABC)
        
        # Folder hierarchy
        assert issubclass(AFolder, IFolder)
        assert issubclass(AFolder, ABC)
        
        # Stream hierarchy
        assert issubclass(AStream, IStream)
        assert issubclass(AStream, ABC)
    
    def test_abstract_classes_have_abstract_methods(self):
        """Test that abstract classes define abstract methods."""
        # AFile should have abstract methods
        assert len(AFile.__abstractmethods__) > 0
        
        # AFolder should have abstract methods
        assert len(AFolder.__abstractmethods__) > 0
        
        # AStream should have abstract methods
        assert len(AStream.__abstractmethods__) > 0

