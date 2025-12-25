"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

XWFile - Concrete implementation of file operations.
"""

import os
from pathlib import Path
from typing import Any, Optional, Union, BinaryIO, TextIO

from ..base import AFile
from ..contracts import FileMode, OperationResult, IFile
from ..common.atomic import AtomicFileWriter
from ...config.logging_setup import get_logger
from ...security.path_validator import PathValidator
from ...validation.data_validator import DataValidator
from ...monitoring.performance_monitor import performance_monitor

logger = get_logger(__name__)

# Import format conversion utilities
from .conversion import FormatConverter


class XWFile(AFile):
    """
    Concrete implementation of file operations with both static and instance methods.
    
    This class provides a complete, production-ready implementation of file
    operations with xwsystem integration for security, validation, and monitoring.
    
    Features:
    - File I/O operations (read, write, save, load)
    - File metadata operations (size, permissions, timestamps)
    - File validation and safety checks
    - Static utility methods for file operations
    - xwsystem integration (security, validation, monitoring)
    """
    
    def __init__(self, file_path: Union[str, Path], **config):
        """
        Initialize XWFile with xwsystem integration.
        
        Args:
            file_path: Path to file
            **config: Configuration options for file operations
        """
        super().__init__(file_path)
        
        # Initialize xwsystem utilities
        self._path_validator = PathValidator()
        self._data_validator = DataValidator()
        
        # Configuration
        self.validate_paths = config.get('validate_paths', True)
        self.validate_data = config.get('validate_data', True)
        self.enable_monitoring = config.get('enable_monitoring', True)
        self.use_atomic_operations = config.get('use_atomic_operations', True)
        self.auto_create_dirs = config.get('auto_create_dirs', True)
        self.auto_backup = config.get('auto_backup', True)
        
        logger.debug(f"XWFile initialized for path: {file_path}")
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    def open(self, mode: FileMode = FileMode.READ) -> None:
        """Open file with validation and monitoring."""
        if self.validate_paths:
            for_writing = mode in [FileMode.WRITE, FileMode.APPEND, FileMode.WRITE_READ, FileMode.BINARY_WRITE, FileMode.BINARY_APPEND, FileMode.BINARY_WRITE_READ]
            self._path_validator.validate_path(self.file_path, for_writing=for_writing, create_dirs=self.auto_create_dirs)
        
        with performance_monitor("file_open"):
            # Ensure parent directory exists
            if self.auto_create_dirs and mode in [FileMode.WRITE, FileMode.APPEND, FileMode.WRITE_READ]:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Open file
            self._handle = open(self.file_path, mode.value)
            logger.debug(f"File opened: {self.file_path} in mode {mode.value}")
    
    def read(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Read from file with validation."""
        if not self._handle:
            raise ValueError("File not open")
        
        with performance_monitor("file_read"):
            data = self._handle.read(size)
            
            if self.validate_data and isinstance(data, (str, bytes)):
                self._data_validator.validate_data(data)
            
            return data
    
    def write(self, data: Union[str, bytes]) -> int:
        """Write to file with validation."""
        if not self._handle:
            raise ValueError("File not open")
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("file_write"):
            return self._handle.write(data)
    
    def save(self, data: Any, **kwargs) -> bool:
        """Save data to file with atomic operations."""
        if self.validate_paths:
            self._path_validator.validate_path(self.file_path, for_writing=True, create_dirs=True)
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("file_save"):
            try:
                if self.use_atomic_operations:
                    # Use atomic file writer
                    mode = 'wb' if isinstance(data, bytes) else 'w'
                    with AtomicFileWriter(self.file_path, mode=mode, backup=self.auto_backup) as writer:
                        if isinstance(data, str):
                            writer.write(data)
                        else:
                            writer.write(data)
                else:
                    # Direct write
                    self.file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.file_path, 'wb' if isinstance(data, bytes) else 'w') as f:
                        f.write(data)
                
                return True
            except Exception as e:
                logger.error(f"Save failed for {self.file_path}: {e}")
                return False
    
    def load(self, **kwargs) -> Any:
        """Load data from file with validation."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.validate_paths:
            self._path_validator.validate_path(self.file_path)
        
        with performance_monitor("file_load"):
            try:
                # Try to read as text first, then binary
                try:
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        data = f.read()
                except UnicodeDecodeError:
                    with open(self.file_path, 'rb') as f:
                        data = f.read()
                
                if self.validate_data:
                    self._data_validator.validate_data(data)
                
                return data
            except Exception as e:
                logger.error(f"Load failed for {self.file_path}: {e}")
                raise
    
    def save_as(self, path: Union[str, Path], data: Any, **kwargs) -> bool:
        """Save data to specific path."""
        target_path = Path(path)
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("file_save_as"):
            try:
                if self.use_atomic_operations:
                    # Use atomic file writer
                    with AtomicFileWriter(target_path, backup=self.auto_backup) as writer:
                        if isinstance(data, str):
                            writer.write(data.encode('utf-8'))
                        else:
                            writer.write(data)
                else:
                    # Direct write
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, 'wb' if isinstance(data, bytes) else 'w') as f:
                        f.write(data)
                
                return True
            except Exception as e:
                logger.error(f"Save as failed for {target_path}: {e}")
                return False
    
    def to_file(self, path: Union[str, Path], **kwargs) -> bool:
        """Write current object to file."""
        # This would depend on the specific object being saved
        # For now, we'll use the file path as the data
        return self.save_as(path, str(self.file_path), **kwargs)
    
    def from_file(self, path: Union[str, Path], **kwargs) -> 'File':
        """Load object from file."""
        # Create new XWFile instance for the given path
        new_file = XWFile(path, **kwargs)
        new_file.load(**kwargs)
        return new_file
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_info(self) -> dict[str, Any]:
        """Get comprehensive file information."""
        return {
            'file_path': str(self.file_path),
            'exists': self.file_path.exists(),
            'size': self.size(self.file_path) if self.file_path.exists() else 0,
            'is_readable': self.is_readable(self.file_path) if self.file_path.exists() else False,
            'is_writable': self.is_writable(self.file_path) if self.file_path.exists() else False,
            'is_executable': self.is_executable(self.file_path) if self.file_path.exists() else False,
            'modified_time': self.get_modified_time(self.file_path) if self.file_path.exists() else 0.0,
            'created_time': self.get_created_time(self.file_path) if self.file_path.exists() else 0.0,
            'permissions': self.get_permissions(self.file_path) if self.file_path.exists() else 0,
            'validate_paths': self.validate_paths,
            'validate_data': self.validate_data,
            'enable_monitoring': self.enable_monitoring,
            'use_atomic_operations': self.use_atomic_operations,
            'auto_create_dirs': self.auto_create_dirs,
            'auto_backup': self.auto_backup
        }
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close()
    
    # ============================================================================
    # FORMAT CONVERSION METHODS
    # ============================================================================
    
    @staticmethod
    def convert(
        source_path: Union[str, Path],
        target_path: Union[str, Path],
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        **options
    ) -> None:
        """
        Convert file from one format to another (static version).
        
        Works for compatible formats in the same category:
        - ARCHIVE: zip ↔ 7z ↔ tar ↔ zst ✓
        - SERIALIZATION: json ↔ yaml ↔ xml ↔ toml ✓
        - ARCHIVE ↔ SERIALIZATION: ✗ (incompatible categories)
        
        Args:
            source_path: Source file path
            target_path: Target file path
            source_format: Source format ID (auto-detected from extension if None)
            target_format: Target format ID (auto-detected from extension if None)
            **options: Format-specific conversion options
        
        Examples:
            >>> # Archive conversion (both ARCHIVE category)
            >>> XWFile.convert("backup.zip", "backup.tar")
            >>> 
            >>> # Explicit format specification
            >>> XWFile.convert(
            ...     "backup.zip",
            ...     "backup.tar",
            ...     source_format="zip",
            ...     target_format="tar"
            ... )
        """
        converter = FormatConverter()
        converter.convert_file(
            Path(source_path),
            Path(target_path),
            source_format,
            target_format,
            **options
        )
    
    def save_as(
        self,
        target_path: Union[str, Path],
        target_format: Optional[str] = None,
        **options
    ) -> None:
        """
        Save file in a different format (instance method).
        
        Uses convert() internally: reads current file, converts format, saves to new path.
        
        Args:
            target_path: Target file path
            target_format: Target format ID (auto-detected from extension if None)
            **options: Format-specific conversion options
        
        Examples:
            >>> file = XWFile("backup.zip")
            >>> 
            >>> # Convert to TAR (auto-detected from extension)
            >>> file.save_as("backup.tar")
            >>> 
            >>> # Explicit format
            >>> file.save_as("backup.tar", target_format="tar")
        """
        XWFile.convert(
            self.file_path,
            target_path,
            target_format=target_format,
            **options
        )
