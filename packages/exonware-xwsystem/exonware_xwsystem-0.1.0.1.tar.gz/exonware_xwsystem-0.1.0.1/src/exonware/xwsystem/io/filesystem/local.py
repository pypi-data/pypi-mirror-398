#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/filesystem/local.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Local filesystem implementation.

Priority 1 (Security): Safe local file operations
Priority 2 (Usability): Simple, consistent API
Priority 3 (Maintainability): Clean filesystem abstraction
Priority 4 (Performance): Efficient local file access
Priority 5 (Extensibility): Foundation for other FS (S3, FTP, etc.)
"""

from pathlib import Path
from typing import Union, Optional, Any

from ..contracts import IFileSystem


class LocalFileSystem(IFileSystem):
    """
    Local filesystem implementation.
    
    Implements IFileSystem for local disk access. Foundation for future
    virtual FS implementations (S3FileSystem, ZipFileSystem, etc.).
    
    Examples:
        >>> fs = LocalFileSystem()
        >>> fs.write_text("/path/file.txt", "content")
        >>> content = fs.read_text("/path/file.txt")
        >>> 
        >>> # Same API will work for future backends:
        >>> fs = S3FileSystem("my-bucket")  # Future
        >>> fs.write_text("file.txt", "content")  # Saves to S3!
    """
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        Initialize local filesystem.
        
        Args:
            base_path: Optional base path for all operations
        """
        self._base_path = Path(base_path) if base_path else None
    
    @property
    def scheme(self) -> str:
        """URI scheme for this filesystem."""
        return "file"
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path with base path if set."""
        p = Path(path)
        if self._base_path:
            if p.is_absolute():
                # Make relative to base_path
                try:
                    p = p.relative_to(self._base_path)
                except ValueError:
                    pass
            return self._base_path / p
        return p
    
    def open(self, path: str, mode: str = 'r') -> Any:
        """Open file in this filesystem."""
        resolved = self._resolve_path(path)
        return open(resolved, mode)
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        return self._resolve_path(path).exists()
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        p = self._resolve_path(path)
        return p.exists() and p.is_file()
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory."""
        p = self._resolve_path(path)
        return p.exists() and p.is_dir()
    
    def listdir(self, path: str) -> list[str]:
        """List directory contents."""
        p = self._resolve_path(path)
        if not p.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")
        return [item.name for item in p.iterdir()]
    
    def mkdir(self, path: str, parents: bool = True) -> None:
        """Create directory."""
        self._resolve_path(path).mkdir(parents=parents, exist_ok=True)
    
    def remove(self, path: str) -> None:
        """Remove file or directory."""
        p = self._resolve_path(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            import shutil
            shutil.rmtree(p)
    
    def copy(self, src: str, dst: str) -> None:
        """Copy file or directory."""
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        
        if src_path.is_file():
            import shutil
            shutil.copy2(src_path, dst_path)
        elif src_path.is_dir():
            import shutil
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
    
    def move(self, src: str, dst: str) -> None:
        """Move file or directory."""
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        import shutil
        shutil.move(str(src_path), str(dst_path))
    
    # Convenience methods
    def read_text(self, path: str, encoding: str = 'utf-8') -> str:
        """Read file as text."""
        return self._resolve_path(path).read_text(encoding=encoding)
    
    def read_bytes(self, path: str) -> bytes:
        """Read file as bytes."""
        return self._resolve_path(path).read_bytes()
    
    def write_text(self, path: str, content: str, encoding: str = 'utf-8') -> None:
        """Write text to file."""
        p = self._resolve_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)
    
    def write_bytes(self, path: str, content: bytes) -> None:
        """Write bytes to file."""
        p = self._resolve_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    
    def read(self, path: str) -> bytes:
        """Read file contents."""
        return self.read_bytes(path)
    
    def write(self, path: str, content: bytes) -> None:
        """Write file contents."""
        self.write_bytes(path, content)

