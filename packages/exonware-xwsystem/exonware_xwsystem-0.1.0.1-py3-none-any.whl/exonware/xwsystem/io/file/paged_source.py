#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/paged_source.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Paged file source with MODULAR paging system.

Uses pluggable paging strategies via registry!

Priority 1 (Security): Safe handling of large files
Priority 2 (Usability): Simple iteration API with auto-detection
Priority 3 (Maintainability): Clean separation - paging logic in strategies
Priority 4 (Performance): Memory-efficient chunk reading
Priority 5 (Extensibility): Add new strategies without changing this class!
"""

from pathlib import Path
from typing import Union, Optional, Iterator

from ..contracts import IPagedDataSource
from .source import FileDataSource
from ..contracts import IPagingStrategy

# Import auto-detection function
from .paging import auto_detect_paging_strategy


class PagedFileSource(FileDataSource, IPagedDataSource[Union[bytes, str]]):
    """
    Paged file source with PLUGGABLE paging strategies!
    
    NO hardcoded paging logic - uses strategy pattern!
    
    Examples:
        >>> # Auto-detect strategy
        >>> source = PagedFileSource("huge.sql")  # Binary → BytePagingStrategy
        >>> source = PagedFileSource("data.csv", mode='r')  # Text → LinePagingStrategy
        >>> 
        >>> # Custom strategy
        >>> from exonware.xwsystem.io.file.paging import RecordPagingStrategy
        >>> source = PagedFileSource("data.jsonl", paging_strategy=RecordPagingStrategy())
        >>> 
        >>> # Future: Your own strategy!
        >>> source = PagedFileSource("data.custom", paging_strategy=MyCustomStrategy())
    """
    
    def __init__(
        self,
        path: Union[str, Path],
        mode: str = 'rb',
        encoding: Optional[str] = None,
        validate_path: bool = True,
        paging_strategy: Optional[IPagingStrategy] = None
    ):
        """
        Initialize paged file source.
        
        Args:
            path: File path
            mode: File mode ('r' or 'rb')
            encoding: Text encoding (for text mode)
            validate_path: Whether to validate path safety
            paging_strategy: Custom paging strategy (None = auto-detect)
        """
        super().__init__(path, mode, encoding, validate_path)
        
        if 'w' in self._mode or 'a' in self._mode:
            raise ValueError("PagedFileSource only supports read modes")
        
        # Auto-detect or use provided strategy
        if paging_strategy is None:
            paging_strategy = auto_detect_paging_strategy(mode)
        
        self._paging_strategy = paging_strategy
    
    @property
    def total_size(self) -> int:
        """Total file size in bytes."""
        if not self.exists():
            return -1
        return self._path.stat().st_size
    
    def read_page(self, page: int, page_size: int, **options) -> Union[bytes, str]:
        """
        Read specific page using the paging strategy.
        
        The strategy determines HOW to page (byte/line/record).
        """
        return self._paging_strategy.read_page(
            self._path,
            page,
            page_size,
            self._mode,
            self._encoding,
            **options
        )
    
    def iter_pages(self, page_size: int, **options) -> Iterator[Union[bytes, str]]:
        """
        Iterate over pages using the paging strategy.
        """
        return self._paging_strategy.iter_pages(
            self._path,
            page_size,
            self._mode,
            self._encoding,
            **options
        )
    
    def read_chunk(self, offset: int, size: int, **options) -> Union[bytes, str]:
        """
        Read chunk by byte offset (always byte-based).
        
        Args:
            offset: Byte offset to start reading
            size: Number of bytes to read
            **options: Read options
        
        Returns:
            Chunk content
        """
        try:
            if 'b' in self._mode:
                with open(self._path, 'rb') as f:
                    f.seek(offset)
                    return f.read(size)
            else:
                encoding = options.get('encoding', self._encoding or 'utf-8')
                with open(self._path, 'r', encoding=encoding) as f:
                    f.seek(offset)
                    return f.read(size)
        except Exception as e:
            raise IOError(f"Failed to read chunk from {self._path}: {e}")
    
    def iter_chunks(self, chunk_size: int, **options) -> Iterator[Union[bytes, str]]:
        """
        Iterate over chunks by byte size.
        
        Always uses byte-based chunking regardless of paging strategy.
        """
        offset = 0
        total_size = self.total_size
        
        if total_size < 0:
            raise IOError(f"Cannot iterate chunks: file {self._path} doesn't exist")
        
        while offset < total_size:
            chunk = self.read_chunk(offset, chunk_size, **options)
            if not chunk:
                break
            yield chunk
            offset += len(chunk) if isinstance(chunk, (bytes, str)) else chunk_size
    
    def get_page_count(self, page_size: int = 1024) -> int:
        """Get total number of pages."""
        total_size = self.total_size
        if total_size < 0:
            return 0
        return (total_size + page_size - 1) // page_size  # Ceiling division