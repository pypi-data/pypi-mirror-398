"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

IO module contracts - interfaces and enums for input/output operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, AsyncGenerator, BinaryIO, TextIO, Protocol, runtime_checkable, Callable, Iterator
from typing_extensions import TypeAlias
from pathlib import Path

# Type aliases for codec options
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity
EncodeOptions: TypeAlias = dict[str, Any]
DecodeOptions: TypeAlias = dict[str, Any]
Serializer: TypeAlias = 'ICodec[Any, bytes]'
Formatter: TypeAlias = 'ICodec[Any, str]'

# Import enums from types module
from .defs import (
    FileMode,
    FileType,
    PathType,
    OperationResult,
    LockType,
    CodecCapability,
)


# ============================================================================
# FILE INTERFACES
# ============================================================================

class IFile(ABC):
    """
    Interface for file operations with both static and instance methods.
    
    Provides comprehensive file operations including:
    - File I/O operations (read, write, save, load)
    - File metadata operations (size, permissions, timestamps)
    - File validation and safety checks
    - Static utility methods for file operations
    """
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def open(self, mode: FileMode = FileMode.READ) -> None:
        """Open file with specified mode."""
        pass
    
    @abstractmethod
    def read(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Read from file."""
        pass
    
    @abstractmethod
    def write(self, data: Union[str, bytes]) -> int:
        """Write to file."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close file."""
        pass
    
    @abstractmethod
    def save(self, data: Any, **kwargs) -> bool:
        """Save data to file."""
        pass
    
    @abstractmethod
    def load(self, **kwargs) -> Any:
        """Load data from file."""
        pass
    
    @abstractmethod
    def save_as(self, path: Union[str, Path], data: Any, **kwargs) -> bool:
        """Save data to specific path."""
        pass
    
    @abstractmethod
    def to_file(self, path: Union[str, Path], **kwargs) -> bool:
        """Write current object to file."""
        pass
    
    @abstractmethod
    def from_file(self, path: Union[str, Path], **kwargs) -> 'IFile':
        """Load object from file."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    def exists(path: Union[str, Path]) -> bool:
        """Check if file exists."""
        pass
    
    @staticmethod
    @abstractmethod
    def size(path: Union[str, Path]) -> int:
        """Get file size."""
        pass
    
    @staticmethod
    @abstractmethod
    def delete(path: Union[str, Path]) -> bool:
        """Delete file."""
        pass
    
    @staticmethod
    @abstractmethod
    def copy(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Copy file."""
        pass
    
    @staticmethod
    @abstractmethod
    def move(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Move file."""
        pass
    
    @staticmethod
    @abstractmethod
    def rename(old_path: Union[str, Path], new_path: Union[str, Path]) -> bool:
        """Rename file."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_modified_time(path: Union[str, Path]) -> float:
        """Get file modification time."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_created_time(path: Union[str, Path]) -> float:
        """Get file creation time."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_permissions(path: Union[str, Path]) -> int:
        """Get file permissions."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_readable(path: Union[str, Path]) -> bool:
        """Check if file is readable."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_writable(path: Union[str, Path]) -> bool:
        """Check if file is writable."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_executable(path: Union[str, Path]) -> bool:
        """Check if file is executable."""
        pass
    
    @staticmethod
    @abstractmethod
    def read_text(path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Read file as text."""
        pass
    
    @staticmethod
    @abstractmethod
    def read_bytes(path: Union[str, Path]) -> bytes:
        """Read file as bytes."""
        pass
    
    @staticmethod
    @abstractmethod
    def write_text(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """Write text to file."""
        pass
    
    @staticmethod
    @abstractmethod
    def write_bytes(path: Union[str, Path], content: bytes) -> bool:
        """Write bytes to file."""
        pass
    
    @staticmethod
    @abstractmethod
    def safe_read_text(path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
        """Safely read text file, returning None on error."""
        pass
    
    @staticmethod
    @abstractmethod
    def safe_read_bytes(path: Union[str, Path]) -> Optional[bytes]:
        """Safely read binary file, returning None on error."""
        pass
    
    @staticmethod
    @abstractmethod
    def safe_write_text(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """Safely write text to file."""
        pass
    
    @staticmethod
    @abstractmethod
    def safe_write_bytes(path: Union[str, Path], content: bytes) -> bool:
        """Safely write bytes to file."""
        pass
    
    # ============================================================================
    # STATIC UTILITY METHODS (File Manager Features)
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    def atomic_write(file_path: Union[str, Path], data: Union[str, bytes], 
                    backup: bool = True) -> OperationResult:
        """Atomically write data to file (static version)."""
        pass
    
    @staticmethod
    @abstractmethod
    def atomic_copy(source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically copy file (static version)."""
        pass
    
    @staticmethod
    @abstractmethod
    def atomic_move(source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically move file (static version)."""
        pass
    
    @staticmethod
    @abstractmethod
    def atomic_delete(file_path: Union[str, Path], backup: bool = True) -> OperationResult:
        """Atomically delete file (static version)."""
        pass
    
    @staticmethod
    @abstractmethod
    def create_backup(source: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[Path]:
        """Create backup of file (static version)."""
        pass
    
    @staticmethod
    @abstractmethod
    def restore_backup(backup_path: Union[str, Path], target: Union[str, Path]) -> OperationResult:
        """Restore from backup (static version)."""
        pass
    
    @staticmethod
    @abstractmethod
    def create_temp_file(suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary file (static version)."""
        pass
    
    @staticmethod
    @abstractmethod
    def create_temp_directory(suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary directory (static version)."""
        pass


# ============================================================================
# FOLDER INTERFACES
# ============================================================================

class IFolder(ABC):
    """
    Interface for folder/directory operations with both static and instance methods.
    
    Provides comprehensive directory operations including:
    - Directory I/O operations (create, delete, list, walk)
    - Directory metadata operations (size, permissions, contents)
    - Directory validation and safety checks
    - Static utility methods for directory operations
    """
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def create(self, parents: bool = True, exist_ok: bool = True) -> bool:
        """Create directory."""
        pass
    
    @abstractmethod
    def delete(self, recursive: bool = False) -> bool:
        """Delete directory."""
        pass
    
    @abstractmethod
    def list_files(self, pattern: Optional[str] = None, recursive: bool = False) -> list[Path]:
        """List files in directory."""
        pass
    
    @abstractmethod
    def list_directories(self, recursive: bool = False) -> list[Path]:
        """List subdirectories."""
        pass
    
    @abstractmethod
    def walk(self) -> list[tuple[Path, list[str], list[str]]]:
        """Walk directory tree."""
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """Get directory size."""
        pass
    
    @abstractmethod
    def is_empty(self) -> bool:
        """Check if directory is empty."""
        pass
    
    @abstractmethod
    def copy_to(self, destination: Union[str, Path]) -> bool:
        """Copy directory to destination."""
        pass
    
    @abstractmethod
    def move_to(self, destination: Union[str, Path]) -> bool:
        """Move directory to destination."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    def exists(path: Union[str, Path]) -> bool:
        """Check if directory exists."""
        pass
    
    @staticmethod
    @abstractmethod
    def create_dir(path: Union[str, Path], parents: bool = True, exist_ok: bool = True) -> bool:
        """Create directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def delete_dir(path: Union[str, Path], recursive: bool = False) -> bool:
        """Delete directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def list_files_static(path: Union[str, Path], pattern: Optional[str] = None, recursive: bool = False) -> list[Path]:
        """List files in directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def list_directories_static(path: Union[str, Path], recursive: bool = False) -> list[Path]:
        """List subdirectories."""
        pass
    
    @staticmethod
    @abstractmethod
    def walk_static(path: Union[str, Path]) -> list[tuple[Path, list[str], list[str]]]:
        """Walk directory tree."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_size_static(path: Union[str, Path]) -> int:
        """Get directory size."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_empty_static(path: Union[str, Path]) -> bool:
        """Check if directory is empty."""
        pass
    
    @staticmethod
    @abstractmethod
    def copy_dir(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Copy directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def move_dir(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Move directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_permissions(path: Union[str, Path]) -> int:
        """Get directory permissions."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_readable(path: Union[str, Path]) -> bool:
        """Check if directory is readable."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_writable(path: Union[str, Path]) -> bool:
        """Check if directory is writable."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_executable(path: Union[str, Path]) -> bool:
        """Check if directory is executable."""
        pass


# ============================================================================
# PATH INTERFACES
# ============================================================================

class IPath(ABC):
    """
    Interface for path operations with both static and instance methods.
    
    Provides comprehensive path operations including:
    - Path manipulation (resolve, normalize, join, split)
    - Path validation and safety checks
    - Static utility methods for path operations
    """
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    def normalize(path: Union[str, Path]) -> Path:
        """Normalize path."""
        pass
    
    @staticmethod
    @abstractmethod
    def resolve(path: Union[str, Path]) -> Path:
        """Resolve path."""
        pass
    
    @staticmethod
    @abstractmethod
    def absolute(path: Union[str, Path]) -> Path:
        """Get absolute path."""
        pass
    
    @staticmethod
    @abstractmethod
    def relative(path: Union[str, Path], start: Optional[Union[str, Path]] = None) -> Path:
        """Get relative path."""
        pass
    
    @staticmethod
    @abstractmethod
    def join(*paths: Union[str, Path]) -> Path:
        """Join paths."""
        pass
    
    @staticmethod
    @abstractmethod
    def split(path: Union[str, Path]) -> tuple[Path, str]:
        """Split path into directory and filename."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_extension(path: Union[str, Path]) -> str:
        """Get file extension."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_stem(path: Union[str, Path]) -> str:
        """Get file stem (name without extension)."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_name(path: Union[str, Path]) -> str:
        """Get file/directory name."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_parent(path: Union[str, Path]) -> Path:
        """Get parent directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_absolute(path: Union[str, Path]) -> bool:
        """Check if path is absolute."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_relative(path: Union[str, Path]) -> bool:
        """Check if path is relative."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_parts(path: Union[str, Path]) -> tuple:
        """Get path parts."""
        pass
    
    @staticmethod
    @abstractmethod
    def match(path: Union[str, Path], pattern: str) -> bool:
        """Check if path matches pattern."""
        pass
    
    @staticmethod
    @abstractmethod
    def with_suffix(path: Union[str, Path], suffix: str) -> Path:
        """Get path with new suffix."""
        pass
    
    @staticmethod
    @abstractmethod
    def with_name(path: Union[str, Path], name: str) -> Path:
        """Get path with new name."""
        pass


# ============================================================================
# STREAM INTERFACES
# ============================================================================

class IStream(ABC):
    """
    Interface for stream operations with both static and instance methods.
    
    Provides comprehensive stream operations including:
    - Stream I/O operations (read, write, seek, tell)
    - Stream validation and safety checks
    - Static utility methods for stream operations
    """
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def read(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Read from stream."""
        pass
    
    @abstractmethod
    def write(self, data: Union[str, bytes]) -> int:
        """Write to stream."""
        pass
    
    @abstractmethod
    def seek(self, position: int, whence: int = 0) -> int:
        """Seek stream position."""
        pass
    
    @abstractmethod
    def tell(self) -> int:
        """Get current stream position."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush stream buffer."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close stream."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    def open_file(path: Union[str, Path], mode: str = 'r', encoding: Optional[str] = None) -> Union[TextIO, BinaryIO]:
        """Open file as stream."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_closed(stream: Union[TextIO, BinaryIO]) -> bool:
        """Check if stream is closed."""
        pass
    
    @staticmethod
    @abstractmethod
    def readable(stream: Union[TextIO, BinaryIO]) -> bool:
        """Check if stream is readable."""
        pass
    
    @staticmethod
    @abstractmethod
    def writable(stream: Union[TextIO, BinaryIO]) -> bool:
        """Check if stream is writable."""
        pass
    
    @staticmethod
    @abstractmethod
    def seekable(stream: Union[TextIO, BinaryIO]) -> bool:
        """Check if stream is seekable."""
        pass


# ============================================================================
# ASYNC I/O INTERFACES
# ============================================================================

class IAsyncIO(ABC):
    """
    Interface for async I/O operations with both static and instance methods.
    
    Provides comprehensive async I/O operations including:
    - Async file operations (aread, awrite, aseek, atell)
    - Async stream operations
    - Static utility methods for async operations
    """
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    async def aread(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Async read operation."""
        pass
    
    @abstractmethod
    async def awrite(self, data: Union[str, bytes]) -> int:
        """Async write operation."""
        pass
    
    @abstractmethod
    async def aseek(self, position: int, whence: int = 0) -> int:
        """Async seek operation."""
        pass
    
    @abstractmethod
    async def atell(self) -> int:
        """Async tell operation."""
        pass
    
    @abstractmethod
    async def aflush(self) -> None:
        """Async flush operation."""
        pass
    
    @abstractmethod
    async def aclose(self) -> None:
        """Async close operation."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    async def aopen_file(path: Union[str, Path], mode: str = 'r', encoding: Optional[str] = None) -> Any:
        """Async open file."""
        pass
    
    @staticmethod
    @abstractmethod
    async def aread_text(path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Async read text file."""
        pass
    
    @staticmethod
    @abstractmethod
    async def aread_bytes(path: Union[str, Path]) -> bytes:
        """Async read binary file."""
        pass
    
    @staticmethod
    @abstractmethod
    async def awrite_text(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """Async write text to file."""
        pass
    
    @staticmethod
    @abstractmethod
    async def awrite_bytes(path: Union[str, Path], content: bytes) -> bool:
        """Async write bytes to file."""
        pass


# ============================================================================
# ATOMIC OPERATIONS INTERFACES
# ============================================================================

class IAtomicOperations(ABC):
    """
    Interface for atomic operations with both static and instance methods.
    
    Provides comprehensive atomic operations including:
    - Atomic file operations (atomic write, copy, move, delete)
    - Backup and restore operations
    - Static utility methods for atomic operations
    """
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def atomic_write(self, file_path: Union[str, Path], data: Union[str, bytes], 
                    backup: bool = True) -> OperationResult:
        """Atomically write data to file."""
        pass
    
    @abstractmethod
    def atomic_copy(self, source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically copy file."""
        pass
    
    @abstractmethod
    def atomic_move(self, source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically move file."""
        pass
    
    @abstractmethod
    def atomic_delete(self, file_path: Union[str, Path], backup: bool = True) -> OperationResult:
        """Atomically delete file."""
        pass
    
    @abstractmethod
    def atomic_rename(self, old_path: Union[str, Path], new_path: Union[str, Path]) -> OperationResult:
        """Atomically rename file."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    def atomic_write_static(file_path: Union[str, Path], data: Union[str, bytes], 
                           backup: bool = True) -> OperationResult:
        """Atomically write data to file."""
        pass
    
    @staticmethod
    @abstractmethod
    def atomic_copy_static(source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically copy file."""
        pass
    
    @staticmethod
    @abstractmethod
    def atomic_move_static(source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically move file."""
        pass
    
    @staticmethod
    @abstractmethod
    def atomic_delete_static(file_path: Union[str, Path], backup: bool = True) -> OperationResult:
        """Atomically delete file."""
        pass
    
    @staticmethod
    @abstractmethod
    def atomic_rename_static(old_path: Union[str, Path], new_path: Union[str, Path]) -> OperationResult:
        """Atomically rename file."""
        pass


# ============================================================================
# BACKUP OPERATIONS INTERFACES
# ============================================================================

class IBackupOperations(ABC):
    """
    Interface for backup operations with both static and instance methods.
    
    Provides comprehensive backup operations including:
    - Backup creation and restoration
    - Backup management and cleanup
    - Static utility methods for backup operations
    """
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def create_backup(self, source: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[Path]:
        """Create backup of file or directory."""
        pass
    
    @abstractmethod
    def restore_backup(self, backup_path: Union[str, Path], target: Union[str, Path]) -> OperationResult:
        """Restore from backup."""
        pass
    
    @abstractmethod
    def list_backups(self, backup_dir: Union[str, Path]) -> list[Path]:
        """List available backups."""
        pass
    
    @abstractmethod
    def cleanup_backups(self, backup_dir: Union[str, Path], max_age_days: int = 30) -> int:
        """Cleanup old backups."""
        pass
    
    @abstractmethod
    def verify_backup(self, backup_path: Union[str, Path]) -> bool:
        """Verify backup integrity."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    def create_backup_static(source: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[Path]:
        """Create backup of file or directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def restore_backup_static(backup_path: Union[str, Path], target: Union[str, Path]) -> OperationResult:
        """Restore from backup."""
        pass
    
    @staticmethod
    @abstractmethod
    def list_backups_static(backup_dir: Union[str, Path]) -> list[Path]:
        """List available backups."""
        pass
    
    @staticmethod
    @abstractmethod
    def cleanup_backups_static(backup_dir: Union[str, Path], max_age_days: int = 30) -> int:
        """Cleanup old backups."""
        pass
    
    @staticmethod
    @abstractmethod
    def verify_backup_static(backup_path: Union[str, Path]) -> bool:
        """Verify backup integrity."""
        pass


# ============================================================================
# TEMPORARY OPERATIONS INTERFACES
# ============================================================================

class ITemporaryOperations(ABC):
    """
    Interface for temporary operations with both static and instance methods.
    
    Provides comprehensive temporary operations including:
    - Temporary file and directory creation
    - Temporary resource cleanup
    - Static utility methods for temporary operations
    """
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def create_temp_file(self, suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary file."""
        pass
    
    @abstractmethod
    def create_temp_directory(self, suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary directory."""
        pass
    
    @abstractmethod
    def cleanup_temp(self, path: Union[str, Path]) -> bool:
        """Cleanup temporary file or directory."""
        pass
    
    @abstractmethod
    def cleanup_all_temp(self) -> int:
        """Cleanup all temporary files and directories."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    @abstractmethod
    def create_temp_file_static(suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary file."""
        pass
    
    @staticmethod
    @abstractmethod
    def create_temp_directory_static(suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def cleanup_temp_static(path: Union[str, Path]) -> bool:
        """Cleanup temporary file or directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def get_temp_base_dir() -> Path:
        """Get temporary base directory."""
        pass
    
    @staticmethod
    @abstractmethod
    def is_temp(path: Union[str, Path]) -> bool:
        """Check if path is temporary."""
        pass


# ============================================================================
# UNIFIED I/O INTERFACE
# ============================================================================

class IUnifiedIO(IFile, IFolder, IPath, IStream, IAsyncIO, IAtomicOperations, IBackupOperations, ITemporaryOperations):
    """
    Unified I/O interface combining all existing I/O capabilities.
    
    This is the unified interface for all input/output operations across XWSystem.
    It combines all existing I/O interfaces into a single, comprehensive interface
    that provides complete I/O functionality for any data source.
    
    Features:
    - File operations (read, write, save, load)
    - Directory operations (create, delete, list, walk)
    - Path operations (resolve, normalize, join, split)
    - Stream operations (open, read, write, seek)
    - Async operations (async read/write, async streams)
    - Atomic operations (atomic write, copy, move, delete)
    - Backup operations (create, restore, list, cleanup)
    - Temporary operations (create temp files/dirs, cleanup)
    
    This interface follows the xwsystem pattern of combining existing interfaces
    rather than creating new abstractions, maximizing code reuse and maintaining
    backward compatibility.
    """
    pass


# ============================================================================
# FILE MANAGER INTERFACE
# ============================================================================

class IFileManager(IFile, IFolder, IPath, IAtomicOperations, IBackupOperations, ITemporaryOperations):
    """
    File Manager interface for comprehensive file operations.
    
    This interface combines file, directory, path, atomic, backup, and temporary
    operations to provide a complete file management solution. It's designed
    to handle any file type (docx, json, photo, movie, etc.) with intelligent
    format detection and appropriate handling.
    
    Features:
    - Universal file type support (any format)
    - Intelligent format detection
    - Atomic file operations
    - Backup and restore capabilities
    - Temporary file management
    - Path validation and normalization
    - Directory operations
    - File metadata and permissions
    
    This interface is specifically designed for file management tasks where
    you need to handle various file types without knowing the specific format
    in advance.
    """
    pass

# ============================================================================
# DATA SOURCE INTERFACES (Used by file/, stream/)
# ============================================================================

class IDataSource[T](ABC):
    """Universal data source interface for various data sources."""
    
    @abstractmethod
    def read(self) -> T:
        """Read data from source."""
        pass
    
    @abstractmethod
    def write(self, data: T) -> None:
        """Write data to source."""
        pass


class IPagedDataSource[T](ABC):
    """Paged data source interface for large data sets."""
    
    @abstractmethod
    def read_page(self, page_number: int) -> list[T]:
        """Read a specific page of data."""
        pass
    
    @abstractmethod
    def get_page_count(self) -> int:
        """Get total number of pages."""
        pass


# ============================================================================
# CODEC-INTEGRATED IO INTERFACES (Used by stream/)
# ============================================================================

class ICodecIO[T, R](ABC):
    """Codec-integrated IO interface with source type T and result type R."""
    
    @abstractmethod
    def read_as(self, codec: str):
        """Read and decode data using specified codec."""
        pass
    
    @abstractmethod
    def write_as(self, data, codec: str) -> None:
        """Encode and write data using specified codec."""
        pass


class IPagedCodecIO[T, R](ABC):
    """Paged codec-integrated IO interface with source type T and result type R."""
    
    @abstractmethod
    def read_page_as(self, page_number: int, codec: str):
        """Read and decode a page using specified codec."""
        pass


# ============================================================================
# FILE SYSTEM INTERFACES (Used by common/, filesystem/)
# ============================================================================

class IFileWatcher(ABC):
    """Interface for watching file system changes."""
    
    @abstractmethod
    def watch(self, path: Union[str, Path]) -> None:
        """Start watching a path."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop watching."""
        pass


class IFileLock(ABC):
    """Interface for file locking."""
    
    @abstractmethod
    def acquire(self) -> bool:
        """Acquire the lock."""
        pass
    
    @abstractmethod
    def release(self) -> None:
        """Release the lock."""
        pass


class IFileSystem(ABC):
    """Virtual file system interface."""
    
    @abstractmethod
    def read(self, path: str) -> bytes:
        """Read file contents."""
        pass
    
    @abstractmethod
    def write(self, path: str, data: bytes) -> None:
        """Write file contents."""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        pass


# ============================================================================
# ARCHIVE INTERFACES - MOVED TO AFTER ICodec DEFINITION
# (See line ~1400 for IArchiver, IArchiveFile, ICompression)
# ============================================================================

# ============================================================================
# SUBFOLDER CONTRACTS (Consolidated)
# ============================================================================


# From archive/

@runtime_checkable
class IArchiveFormat(Protocol):
    """
    Interface for archive format handlers.
    
    Each format (ZIP, TAR, 7Z, RAR) implements this.
    """
    
    @property
    def format_id(self) -> str:
        """Unique format identifier."""
        ...
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        ...
    
    @property
    def mime_types(self) -> list[str]:
        """Supported MIME types."""
        ...
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """Create archive from files."""
        ...
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """Extract archive."""
        ...
    
    def list_contents(self, archive: Path) -> list[str]:
        """List archive contents."""
        ...
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """Add file to existing archive."""
        ...

@runtime_checkable
class ICompressor(Protocol):
    """
    Interface for compression algorithms.
    
    Each algorithm (gzip, bz2, lzma, zstd) implements this.
    """
    
    @property
    def algorithm_id(self) -> str:
        """Unique algorithm identifier."""
        ...
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        ...
    
    def compress(self, data: bytes, level: int = 6) -> bytes:
        """Compress bytes."""
        ...
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress bytes."""
        ...
    
    def can_handle(self, data: bytes) -> bool:
        """Check if this compressor can handle the data."""
        ...

@runtime_checkable
class IArchiveMetadata(Protocol):
    """
    Metadata protocol for self-describing archivers.
    
    Like ICodecMetadata for codecs!
    """
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        ...
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        ...
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        ...
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        ...


# From codec/

@runtime_checkable
class ICodec[T, R](Protocol):
    """
    Universal codec interface for bidirectional transformation.
    
    A codec transforms between a model (T) and its representation (R).
    This is the minimal contract that all codecs must implement.
    
    Type Parameters:
        T: Model type (e.g., dict, AST, dataclass)
        R: Representation type (bytes or str)
    
    Examples:
        JSON serializer:  ICodec[dict, bytes]
        SQL formatter:    ICodec[QueryAST, str]
        Pickle:           ICodec[Any, bytes]
        Python unparser:  ICodec[ast.AST, str]
    
    Design Principles:
        - Bidirectional by default (encode/decode)
        - Options-based configuration (not constructor pollution)
        - Representation-type specific (bytes OR str, not both)
        - Composable via adapters
    """
    
    def encode(self, value: T, *, options: Optional[EncodeOptions] = None) -> R:
        """
        Encode a model to its representation.
        
        Args:
            value: Model instance to encode
            options: Format-specific encoding options (e.g., {'pretty': True})
        
        Returns:
            Representation (bytes or str depending on codec type)
        
        Raises:
            EncodeError: If encoding fails
        
        Examples:
            >>> codec = JsonSerializer()
            >>> codec.encode({"key": "value"})
            b'{"key":"value"}'
            
            >>> formatter = SqlFormatter()
            >>> formatter.encode(select_ast, options={"pretty": True})
            'SELECT *\\nFROM users\\nWHERE id = 1'
        """
        ...
    
    def decode(self, repr: R, *, options: Optional[DecodeOptions] = None) -> T:
        """
        Decode a representation to a model.
        
        Args:
            repr: Representation to decode (bytes or str)
            options: Format-specific decoding options (e.g., {'strict': False})
        
        Returns:
            Model instance
        
        Raises:
            DecodeError: If decoding fails
        
        Examples:
            >>> codec = JsonSerializer()
            >>> codec.decode(b'{"key":"value"}')
            {'key': 'value'}
            
            >>> formatter = SqlFormatter()
            >>> formatter.decode('SELECT * FROM users')
            QueryAST(...)
        """
        ...

@runtime_checkable
class ICodecMetadata(Protocol):
    """
    Metadata protocol for codec discovery and registration.
    
    Codecs that implement this protocol can self-register and be
    discovered by the registry system with no hardcoding.
    
    Example:
        >>> class JsonCodec:
        ...     codec_id = "json"
        ...     media_types = ["application/json", "text/json"]
        ...     file_extensions = [".json", ".jsonl"]
        ...     aliases = ["JSON"]
        ...     
        ...     def capabilities(self):
        ...         return CodecCapability.BIDIRECTIONAL | CodecCapability.TEXT
    """
    
    @property
    def codec_id(self) -> str:
        """
        Unique codec identifier.
        
        Should be lowercase, alphanumeric + dash/underscore.
        
        Examples:
            - "json"
            - "sql"
            - "protobuf"
            - "python-ast"
        """
        ...
    
    @property
    def media_types(self) -> list[str]:
        """
        Supported media types / content types (RFC 2046).
        
        Used for content negotiation and HTTP Content-Type headers.
        
        Examples:
            - JSON: ["application/json", "text/json"]
            - SQL: ["application/sql", "text/x-sql"]
            - Protobuf: ["application/protobuf", "application/x-protobuf"]
        """
        ...
    
    @property
    def file_extensions(self) -> list[str]:
        """
        Supported file extensions (with leading dot).
        
        Used for auto-detection from file paths.
        
        Examples:
            - JSON: [".json", ".jsonl"]
            - SQL: [".sql", ".ddl", ".dml"]
            - Python: [".py", ".pyi"]
        """
        ...
    
    @property
    def aliases(self) -> list[str]:
        """
        Alternative names for this codec.
        
        Used for flexible lookup (case-insensitive matching).
        
        Examples:
            - JSON: ["json", "JSON"]
            - SQL: ["sql", "SQL", "structured-query"]
        """
        ...
    
    def capabilities(self) -> CodecCapability:
        """
        Get capabilities supported by this codec.
        
        Returns:
            Flag combination of supported features
        
        Example:
            >>> codec.capabilities()
            CodecCapability.BIDIRECTIONAL | CodecCapability.TEXT | CodecCapability.SCHEMA
        """
        ...


# From common/

@runtime_checkable
class IAtomicWriter(Protocol):
    """Interface for atomic file write operations."""
    
    def write(self, data: bytes) -> int:
        """Write data atomically."""
        ...
    
    def __enter__(self) -> 'IAtomicWriter':
        """Enter context manager."""
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        ...


# ============================================================================
# ARCHIVE INTERFACES (Dual Architecture: Codec + File)
# ============================================================================

class IArchiver[T](ICodec[T, bytes]):
    """
    Archive codec interface - operates in MEMORY on ANY data.
    
    Extends ICodec to provide dual API:
    - encode()/decode() - Low-level codec operations
    - compress()/extract() - User-friendly archive operations
    
    Type: ICodec[T, bytes] where T can be:
    - bytes (raw data)
    - str (text data)
    - dict/list (structured data)
    - Any (objects)
    
    NOT limited to file paths - works on data in RAM!
    """
    
    @abstractmethod
    def compress(self, data: T, **options) -> bytes:
        """
        Compress data to archive bytes (in RAM).
        
        Delegates to encode() internally.
        """
        pass
    
    @abstractmethod
    def extract(self, archive_bytes: bytes, **options) -> T:
        """
        Extract archive bytes to data (in RAM).
        
        Delegates to decode() internally.
        """
        pass


class IArchiveFile(IFile):
    """
    Archive FILE interface - operates on DISK.
    
    Extends IFile for file operations.
    USES IArchiver internally for compression (composition).
    
    This handles:
    - File I/O with archive files on disk
    - Adding/extracting files to/from archives
    - Archive file management
    """
    
    @abstractmethod
    def add_files(self, files: list[Path], **options) -> None:
        """Add files to archive (uses archiver.compress internally)."""
        pass
    
    @abstractmethod
    def extract_to(self, dest: Path, **options) -> list[Path]:
        """Extract archive to destination (uses archiver.extract internally)."""
        pass
    
    @abstractmethod
    def list_contents(self) -> list[str]:
        """List files in archive."""
        pass
    
    @abstractmethod
    def get_archiver(self) -> IArchiver:
        """Get the underlying archiver codec."""
        pass


class ICompression(ABC):
    """
    Interface for raw compression operations (gzip, bz2, lzma, etc.).
    
    This is for compressing RAW BYTES (not archives).
    Separate from IArchiver which handles archive formats.
    """
    
    @abstractmethod
    def compress(self, data: bytes, **options) -> bytes:
        """Compress raw bytes."""
        pass
    
    @abstractmethod
    def decompress(self, data: bytes, **options) -> bytes:
        """Decompress raw bytes."""
        pass


@runtime_checkable
class IPathValidator(Protocol):
    """Interface for path validation and security checks."""
    
    def validate_path(self, path: Union[str, Path]) -> bool:
        """Validate path safety."""
        ...
    
    def is_safe_path(self, path: Union[str, Path]) -> bool:
        """Check if path is safe to use."""
        ...
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize and resolve path."""
        ...



# From file/

@runtime_checkable
class IFileSource(Protocol):
    """Interface for file data sources."""
    
    @property
    def uri(self) -> str:
        """Source URI."""
        ...
    
    @property
    def scheme(self) -> str:
        """URI scheme."""
        ...
    
    def read(self, **options) -> Union[bytes, str]:
        """Read entire file content."""
        ...
    
    def write(self, data: Union[bytes, str], **options) -> None:
        """Write entire content to file."""
        ...
    
    def exists(self) -> bool:
        """Check if file exists."""
        ...
    
    def delete(self) -> None:
        """Delete file."""
        ...

@runtime_checkable
class IPagedSource(Protocol):
    """Interface for paged file sources."""
    
    @property
    def total_size(self) -> int:
        """Total file size in bytes."""
        ...
    
    def read_page(self, page: int, page_size: int, **options) -> Union[bytes, str]:
        """Read specific page."""
        ...
    
    def read_chunk(self, offset: int, size: int, **options) -> Union[bytes, str]:
        """Read chunk by byte offset."""
        ...
    
    def iter_pages(self, page_size: int, **options) -> Iterator[Union[bytes, str]]:
        """Iterate over pages."""
        ...
    
    def iter_chunks(self, chunk_size: int, **options) -> Iterator[Union[bytes, str]]:
        """Iterate over chunks."""
        ...

@runtime_checkable
class IPagingStrategy(Protocol):
    """
    Strategy interface for paging through file data.
    
    Enables pluggable paging algorithms:
    - BytePagingStrategy: Page by byte offsets
    - LinePagingStrategy: Page by line counts
    - RecordPagingStrategy: Page by record boundaries (CSV, JSONL)
    - SmartPagingStrategy: Adaptive paging based on content
    """
    
    @property
    def strategy_id(self) -> str:
        """Unique strategy identifier."""
        ...
    
    def read_page(
        self,
        file_path: Path,
        page: int,
        page_size: int,
        mode: str = 'rb',
        encoding: Optional[str] = None,
        **options
    ) -> Union[bytes, str]:
        """
        Read specific page using this strategy.
        
        Args:
            file_path: Path to file
            page: Page number (0-based)
            page_size: Items per page (interpretation depends on strategy)
            mode: File mode
            encoding: Text encoding (for text mode)
            **options: Strategy-specific options
        
        Returns:
            Page content
        """
        ...
    
    def iter_pages(
        self,
        file_path: Path,
        page_size: int,
        mode: str = 'rb',
        encoding: Optional[str] = None,
        **options
    ) -> Iterator[Union[bytes, str]]:
        """
        Iterate over pages using this strategy.
        
        Args:
            file_path: Path to file
            page_size: Items per page
            mode: File mode
            encoding: Text encoding
            **options: Strategy-specific options
        
        Yields:
            Page content
        """
        ...


# From filesystem/

@runtime_checkable
class IVirtualFS(Protocol):
    """Interface for virtual filesystem operations."""
    
    @property
    def scheme(self) -> str:
        """URI scheme."""
        ...
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        ...
    
    def is_file(self, path: str) -> bool:
        """Check if path is file."""
        ...


# From folder/

@runtime_checkable
class IFolderSource(Protocol):
    """Interface for folder operations."""
    
    def create(self, parents: bool = True, exist_ok: bool = True) -> bool:
        """Create directory."""
        ...
    
    def delete(self, recursive: bool = False) -> bool:
        """Delete directory."""
        ...
    
    def list_files(self, pattern: Optional[str] = None, recursive: bool = False) -> list[Path]:
        """List files in directory."""
        ...


# From manager/

@runtime_checkable
class IIOManager(Protocol):
    """Interface for I/O managers."""
    
    def open(self, **opts):
        """Open resource."""
        ...
    
    def close(self) -> None:
        """Close resource."""
        ...


# From stream/


class IPagedCodecIO[T, R](ICodecIO[T, R]):
    """
    Interface for paged codec I/O.
    """
    
    @abstractmethod
    def iter_items(self, page_size: int, **opts):
        """Iterate over decoded items."""
        ...
    
    @abstractmethod
    def load_page(self, page: int, page_size: int, **opts) -> list[T]:
        """Load specific page."""
        ...
