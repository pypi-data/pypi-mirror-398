#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/filesystem/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Virtual filesystem abstractions.

Following codec/ pattern.

Priority 1 (Security): Safe filesystem operations
Priority 2 (Usability): Uniform API across backends
Priority 3 (Maintainability): Clean filesystem abstraction
Priority 4 (Performance): Efficient operations
Priority 5 (Extensibility): Ready for S3, ZIP, FTP filesystems
"""

from ..contracts import IVirtualFS
from ..defs import FSScheme
from .base import AFileSystem
from ..errors import FileSystemError
from .local import LocalFileSystem

__all__ = [
    # Contracts
    "IVirtualFS",
    
    # Definitions
    "FSScheme",
    
    # Base classes
    "AFileSystem",
    
    # Errors
    "FileSystemError",
    
    # Concrete implementations
    "LocalFileSystem",
]
