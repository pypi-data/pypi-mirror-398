#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

File-specific implementations and utilities.

Following codec/ pattern with MODULAR PAGING SYSTEM!

Priority 1 (Security): Safe file operations with validation
Priority 2 (Usability): Simple file API + auto-detection
Priority 3 (Maintainability): Focused file-specific code
Priority 4 (Performance): Efficient file I/O + pluggable strategies
Priority 5 (Extensibility): Easy to add new file features & paging strategies
"""

# Contracts
from ..contracts import (
    IFileSource,
    IPagedSource,
    IPagingStrategy,
)

# Definitions
from ..defs import (
    PagingMode,
    FileEncoding,
)

# Base classes
from .base import (
    AFileSource,
    APagedSource,
)

# Errors
from ..errors import (
    FileError,
    FileSourceError,
    PagedSourceError,
    PagingStrategyError,
)

# Paging system (modular!)
from .paging import (
    # Strategies
    BytePagingStrategy,
    LinePagingStrategy,
    RecordPagingStrategy,
    
    # Registry
    PagingStrategyRegistry,
    get_global_paging_registry,
    register_paging_strategy,
    get_paging_strategy,
    auto_detect_paging_strategy,
)

# Concrete implementations
from .source import FileDataSource
from .paged_source import PagedFileSource
from .file import XWFile

# Format conversion
from .conversion import FormatConverter, convert_file

__all__ = [
    # Contracts
    "IFileSource",
    "IPagedSource",
    "IPagingStrategy",
    
    # Definitions
    "PagingMode",
    "FileEncoding",
    
    # Base classes
    "AFileSource",
    "APagedSource",
    
    # Errors
    "FileError",
    "FileSourceError",
    "PagedSourceError",
    "PagingStrategyError",
    
    # Paging strategies
    "BytePagingStrategy",
    "LinePagingStrategy",
    "RecordPagingStrategy",
    
    # Paging registry
    "PagingStrategyRegistry",
    "get_global_paging_registry",
    "register_paging_strategy",
    "get_paging_strategy",
    "auto_detect_paging_strategy",
    
    # Concrete implementations
    "FileDataSource",
    "PagedFileSource",
    "XWFile",
    
    # Format conversion
    "FormatConverter",
    "convert_file",
]
