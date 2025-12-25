#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/common/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Common utilities shared across IO operations.

Following codec/ pattern:
- contracts.py: Interfaces
- defs.py: Enums
- base.py: Abstract classes
- errors.py: Exceptions
- [concrete files]: Implementations

Priority 1 (Security): Safe atomic operations, path validation
Priority 2 (Usability): Simple, reusable utilities
Priority 3 (Maintainability): Centralized common code
Priority 4 (Performance): Efficient helper functions
Priority 5 (Extensibility): Easy to add new utilities
"""

# Core abstractions
from ..contracts import (
    IAtomicWriter,
    IPathValidator,
    IFileWatcher,
    IFileLock,
)

from ..defs import (
    AtomicMode,
    WatcherEvent,
    LockMode,
    PathSecurityLevel,
)

from .base import (
    AAtomicWriter,
    APathValidator,
    AFileWatcher,
    AFileLock,
)

from ..errors import (
    CommonIOError,
    AtomicOperationError,
    PathValidationError,
    WatcherError,
    LockError,
    LockTimeoutError,
)

# Concrete implementations
from .atomic import (
    AtomicFileWriter,
    FileOperationError,
    safe_read_bytes,
    safe_read_text,
    safe_read_with_fallback,
    safe_write_bytes,
    safe_write_text,
)

from .path_manager import PathManager
from .watcher import FileWatcher
from .lock import FileLock


__all__ = [
    # Contracts
    "IAtomicWriter",
    "IPathValidator",
    "IFileWatcher",
    "IFileLock",
    
    # Definitions
    "AtomicMode",
    "WatcherEvent",
    "LockMode",
    "PathSecurityLevel",
    
    # Abstract bases
    "AAtomicWriter",
    "APathValidator",
    "AFileWatcher",
    "AFileLock",
    
    # Errors
    "CommonIOError",
    "AtomicOperationError",
    "PathValidationError",
    "WatcherError",
    "LockError",
    "LockTimeoutError",
    
    # Concrete implementations
    "AtomicFileWriter",
    "FileOperationError",
    "safe_read_bytes",
    "safe_read_text",
    "safe_read_with_fallback",
    "safe_write_bytes",
    "safe_write_text",
    "PathManager",
    "FileWatcher",
    "FileLock",
]
