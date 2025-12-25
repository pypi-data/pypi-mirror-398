#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/paging/byte_paging.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Byte-based paging strategy.

Priority 1 (Security): Safe byte-level operations
Priority 2 (Usability): Simple byte paging
Priority 3 (Maintainability): Clean strategy implementation
Priority 4 (Performance): Efficient byte-level reads
Priority 5 (Extensibility): Pluggable via registry
"""

from pathlib import Path
from typing import Union, Optional, Iterator

from ...contracts import IPagingStrategy


class BytePagingStrategy:
    """
    Page by byte offsets - most efficient for binary files.
    
    Page size = number of bytes per page.
    
    Best for:
    - Binary files
    - Fixed-width records
    - Raw data streams
    """
    
    @property
    def strategy_id(self) -> str:
        """Unique strategy identifier."""
        return "byte"
    
    def read_page(
        self,
        file_path: Path,
        page: int,
        page_size: int,
        mode: str = 'rb',
        encoding: Optional[str] = None,
        **options
    ) -> Union[bytes, str]:
        """Read page by byte offset."""
        offset = page * page_size
        
        with open(file_path, mode, encoding=encoding) as f:
            f.seek(offset)
            return f.read(page_size)
    
    def iter_pages(
        self,
        file_path: Path,
        page_size: int,
        mode: str = 'rb',
        encoding: Optional[str] = None,
        **options
    ) -> Iterator[Union[bytes, str]]:
        """Iterate over pages by byte chunks."""
        page = 0
        while True:
            content = self.read_page(file_path, page, page_size, mode, encoding, **options)
            if not content:
                break
            yield content
            page += 1

