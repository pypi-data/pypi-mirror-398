#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Base classes for file operations.

Like codec/base.py: contains abstract bases + utilities.

Priority 1 (Security): Safe base implementations
Priority 2 (Usability): Easy to extend
Priority 3 (Maintainability): Clean abstractions
Priority 4 (Performance): Efficient operations
Priority 5 (Extensibility): Ready for new file types
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Optional, Any

from ..contracts import IFileSource, IPagedSource, IPagingStrategy
from ..defs import PagingMode

__all__ = [
    'AFileSource',
    'APagedSource',
]


class AFileSource(IFileSource, ABC):
    """
    Abstract base for file data sources.
    
    Provides common file source functionality.
    """
    
    def __init__(self, path: Union[str, Path], mode: str = 'rb', encoding: Optional[str] = None):
        """Initialize file source."""
        self._path = Path(path)
        self._mode = mode
        self._encoding = encoding
    
    @property
    def uri(self) -> str:
        """Return file:// URI."""
        return f"file://{self._path.absolute()}"
    
    @property
    def scheme(self) -> str:
        """Return scheme identifier."""
        return "file"
    
    def exists(self) -> bool:
        """Check if file exists."""
        return self._path.exists() and self._path.is_file()
    
    def delete(self) -> None:
        """Delete file."""
        if self._path.exists():
            self._path.unlink()
    
    @abstractmethod
    def read(self, **options) -> Union[bytes, str]:
        """Read entire file content."""
        pass
    
    @abstractmethod
    def write(self, data: Union[bytes, str], **options) -> None:
        """Write entire content to file."""
        pass


class APagedSource(IPagedSource, ABC):
    """
    Abstract base for paged file sources.
    
    Provides common paged reading functionality.
    Uses pluggable paging strategies!
    """
    
    def __init__(
        self,
        path: Union[str, Path],
        mode: str = 'rb',
        encoding: Optional[str] = None,
        paging_strategy: Optional[IPagingStrategy] = None
    ):
        """
        Initialize paged source.
        
        Args:
            path: File path
            mode: File mode
            encoding: Text encoding
            paging_strategy: Custom paging strategy (None = auto-detect)
        """
        self._path = Path(path)
        self._mode = mode
        self._encoding = encoding
        
        # Auto-detect strategy if not provided
        if paging_strategy is None:
            from .paging import auto_detect_paging_strategy
            paging_strategy = auto_detect_paging_strategy(mode)
        
        self._paging_strategy = paging_strategy
    
    @property
    def total_size(self) -> int:
        """Total file size in bytes."""
        if not self._path.exists():
            return -1
        return self._path.stat().st_size
    
    def read_page(self, page: int, page_size: int, **options) -> Union[bytes, str]:
        """Read specific page using strategy."""
        return self._paging_strategy.read_page(
            self._path,
            page,
            page_size,
            self._mode,
            self._encoding,
            **options
        )
    
    def iter_pages(self, page_size: int, **options):
        """Iterate over pages using strategy."""
        return self._paging_strategy.iter_pages(
            self._path,
            page_size,
            self._mode,
            self._encoding,
            **options
        )
    
    @abstractmethod
    def read_chunk(self, offset: int, size: int, **options) -> Union[bytes, str]:
        """Read chunk by byte offset."""
        pass
    
    @abstractmethod
    def iter_chunks(self, chunk_size: int, **options):
        """Iterate over chunks."""
        pass

