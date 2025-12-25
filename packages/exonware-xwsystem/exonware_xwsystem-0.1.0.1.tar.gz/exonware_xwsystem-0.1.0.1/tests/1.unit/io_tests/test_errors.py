"""
Unit tests for io.errors module

Tests all IO exception classes.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from exonware.xwsystem.io.errors import (
    FileNotFoundError,
    FilePermissionError,
    FileLockError,
    FileReadError,
    FileWriteError,
    FileDeleteError,
)


@pytest.mark.xwsystem_unit
class TestFileExceptions:
    """Test file-related exceptions."""
    
    def test_file_not_found_error_extends_ioerror(self):
        """Test FileNotFoundError extends Python's IOError."""
        assert issubclass(FileNotFoundError, IOError)
    
    def test_file_not_found_error_can_be_raised(self):
        """Test FileNotFoundError can be raised and caught."""
        with pytest.raises(FileNotFoundError):
            raise FileNotFoundError("file.txt not found")
    
    def test_file_permission_error_extends_ioerror(self):
        """Test FilePermissionError extends IOError."""
        assert issubclass(FilePermissionError, IOError)
    
    def test_file_lock_error_extends_ioerror(self):
        """Test FileLockError extends IOError."""
        assert issubclass(FileLockError, IOError)
    
    def test_file_read_error_extends_ioerror(self):
        """Test FileReadError extends IOError."""
        assert issubclass(FileReadError, IOError)
    
    def test_file_write_error_extends_ioerror(self):
        """Test FileWriteError extends IOError."""
        assert issubclass(FileWriteError, IOError)
    
    def test_file_delete_error_extends_ioerror(self):
        """Test FileDeleteError extends IOError."""
        assert issubclass(FileDeleteError, IOError)


@pytest.mark.xwsystem_unit
class TestExceptionUsability:
    """Test exception usability (Priority #2)."""
    
    def test_exceptions_have_clear_names(self):
        """Test exceptions have clear, descriptive names."""
        # Names should be self-documenting
        assert "NotFound" in FileNotFoundError.__name__
        assert "Permission" in FilePermissionError.__name__
        assert "Lock" in FileLockError.__name__
        assert "Read" in FileReadError.__name__
        assert "Write" in FileWriteError.__name__
        assert "Delete" in FileDeleteError.__name__
    
    def test_exceptions_can_be_caught_specifically(self):
        """Test exceptions can be caught by specific type."""
        try:
            raise FileNotFoundError("file.txt not found")
        except FileNotFoundError as e:
            assert isinstance(e, FileNotFoundError)
            assert isinstance(e, IOError)
            assert "file.txt" in str(e)
    
    def test_file_errors_provide_context(self):
        """Test file errors can carry contextual information."""
        try:
            raise FileWriteError("Cannot write to /protected/file.txt")
        except FileWriteError as e:
            error_msg = str(e)
            assert "write" in error_msg.lower() or "Cannot write" in error_msg

