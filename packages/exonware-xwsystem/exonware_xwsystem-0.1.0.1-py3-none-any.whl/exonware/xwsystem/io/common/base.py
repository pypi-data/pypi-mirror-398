#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/common/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Base classes and utilities for common IO operations.

Like codec/base.py, this contains:
- Abstract base classes (AAtomicWriter, APathValidator, etc.)
- Utilities and helper functions
- Registries (if needed in future)

Priority 1 (Security): Safe base implementations
Priority 2 (Usability): Easy to extend
Priority 3 (Maintainability): Clean abstractions
Priority 4 (Performance): Efficient operations
Priority 5 (Extensibility): Ready for new utilities
"""

from abc import ABC, abstractmethod
from typing import Optional, Union, Callable
from pathlib import Path

from ..contracts import IAtomicWriter, IPathValidator, IFileWatcher, IFileLock
from ..defs import AtomicMode, WatcherEvent, LockMode, PathSecurityLevel

__all__ = [
    'AAtomicWriter',
    'APathValidator',
    'AFileWatcher',
    'AFileLock',
]


class AAtomicWriter(IAtomicWriter, ABC):
    """
    Abstract base for atomic file writers.
    
    Provides skeletal implementation for atomic write operations.
    """
    
    def __init__(self, path: Union[str, Path], mode: AtomicMode = AtomicMode.WRITE_BACKUP):
        """Initialize atomic writer."""
        self.path = Path(path)
        self.mode = mode
        self._temp_path: Optional[Path] = None
        self._backup_path: Optional[Path] = None
    
    @abstractmethod
    def write(self, data: bytes) -> int:
        """Write data atomically."""
        pass
    
    def __enter__(self) -> 'AAtomicWriter':
        """Enter context manager."""
        return self
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        pass


class APathValidator(IPathValidator, ABC):
    """
    Abstract base for path validators.
    
    Provides common validation logic.
    """
    
    def __init__(self, security_level: PathSecurityLevel = PathSecurityLevel.STRICT):
        """Initialize path validator."""
        self.security_level = security_level
    
    @abstractmethod
    def validate_path(self, path: Union[str, Path]) -> bool:
        """Validate path safety."""
        pass
    
    def is_safe_path(self, path: Union[str, Path]) -> bool:
        """Check if path is safe to use."""
        try:
            return self.validate_path(path)
        except Exception:
            return False
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize and resolve path."""
        return Path(path).resolve()


class AFileWatcher(IFileWatcher, ABC):
    """
    Abstract base for file watchers.
    
    Provides common watching logic.
    """
    
    def __init__(self, poll_interval: float = 1.0):
        """Initialize watcher."""
        self.poll_interval = poll_interval
        self._watched = {}
        self._running = False
    
    @abstractmethod
    def watch(self, path: Path, on_change: Callable[[Path, str], None]) -> None:
        """Watch path for changes."""
        pass
    
    @abstractmethod
    def unwatch(self, path: Path) -> None:
        """Stop watching path."""
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start watching."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop all watchers."""
        pass


class AFileLock(IFileLock, ABC):
    """
    Abstract base for file locks.
    
    Provides common locking logic.
    """
    
    def __init__(self, path: Union[str, Path], mode: LockMode = LockMode.EXCLUSIVE):
        """Initialize lock."""
        self.path = Path(path)
        self.mode = mode
        self._locked = False
    
    @abstractmethod
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire lock."""
        pass
    
    @abstractmethod
    def release(self) -> None:
        """Release lock."""
        pass
    
    def is_locked(self) -> bool:
        """Check if locked."""
        return self._locked
    
    def __enter__(self) -> 'AFileLock':
        """Context manager entry."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()

