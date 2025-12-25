"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri  
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

IO module errors - ALL exceptions in ONE place.

Consolidated from all submodules for maintainability.
"""

from typing import Any, Optional, Union
from pathlib import Path


# From ROOT
class FileNotFoundError(IOError):
    """Raised when file is not found."""
    pass


# From ROOT
class FilePermissionError(IOError):
    """Raised when file permission is denied."""
    pass


# From ROOT
class FileLockError(IOError):
    """Raised when file lock operation fails."""
    pass


# From ROOT
class FileReadError(IOError):
    """Raised when file read operation fails."""
    pass


# From ROOT
class FileWriteError(IOError):
    """Raised when file write operation fails."""
    pass


# From ROOT
class FileDeleteError(IOError):
    """Raised when file delete operation fails."""
    pass


# From ROOT
class FileCopyError(IOError):
    """Raised when file copy operation fails."""
    pass


# From ROOT
class FileMoveError(IOError):
    """Raised when file move operation fails."""
    pass


# From ROOT
class DirectoryError(IOError):
    """Raised when directory operation fails."""
    pass


# From ROOT
class DirectoryNotFoundError(DirectoryError):
    """Raised when directory is not found."""
    pass


# From ROOT
class DirectoryCreateError(DirectoryError):
    """Raised when directory creation fails."""
    pass


# From ROOT
class DirectoryDeleteError(DirectoryError):
    """Raised when directory deletion fails."""
    pass


# From ROOT
class PathError(IOError):
    """Raised when path operation fails."""
    pass


# From ROOT
class PathValidationError(PathError):
    """Raised when path validation fails."""
    pass


# From ROOT
class PathResolutionError(PathError):
    """Raised when path resolution fails."""
    pass


# From ROOT
class StreamError(IOError):
    """Raised when stream operation fails."""
    pass


# From ROOT
class StreamOpenError(StreamError):
    """Raised when stream opening fails."""
    pass


# From ROOT
class StreamCloseError(StreamError):
    """Raised when stream closing fails."""
    pass


# From ROOT
class StreamReadError(StreamError):
    """Raised when stream read fails."""
    pass


# From ROOT
class StreamWriteError(StreamError):
    """Raised when stream write fails."""
    pass


# From ROOT
class AtomicOperationError(IOError):
    """Raised when atomic operation fails."""
    pass


# From ROOT
class BackupError(IOError):
    """Raised when backup operation fails."""
    pass


# From ROOT
class TemporaryFileError(IOError):
    """Raised when temporary file operation fails."""
    pass


# From common
class CommonIOError(Exception):
    """Base exception for common IO utility errors."""
    
    def __init__(
        self,
        message: str,
        path: Optional[Path] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.path = path
        self.original_error = original_error
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.path:
            parts.append(f"[path: {self.path}]")
        if self.original_error:
            parts.append(f"[caused by: {type(self.original_error).__name__}]")
        return " ".join(parts)


# From common
class WatcherError(CommonIOError):
    """Error in file watcher operations."""
    pass


# From common
class LockError(CommonIOError):
    """Error in file lock operations."""
    pass


# From common
class LockTimeoutError(LockError):
    """Lock acquisition timeout."""
    
    def __init__(self, message: str, path: Optional[Path] = None, timeout: Optional[float] = None):
        super().__init__(message, path)
        self.timeout = timeout



# From file
class FileError(Exception):
    """Base exception for file operations."""
    
    def __init__(
        self,
        message: str,
        path: Optional[Path] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.path = path
        self.original_error = original_error
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.path:
            parts.append(f"[path: {self.path}]")
        if self.original_error:
            parts.append(f"[caused by: {type(self.original_error).__name__}]")
        return " ".join(parts)


# From file
class FileSourceError(FileError):
    """Error in file data source operations."""
    pass


# From file
class PagedSourceError(FileError):
    """Error in paged file source operations."""
    pass


# From file
class PagingStrategyError(FileError):
    """Error in paging strategy operations."""
    
    def __init__(
        self,
        message: str,
        strategy_id: Optional[str] = None,
        path: Optional[Path] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, path, original_error)
        self.strategy_id = strategy_id



# From folder
class FolderError(Exception):
    """Base exception for folder operations."""
    pass



# From stream
class CodecIOError(StreamError):
    """Error in codec I/O operations."""
    pass


# From stream
class AsyncIOError(StreamError):
    """Error in async I/O operations."""
    pass



# From filesystem
class FileSystemError(Exception):
    """Base exception for filesystem operations."""
    pass



# From archive
class ArchiveError(Exception):
    """Base exception for archive operations."""
    
    def __init__(
        self,
        message: str,
        archive_path: Optional[Path] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.archive_path = archive_path
        self.original_error = original_error
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.archive_path:
            parts.append(f"[archive: {self.archive_path}]")
        if self.original_error:
            parts.append(f"[caused by: {type(self.original_error).__name__}]")
        return " ".join(parts)


# From archive
class ArchiveFormatError(ArchiveError):
    """Error when archive format is unsupported or invalid."""
    
    def __init__(self, message: str, format_id: Optional[str] = None, archive_path: Optional[Path] = None):
        super().__init__(message, archive_path)
        self.format_id = format_id


# From archive
class ArchiveNotFoundError(ArchiveError):
    """Error when archiver lookup fails."""
    pass


# From archive
class ExtractionError(ArchiveError):
    """Error during archive extraction."""
    pass


# From archive
class CompressionError(Exception):
    """Error during compression operations."""
    
    def __init__(
        self,
        message: str,
        algorithm: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.algorithm = algorithm
        self.original_error = original_error


# From archive
class DecompressionError(CompressionError):
    """Error during decompression operations."""
    pass



# From manager
class ManagerError(Exception):
    """Base exception for manager operations."""
    pass


# From codec
class CodecError(Exception):
    """Base exception for codec operations."""
    pass


class SerializationError(Exception):
    """
    Base exception for serialization operations.
    
    Root cause fixed: Added missing SerializationError class that was being
    imported by serialization/base.py but didn't exist.
    
    Root cause fixed: Added __init__ to accept format_name and original_error
    parameters that are used throughout the serialization codebase.
    """
    
    def __init__(
        self,
        message: str,
        format_name: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize SerializationError.
        
        Args:
            message: Error message
            format_name: Optional format name (e.g., "JSON", "XML")
            original_error: Optional original exception that caused this error
        """
        super().__init__(message)
        self.format_name = format_name
        self.original_error = original_error
    
    def __str__(self) -> str:
        """Format error message with optional context."""
        parts = [super().__str__()]
        if self.format_name:
            parts.append(f"[format: {self.format_name}]")
        if self.original_error:
            parts.append(f"[caused by: {type(self.original_error).__name__}]")
        return " ".join(parts)


class EncodeError(CodecError):
    """Raised when encoding fails."""
    pass


class DecodeError(CodecError):
    """Raised when decoding fails."""
    pass


class CodecNotFoundError(CodecError):
    """Raised when codec is not found."""
    pass


class CodecRegistrationError(CodecError):
    """Raised when codec registration fails."""
    pass
