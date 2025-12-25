"""
Shared Memory Utilities
=======================

Production-grade shared memory management for XSystem.

Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Company: eXonware.com
Generation Date: September 05, 2025
"""

import os
import sys
import mmap
import struct
import pickle
import threading
from typing import Any, Optional, Union
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class SharedData[T]:
    """
    Thread-safe shared data container with automatic serialization.
    
    Features:
    - Automatic pickle serialization/deserialization
    - Thread-safe access with locks
    - Type hints support
    - Memory-mapped file backend
    - Cross-platform compatibility
    """
    
    def __init__(self, name: str, size: int = 1024 * 1024, create: bool = True):
        """
        Initialize shared data container.
        
        Args:
            name: Unique name for the shared memory segment
            size: Size of memory segment in bytes
            create: Whether to create new segment or attach to existing
        """
        self.name = name
        self.size = size
        self._lock = threading.RLock()
        self._mmap: Optional[mmap.mmap] = None
        self._file_handle = None
        
        if create:
            self._create_segment()
        else:
            self._attach_segment()
    
    def _create_segment(self):
        """Create a new shared memory segment."""
        try:
            if sys.platform == 'win32':
                # Windows: Use memory-mapped files
                self._file_handle = mmap.mmap(-1, self.size, tagname=self.name)
                self._mmap = self._file_handle
            else:
                # Unix: Use /dev/shm or temporary files
                import tempfile
                self._file_handle = tempfile.NamedTemporaryFile(
                    prefix=f"xwsystem_shared_{self.name}_",
                    delete=False
                )
                self._file_handle.write(b'\x00' * self.size)
                self._file_handle.flush()
                
                self._mmap = mmap.mmap(
                    self._file_handle.fileno(),
                    self.size,
                    access=mmap.ACCESS_WRITE
                )
            
            # Initialize with empty data marker
            self._write_header(0, 0)  # length=0, checksum=0
            logger.info(f"Created shared memory segment '{self.name}' ({self.size} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to create shared memory segment '{self.name}': {e}")
            raise
    
    def _attach_segment(self):
        """Attach to an existing shared memory segment."""
        try:
            if sys.platform == 'win32':
                self._file_handle = mmap.mmap(-1, self.size, tagname=self.name)
                self._mmap = self._file_handle
            else:
                # This is simplified - in production, you'd need a registry
                # of shared memory segments or use POSIX shared memory
                raise NotImplementedError("Attaching to existing segments not implemented on Unix")
            
            logger.info(f"Attached to shared memory segment '{self.name}'")
            
        except Exception as e:
            logger.error(f"Failed to attach to shared memory segment '{self.name}': {e}")
            raise
    
    def _write_header(self, length: int, checksum: int):
        """Write header with data length and checksum."""
        header = struct.pack('II', length, checksum)
        self._mmap.seek(0)
        self._mmap.write(header)
    
    def _read_header(self) -> tuple[int, int]:
        """Read header to get data length and checksum."""
        self._mmap.seek(0)
        header = self._mmap.read(8)  # 2 * 4 bytes
        return struct.unpack('II', header)
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate simple checksum for data integrity."""
        return sum(data) % (2**32)
    
    def set(self, value: T) -> bool:
        """
        Store a value in shared memory.
        
        Args:
            value: Value to store (must be picklable)
            
        Returns:
            True if successful
        """
        with self._lock:
            try:
                # Serialize the value
                data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
                data_length = len(data)
                
                # Check if data fits
                if data_length + 8 > self.size:  # +8 for header
                    logger.error(f"Data too large for shared memory segment: {data_length} > {self.size - 8}")
                    return False
                
                # Calculate checksum
                checksum = self._calculate_checksum(data)
                
                # Write header and data
                self._write_header(data_length, checksum)
                self._mmap.seek(8)  # Skip header
                self._mmap.write(data)
                self._mmap.flush()
                
                logger.debug(f"Stored {data_length} bytes in shared memory '{self.name}'")
                return True
                
            except Exception as e:
                logger.error(f"Failed to store data in shared memory '{self.name}': {e}")
                return False
    
    def get(self) -> Optional[T]:
        """
        Retrieve a value from shared memory.
        
        Returns:
            Stored value or None if error/empty
        """
        with self._lock:
            try:
                # Read header
                length, expected_checksum = self._read_header()
                
                if length == 0:
                    return None  # No data stored
                
                # Read data
                self._mmap.seek(8)
                data = self._mmap.read(length)
                
                # Verify checksum
                actual_checksum = self._calculate_checksum(data)
                if actual_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch in shared memory '{self.name}'")
                    return None
                
                # Deserialize
                value = pickle.loads(data)
                logger.debug(f"Retrieved {length} bytes from shared memory '{self.name}'")
                return value
                
            except Exception as e:
                logger.error(f"Failed to retrieve data from shared memory '{self.name}': {e}")
                return None
    
    def clear(self) -> bool:
        """Clear the shared memory segment."""
        with self._lock:
            try:
                self._write_header(0, 0)
                self._mmap.flush()
                logger.debug(f"Cleared shared memory '{self.name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to clear shared memory '{self.name}': {e}")
                return False
    
    def close(self):
        """Close and cleanup the shared memory segment."""
        with self._lock:
            try:
                if self._mmap:
                    self._mmap.close()
                    self._mmap = None
                
                if self._file_handle and hasattr(self._file_handle, 'close'):
                    self._file_handle.close()
                    self._file_handle = None
                
                logger.debug(f"Closed shared memory '{self.name}'")
                
            except Exception as e:
                logger.error(f"Failed to close shared memory '{self.name}': {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()


class SharedMemoryManager:
    """
    Manager for multiple shared memory segments.
    
    Features:
    - Centralized management of shared memory segments
    - Automatic cleanup on shutdown
    - Thread-safe operations
    - Memory usage monitoring
    """
    
    def __init__(self):
        self._segments: dict[str, SharedData] = {}
        self._lock = threading.RLock()
    
    def create_segment(self, name: str, size: int = 1024 * 1024) -> SharedData:
        """
        Create a new shared memory segment.
        
        Args:
            name: Unique name for the segment
            size: Size in bytes
            
        Returns:
            SharedData instance
        """
        with self._lock:
            if name in self._segments:
                raise ValueError(f"Shared memory segment '{name}' already exists")
            
            segment = SharedData(name, size, create=True)
            self._segments[name] = segment
            return segment
    
    def get_segment(self, name: str) -> Optional[SharedData]:
        """Get an existing shared memory segment."""
        with self._lock:
            return self._segments.get(name)
    
    def remove_segment(self, name: str) -> bool:
        """Remove and cleanup a shared memory segment."""
        with self._lock:
            if name not in self._segments:
                return False
            
            segment = self._segments[name]
            segment.close()
            del self._segments[name]
            return True
    
    def list_segments(self) -> list[str]:
        """List all managed segment names."""
        with self._lock:
            return list(self._segments.keys())
    
    def cleanup_all(self):
        """Cleanup all managed segments."""
        with self._lock:
            for segment in self._segments.values():
                segment.close()
            self._segments.clear()
    
    def attach_segment(self, name: str) -> SharedData:
        """
        Attach to an existing shared memory segment.
        
        Args:
            name: Name of the segment to attach to
            
        Returns:
            SharedData object
        """
        return self.get_segment(name)
    
    def detach_segment(self, segment: SharedData) -> bool:
        """
        Detach from a shared memory segment.
        
        Args:
            segment: SharedData segment to detach from
            
        Returns:
            True if successful
        """
        try:
            segment.close()
            return True
        except Exception as e:
            logger.error(f"Failed to detach segment: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_all()


@contextmanager
def shared_data(name: str, size: int = 1024 * 1024):
    """
    Context manager for temporary shared data.
    
    Args:
        name: Segment name
        size: Size in bytes
        
    Yields:
        SharedData instance
    """
    segment = SharedData(name, size, create=True)
    try:
        yield segment
    finally:
        segment.close()


class SharedMemory:
    """
    Simple shared memory interface for backward compatibility.
    
    Provides a simplified interface to shared memory functionality.
    """
    
    def __init__(self, name: str = None, size: int = 1024 * 1024):
        """
        Initialize shared memory.
        
        Args:
            name: Name for the shared memory segment
            size: Size of the memory segment
        """
        self.name = name or f"xwsystem_shared_{os.getpid()}"
        self.size = size
        self._manager = SharedMemoryManager()
        self._segment = None
    
    def create(self, name: str, size: int) -> str:
        """
        Create a shared memory segment.
        
        Args:
            name: Name for the segment
            size: Size of the segment
            
        Returns:
            Memory ID
        """
        self.name = name
        self.size = size
        self._segment = self._manager.create_segment(name, size)
        return f"memory_{name}"
    
    def attach(self, name: str) -> str:
        """
        Attach to an existing shared memory segment.
        
        Args:
            name: Name of the segment
            
        Returns:
            Memory handle
        """
        self.name = name
        self._segment = self._manager.attach_segment(name)
        return f"handle_{name}"
    
    def detach(self, handle: str = None) -> bool:
        """
        Detach from the shared memory segment.
        
        Args:
            handle: Optional handle to detach (for backward compatibility)
        
        Returns:
            True if successful
        """
        if self._segment:
            self._manager.detach_segment(self._segment)
            self._segment = None
            return True
        return False
    
    def close(self) -> bool:
        """
        Close the shared memory segment.
        
        Returns:
            True if successful
        """
        if self._segment:
            self._manager.close_segment(self._segment)
            self._segment = None
            return True
        return False
    
    def destroy(self, name: str = None) -> bool:
        """
        Destroy the shared memory segment (alias for close method).
        
        Args:
            name: Optional name parameter (for backward compatibility)
        
        Returns:
            True if successful
        """
        return self.close()


def is_shared_memory_available() -> bool:
    """Check if shared memory functionality is available."""
    # mmap is a built-in Python module, always available
    import mmap
    return True
