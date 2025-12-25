#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/common/watcher.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

File watching implementation for change monitoring.

Priority 1 (Security): Safe file monitoring without exposing system internals
Priority 2 (Usability): Simple callback-based API
Priority 3 (Maintainability): Clean, testable watcher implementation
Priority 4 (Performance): Efficient polling with configurable interval
Priority 5 (Extensibility): Easy to add new event types
"""

import time
import threading
from pathlib import Path
from typing import Any, Optional, Callable

from ..contracts import IFileWatcher


class FileWatcher(IFileWatcher):
    """
    Watch files/folders for changes.
    
    Uses polling-based implementation for cross-platform compatibility.
    For better performance, consider using `watchdog` library.
    
    Use cases:
    - Configuration hot-reload
    - Live data updates
    - Development auto-reload
    - File sync monitoring
    
    Examples:
        >>> def on_change(path, event):
        ...     print(f"{path} was {event}")
        >>> 
        >>> watcher = FileWatcher()
        >>> watcher.watch(Path("config.json"), on_change)
        >>> watcher.start()
        >>> # ... do work ...
        >>> watcher.stop()
    """
    
    def __init__(self, poll_interval: float = 1.0):
        """
        Initialize file watcher.
        
        Args:
            poll_interval: Polling interval in seconds
        """
        self._poll_interval = poll_interval
        self._watched: dict[Path, Callable] = {}
        self._file_states: dict[Path, dict[str, Any]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def watch(self, path: Path, on_change: Callable[[Path, str], None]) -> None:
        """
        Watch path for changes.
        
        Args:
            path: Path to watch
            on_change: Callback receiving (path, event_type)
                       event_type: 'created', 'modified', 'deleted', 'moved'
        """
        path = Path(path).resolve()
        self._watched[path] = on_change
        
        # Record initial state
        if path.exists():
            stat = path.stat()
            self._file_states[path] = {
                'exists': True,
                'mtime': stat.st_mtime,
                'size': stat.st_size
            }
        else:
            self._file_states[path] = {'exists': False}
    
    def unwatch(self, path: Path) -> None:
        """Stop watching path."""
        path = Path(path).resolve()
        if path in self._watched:
            del self._watched[path]
        if path in self._file_states:
            del self._file_states[path]
    
    def start(self) -> None:
        """Start watching (non-blocking)."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop all watchers."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._poll_interval * 2)
            self._thread = None
    
    def _watch_loop(self) -> None:
        """Internal watch loop."""
        while self._running:
            try:
                self._check_changes()
            except Exception:
                pass  # Silently continue on errors
            
            time.sleep(self._poll_interval)
    
    def _check_changes(self) -> None:
        """Check for file changes."""
        for path, callback in list(self._watched.items()):
            try:
                old_state = self._file_states.get(path, {})
                exists_now = path.exists()
                existed_before = old_state.get('exists', False)
                
                if not existed_before and exists_now:
                    # File created
                    stat = path.stat()
                    self._file_states[path] = {
                        'exists': True,
                        'mtime': stat.st_mtime,
                        'size': stat.st_size
                    }
                    callback(path, 'created')
                
                elif existed_before and not exists_now:
                    # File deleted
                    self._file_states[path] = {'exists': False}
                    callback(path, 'deleted')
                
                elif existed_before and exists_now:
                    # Check if modified
                    stat = path.stat()
                    if (stat.st_mtime != old_state.get('mtime') or 
                        stat.st_size != old_state.get('size')):
                        self._file_states[path] = {
                            'exists': True,
                            'mtime': stat.st_mtime,
                            'size': stat.st_size
                        }
                        callback(path, 'modified')
            
            except Exception:
                continue

