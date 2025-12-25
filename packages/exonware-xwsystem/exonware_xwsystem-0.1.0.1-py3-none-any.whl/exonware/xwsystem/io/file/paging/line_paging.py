#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/paging/line_paging.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Line-based paging strategy.

Priority 1 (Security): Safe line-level operations
Priority 2 (Usability): Simple line paging
Priority 3 (Maintainability): Clean strategy implementation
Priority 4 (Performance): Efficient line-level reads
Priority 5 (Extensibility): Pluggable via registry
"""

from pathlib import Path
from typing import Union, Optional, Iterator

from ...contracts import IPagingStrategy


class LinePagingStrategy:
    """
    Page by line counts - best for text files.
    
    Page size = number of lines per page.
    
    Best for:
    - Text files
    - Log files
    - Line-oriented formats
    """
    
    @property
    def strategy_id(self) -> str:
        """Unique strategy identifier."""
        return "line"
    
    def read_page(
        self,
        file_path: Path,
        page: int,
        page_size: int,
        mode: str = 'r',
        encoding: Optional[str] = None,
        **options
    ) -> str:
        """Read page by line count."""
        skip_lines = page * page_size
        encoding = encoding or 'utf-8'
        
        with open(file_path, mode, encoding=encoding) as f:
            # Skip to start of page
            for _ in range(skip_lines):
                if not f.readline():
                    return ""  # EOF
            
            # Read page_size lines
            lines = []
            for _ in range(page_size):
                line = f.readline()
                if not line:
                    break
                lines.append(line)
            
            return "".join(lines)
    
    def iter_pages(
        self,
        file_path: Path,
        page_size: int,
        mode: str = 'r',
        encoding: Optional[str] = None,
        **options
    ) -> Iterator[str]:
        """Iterate over pages by line chunks."""
        page = 0
        while True:
            content = self.read_page(file_path, page, page_size, mode, encoding, **options)
            if not content:
                break
            yield content
            page += 1

