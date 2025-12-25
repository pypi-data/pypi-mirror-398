#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/source.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

File-based data source implementation.

Priority 1 (Security): Safe path validation, atomic writes
Priority 2 (Usability): Simple file read/write API
Priority 3 (Maintainability): Clean, focused data source
Priority 4 (Performance): Efficient file operations
Priority 5 (Extensibility): Foundation for other data sources (HTTP, S3, etc.)
"""

from pathlib import Path
from typing import Union, Optional, Any

from ..contracts import IDataSource


class FileDataSource(IDataSource[Union[bytes, str]]):
    """
    File-based data source implementation.
    
    Wraps a file path as a universal data source, supporting both
    text and binary modes. Integrates with common/atomic.py
    and common/path_manager.py for safety.
    
    Examples:
        >>> # Binary mode
        >>> source = FileDataSource("data.bin", mode='rb')
        >>> data = source.read()
        >>> isinstance(data, bytes)
        True
        
        >>> # Text mode
        >>> source = FileDataSource("config.txt", mode='r', encoding='utf-8')
        >>> text = source.read()
        >>> isinstance(text, str)
        True
    """
    
    def __init__(
        self,
        path: Union[str, Path],
        mode: str = 'rb',
        encoding: Optional[str] = None,
        validate_path: bool = True
    ):
        """
        Initialize file data source.
        
        Args:
            path: File path
            mode: File mode ('r', 'rb', 'w', 'wb', etc.)
            encoding: Text encoding (for text mode)
            validate_path: Whether to validate path safety
        """
        self._path = Path(path)
        self._mode = mode
        self._encoding = encoding
        self._validate_path = validate_path
        
        if validate_path:
            # Use PathValidator for validation if available
            try:
                from ...security.path_validator import PathValidator
                # Don't check existence during initialization - file may be created later
                pv = PathValidator(check_existence=False)
                # For write modes, allow creating the file (path doesn't exist yet)
                for_writing = mode and ('w' in mode or 'a' in mode or '+' in mode)
                pv.validate_path(str(self._path), for_writing=for_writing, create_dirs=True)
            except ImportError:
                pass
    
    @property
    def uri(self) -> str:
        """Return file:// URI."""
        return f"file://{self._path.absolute()}"
    
    @property
    def scheme(self) -> str:
        """Return scheme identifier."""
        return "file"
    
    def read(self, **options) -> Union[bytes, str]:
        """
        Read entire file content.
        
        Args:
            **options: Read options (encoding for text mode)
        
        Returns:
            File content as bytes or str (depending on mode)
        
        Raises:
            IOError: If read operation fails
        """
        try:
            if 'b' in self._mode:
                return self._path.read_bytes()
            else:
                encoding = options.get('encoding', self._encoding or 'utf-8')
                return self._path.read_text(encoding=encoding)
        except Exception as e:
            raise IOError(f"Failed to read {self._path}: {e}")
    
    def write(self, data: Union[bytes, str], **options) -> None:
        """
        Write entire content to file.
        
        Args:
            data: Data to write (bytes or str)
            **options: Write options
                - atomic: Use atomic write (default: True)
                - backup: Create backup before write (default: True)
                - encoding: Text encoding (for str data)
        
        Raises:
            IOError: If write operation fails
        """
        try:
            atomic = options.get('atomic', True)
            backup = options.get('backup', True)
            
            # Ensure parent directory exists
            self._path.parent.mkdir(parents=True, exist_ok=True)
            
            if atomic:
                # Use AtomicFileWriter from common
                from ..common.atomic import AtomicFileWriter
                # Determine mode based on data type and stored mode
                if isinstance(data, bytes):
                    # Binary mode
                    atomic_mode = 'wb'
                    encoding = None
                else:
                    # Text mode
                    atomic_mode = 'w'
                    encoding = options.get('encoding', self._encoding or 'utf-8')
                
                with AtomicFileWriter(self._path, mode=atomic_mode, encoding=encoding, backup=backup) as writer:
                    if isinstance(data, str):
                        writer.write(data)
                    else:
                        writer.write(data)
            else:
                # Direct write
                if isinstance(data, bytes):
                    self._path.write_bytes(data)
                else:
                    encoding = options.get('encoding', self._encoding or 'utf-8')
                    self._path.write_text(data, encoding=encoding)
        except Exception as e:
            raise IOError(f"Failed to write {self._path}: {e}")
    
    def exists(self) -> bool:
        """Check if file exists."""
        return self._path.exists() and self._path.is_file()
    
    def delete(self) -> None:
        """
        Delete file.
        
        Raises:
            IOError: If delete operation fails
        """
        try:
            if self._path.exists():
                self._path.unlink()
        except Exception as e:
            raise IOError(f"Failed to delete {self._path}: {e}")
    
    def metadata(self) -> dict[str, Any]:
        """
        Get file metadata.
        
        Returns:
            Dictionary with metadata (size, modified time, etc.)
        """
        if not self.exists():
            return {
                'exists': False,
                'path': str(self._path),
                'uri': self.uri
            }
        
        try:
            stat = self._path.stat()
            return {
                'exists': True,
                'path': str(self._path),
                'uri': self.uri,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'accessed': stat.st_atime,
                'mode': self._mode,
                'encoding': self._encoding,
                'is_file': self._path.is_file(),
                'is_symlink': self._path.is_symlink(),
            }
        except Exception as e:
            return {
                'exists': True,
                'path': str(self._path),
                'uri': self.uri,
                'error': str(e)
            }

