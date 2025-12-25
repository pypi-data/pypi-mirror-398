#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/common/lock.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

File locking implementation for concurrent access control.

Priority 1 (Security): Safe concurrent access, prevent race conditions
Priority 2 (Usability): Context manager support for easy usage
Priority 3 (Maintainability): Simple, reliable lock implementation
Priority 4 (Performance): Minimal overhead, fast lock acquisition
Priority 5 (Extensibility): Easy to extend with different lock types
"""

import time
from pathlib import Path
from typing import Union, Optional, Any

from ..contracts import IFileLock


class FileLock(IFileLock):
    """
    File locking for concurrent access.
    
    Prevents race conditions in multi-process/multi-threaded scenarios.
    Uses file-based locking for cross-platform compatibility.
    
    Example:
        >>> with FileLock("data.json"):
        ...     # Exclusive access guaranteed
        ...     data = load_file("data.json")
        ...     data['counter'] += 1
        ...     save_file("data.json", data)
    """
    
    def __init__(self, path: Union[str, Path], timeout: Optional[float] = None):
        """
        Initialize file lock.
        
        Args:
            path: Path to lock (lock file will be path + '.lock')
            timeout: Default timeout for acquire (None = block forever)
        """
        self._path = Path(path)
        self._lock_path = Path(str(self._path) + '.lock')
        self._default_timeout = timeout
        self._locked = False
        self._lock_file: Optional[Any] = None
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire lock.
        
        Args:
            timeout: Timeout in seconds (None = use default, or block forever)
        
        Returns:
            True if lock acquired, False if timeout
        """
        if self._locked:
            return True
        
        timeout = timeout if timeout is not None else self._default_timeout
        start_time = time.time()
        
        while True:
            try:
                # Try to create lock file exclusively
                self._lock_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Use 'x' mode for exclusive creation
                self._lock_file = open(self._lock_path, 'x')
                self._locked = True
                return True
            
            except FileExistsError:
                # Lock file already exists
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        return False
                
                # Wait a bit and retry
                time.sleep(0.01)
            
            except Exception:
                return False
    
    def release(self) -> None:
        """Release lock."""
        if not self._locked:
            return
        
        try:
            if self._lock_file:
                self._lock_file.close()
                self._lock_file = None
            
            if self._lock_path.exists():
                self._lock_path.unlink()
            
            self._locked = False
        
        except Exception:
            pass
    
    def is_locked(self) -> bool:
        """Check if currently locked."""
        return self._locked
    
    def __enter__(self) -> 'FileLock':
        """Context manager entry."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.release()

