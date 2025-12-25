#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/paging/record_paging.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Record-based paging strategy for structured formats.

Priority 1 (Security): Safe record parsing
Priority 2 (Usability): Smart record detection
Priority 3 (Maintainability): Clean strategy implementation
Priority 4 (Performance): Efficient record-level reads
Priority 5 (Extensibility): Pluggable via registry
"""

from pathlib import Path
from typing import Union, Optional, Iterator

from ...contracts import IPagingStrategy


class RecordPagingStrategy:
    """
    Page by record boundaries - smart for structured formats.
    
    Page size = number of records per page.
    
    Best for:
    - CSV files (records = rows)
    - JSONL files (records = JSON objects per line)
    - SQL dumps (records = statements)
    - Log files with structured entries
    
    Future enhancement: Auto-detect record delimiter from content.
    """
    
    def __init__(self, delimiter: str = '\n'):
        """
        Initialize record paging strategy.
        
        Args:
            delimiter: Record delimiter (default: newline)
        """
        self.delimiter = delimiter
    
    @property
    def strategy_id(self) -> str:
        """Unique strategy identifier."""
        return "record"
    
    def read_page(
        self,
        file_path: Path,
        page: int,
        page_size: int,
        mode: str = 'r',
        encoding: Optional[str] = None,
        **options
    ) -> str:
        """Read page by record count."""
        # For now, use line-based (newline delimiter)
        # Future: Support custom delimiters
        skip_records = page * page_size
        encoding = encoding or 'utf-8'
        
        with open(file_path, mode, encoding=encoding) as f:
            # Skip to start of page
            for _ in range(skip_records):
                if not f.readline():
                    return ""  # EOF
            
            # Read page_size records
            records = []
            for _ in range(page_size):
                record = f.readline()
                if not record:
                    break
                records.append(record)
            
            return "".join(records)
    
    def iter_pages(
        self,
        file_path: Path,
        page_size: int,
        mode: str = 'r',
        encoding: Optional[str] = None,
        **options
    ) -> Iterator[str]:
        """Iterate over pages by record chunks."""
        page = 0
        while True:
            content = self.read_page(file_path, page, page_size, mode, encoding, **options)
            if not content:
                break
            yield content
            page += 1

