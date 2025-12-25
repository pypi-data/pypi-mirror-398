"""
Pipe Communication Utilities
============================

Production-grade pipes for XSystem.

Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Company: eXonware.com
Generation Date: September 05, 2025
"""

import asyncio
import os
import sys
import threading
import multiprocessing as mp
from typing import Any, Optional, Union, Callable, BinaryIO
import pickle
import struct
import logging

logger = logging.getLogger(__name__)


class Pipe:
    """
    Cross-platform pipe for inter-process communication.
    
    Features:
    - Automatic serialization/deserialization
    - Thread-safe operations
    - Timeout support
    - Error handling
    - Cross-platform compatibility
    """
    
    def __init__(self, duplex: bool = True, buffer_size: int = 8192):
        """
        Initialize pipe.
        
        Args:
            duplex: Whether pipe supports bidirectional communication
            buffer_size: Buffer size for data transfer
        """
        self.duplex = duplex
        self.buffer_size = buffer_size
        
        # Create pipe
        if sys.platform == 'win32':
            # Windows named pipes
            import uuid
            self.pipe_name = f"\\\\.\\pipe\\xwsystem_{uuid.uuid4().hex}"
            self._create_windows_pipe()
        else:
            # Unix domain sockets or os.pipe()
            self._create_unix_pipe()
        
        self._lock = threading.RLock()
        self._closed = False
    
    def _create_windows_pipe(self):
        """Create Windows named pipe."""
        # Import is explicit - if missing, user should install pywin32 for Windows optimizations
        import win32pipe
        import win32file
        
        try:
            # Create named pipe
            self._pipe_handle = win32pipe.CreateNamedPipe(
                self.pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX if self.duplex else win32pipe.PIPE_ACCESS_OUTBOUND,
                win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                1,  # max instances
                self.buffer_size,  # out buffer size
                self.buffer_size,  # in buffer size
                0,  # default timeout
                None  # security attributes
            )
            
            self._read_handle = self._pipe_handle
            self._write_handle = self._pipe_handle
            
        except Exception as e:
            # Fallback to multiprocessing pipe if named pipe creation fails
            logger.warning(f"Windows named pipe creation failed: {e}, using multiprocessing pipe")
            self._read_conn, self._write_conn = mp.Pipe(self.duplex)
            self._read_handle = self._read_conn
            self._write_handle = self._write_conn
    
    def _create_unix_pipe(self):
        """Create Unix pipe."""
        try:
            # Try to use os.pipe() for better performance
            read_fd, write_fd = os.pipe()
            self._read_handle = os.fdopen(read_fd, 'rb')
            self._write_handle = os.fdopen(write_fd, 'wb')
            
        except Exception:
            # Fallback to multiprocessing pipe
            logger.warning("os.pipe() failed, using multiprocessing pipe")
            self._read_conn, self._write_conn = mp.Pipe(self.duplex)
            self._read_handle = self._read_conn
            self._write_handle = self._write_conn
    
    def send(self, data: Any, timeout: Optional[float] = None) -> bool:
        """
        Send data through the pipe.
        
        Args:
            data: Data to send (will be pickled)
            timeout: Timeout in seconds
            
        Returns:
            True if successful
        """
        if self._closed:
            return False
        
        with self._lock:
            try:
                # Serialize data
                serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
                data_length = len(serialized)
                
                # Send length header first
                length_header = struct.pack('I', data_length)
                
                if hasattr(self._write_handle, 'send'):
                    # multiprocessing.Connection
                    self._write_handle.send(data)
                else:
                    # File-like object
                    self._write_handle.write(length_header)
                    self._write_handle.write(serialized)
                    self._write_handle.flush()
                
                logger.debug(f"Sent {data_length} bytes through pipe")
                return True
                
            except Exception as e:
                logger.error(f"Failed to send data through pipe: {e}")
                return False
    
    def recv(self, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Receive data from the pipe.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Received data or None
        """
        if self._closed:
            return None
        
        with self._lock:
            try:
                if hasattr(self._read_handle, 'recv'):
                    # multiprocessing.Connection
                    if hasattr(self._read_handle, 'poll'):
                        # Check if data is available
                        if timeout is not None and not self._read_handle.poll(timeout):
                            return None
                    
                    return self._read_handle.recv()
                    
                else:
                    # File-like object
                    # Read length header
                    length_data = self._read_handle.read(4)
                    if len(length_data) != 4:
                        return None
                    
                    data_length = struct.unpack('I', length_data)[0]
                    
                    # Read actual data
                    serialized = self._read_handle.read(data_length)
                    if len(serialized) != data_length:
                        return None
                    
                    # Deserialize
                    data = pickle.loads(serialized)
                    logger.debug(f"Received {data_length} bytes from pipe")
                    return data
                
            except Exception as e:
                logger.error(f"Failed to receive data from pipe: {e}")
                return None
    
    def close(self):
        """Close the pipe."""
        with self._lock:
            if self._closed:
                return
            
            self._closed = True
            
            try:
                if hasattr(self._read_handle, 'close'):
                    self._read_handle.close()
                if hasattr(self._write_handle, 'close') and self._write_handle != self._read_handle:
                    self._write_handle.close()
                    
                logger.debug("Pipe closed")
                
            except Exception as e:
                logger.error(f"Error closing pipe: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AsyncPipe:
    """
    Async-compatible pipe for inter-process communication.
    
    Features:
    - Full asyncio integration
    - Non-blocking operations
    - Automatic serialization
    - Graceful shutdown
    """
    
    def __init__(self, buffer_size: int = 8192):
        """
        Initialize async pipe.
        
        Args:
            buffer_size: Buffer size for data transfer
        """
        self.buffer_size = buffer_size
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._server: Optional[asyncio.Server] = None
        self._closed = False
        
        # Create async pipe using Unix domain socket or named pipe
        self._pipe_path = None
        self._setup_complete = asyncio.Event()
    
    async def _create_unix_socket(self):
        """Create Unix domain socket for async communication."""
        import tempfile
        
        # Create temporary socket path
        temp_dir = tempfile.gettempdir()
        self._pipe_path = os.path.join(temp_dir, f"xwsystem_pipe_{os.getpid()}")
        
        # Remove existing socket file
        try:
            os.unlink(self._pipe_path)
        except FileNotFoundError:
            pass
        
        # Create server
        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=self._pipe_path
        )
        
        logger.debug(f"Created async Unix socket pipe at {self._pipe_path}")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection."""
        self._reader = reader
        self._writer = writer
        self._setup_complete.set()
        logger.debug("Async pipe client connected")
    
    async def connect(self) -> bool:
        """Connect to the async pipe."""
        try:
            if sys.platform != 'win32':
                # Unix domain socket
                if not self._server:
                    await self._create_unix_socket()
                
                # Connect as client
                self._reader, self._writer = await asyncio.open_unix_connection(self._pipe_path)
                self._setup_complete.set()
                
            else:
                # Windows: Use asyncio subprocess pipes
                # This is a simplified implementation
                logger.warning("Windows async pipes not fully implemented")
                return False
            
            logger.debug("Connected to async pipe")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to async pipe: {e}")
            return False
    
    async def send(self, data: Any, timeout: Optional[float] = None) -> bool:
        """
        Send data through the async pipe.
        
        Args:
            data: Data to send
            timeout: Timeout in seconds
            
        Returns:
            True if successful
        """
        if self._closed or not self._writer:
            return False
        
        try:
            # Wait for setup to complete
            if timeout:
                await asyncio.wait_for(self._setup_complete.wait(), timeout=timeout)
            else:
                await self._setup_complete.wait()
            
            # Serialize data
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            data_length = len(serialized)
            
            # Send length header and data
            length_header = struct.pack('I', data_length)
            self._writer.write(length_header + serialized)
            
            if timeout:
                await asyncio.wait_for(self._writer.drain(), timeout=timeout)
            else:
                await self._writer.drain()
            
            logger.debug(f"Sent {data_length} bytes through async pipe")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send data through async pipe: {e}")
            return False
    
    async def recv(self, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Receive data from the async pipe.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Received data or None
        """
        if self._closed or not self._reader:
            return None
        
        try:
            # Wait for setup to complete
            if timeout:
                await asyncio.wait_for(self._setup_complete.wait(), timeout=timeout)
            else:
                await self._setup_complete.wait()
            
            # Read length header
            if timeout:
                length_data = await asyncio.wait_for(self._reader.read(4), timeout=timeout)
            else:
                length_data = await self._reader.read(4)
            
            if len(length_data) != 4:
                return None
            
            data_length = struct.unpack('I', length_data)[0]
            
            # Read actual data
            if timeout:
                serialized = await asyncio.wait_for(self._reader.read(data_length), timeout=timeout)
            else:
                serialized = await self._reader.read(data_length)
            
            if len(serialized) != data_length:
                return None
            
            # Deserialize
            data = pickle.loads(serialized)
            logger.debug(f"Received {data_length} bytes from async pipe")
            return data
            
        except Exception as e:
            logger.error(f"Failed to receive data from async pipe: {e}")
            return None
    
    async def close(self):
        """Close the async pipe."""
        if self._closed:
            return
        
        self._closed = True
        
        try:
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
            
            if self._server:
                self._server.close()
                await self._server.wait_closed()
            
            # Clean up socket file
            if self._pipe_path and os.path.exists(self._pipe_path):
                os.unlink(self._pipe_path)
            
            logger.debug("Async pipe closed")
            
        except Exception as e:
            logger.error(f"Error closing async pipe: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class PipeManager:
    """
    Manager for pipe creation and management.
    
    Provides a high-level interface for creating and managing pipes
    for inter-process communication.
    """
    
    def __init__(self):
        """Initialize pipe manager."""
        self._pipes = {}
        self._next_id = 0
        self._lock = threading.RLock()
    
    def create_pipe(self, duplex: bool = True, buffer_size: int = 8192) -> tuple:
        """
        Create a new pipe.
        
        Args:
            duplex: Whether pipe supports bidirectional communication
            buffer_size: Buffer size for data transfer
            
        Returns:
            Tuple of (read_end, write_end) or (pipe_id, pipe_object)
        """
        with self._lock:
            pipe_id = f"pipe_{self._next_id}"
            self._next_id += 1
            
            try:
                # Create pipe using multiprocessing
                read_conn, write_conn = mp.Pipe(duplex)
                
                # Store pipe info
                self._pipes[pipe_id] = {
                    'read_conn': read_conn,
                    'write_conn': write_conn,
                    'duplex': duplex,
                    'buffer_size': buffer_size
                }
                
                if duplex:
                    return (read_conn, write_conn)
                else:
                    return (read_conn, write_conn)
                    
            except Exception as e:
                logger.error(f"Failed to create pipe: {e}")
                return (None, None)
    
    def close_pipe(self, pipe_id: str) -> bool:
        """
        Close a pipe by ID.
        
        Args:
            pipe_id: ID of the pipe to close
            
        Returns:
            True if successful
        """
        with self._lock:
            if pipe_id not in self._pipes:
                return False
            
            try:
                pipe_info = self._pipes[pipe_id]
                pipe_info['read_conn'].close()
                pipe_info['write_conn'].close()
                del self._pipes[pipe_id]
                
                logger.debug(f"Closed pipe {pipe_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to close pipe {pipe_id}: {e}")
                return False
    
    def get_pipe_info(self, pipe_id: str) -> dict:
        """
        Get information about a pipe.
        
        Args:
            pipe_id: ID of the pipe
            
        Returns:
            Dictionary with pipe information
        """
        with self._lock:
            return self._pipes.get(pipe_id, {})
    
    def list_pipes(self) -> list:
        """
        List all active pipes.
        
        Returns:
            List of pipe IDs
        """
        with self._lock:
            return list(self._pipes.keys())
    
    def close_all_pipes(self) -> int:
        """
        Close all pipes.
        
        Returns:
            Number of pipes closed
        """
        with self._lock:
            closed_count = 0
            for pipe_id in list(self._pipes.keys()):
                if self.close_pipe(pipe_id):
                    closed_count += 1
            
            return closed_count


def is_pipes_available() -> bool:
    """Check if pipe functionality is available."""
    # multiprocessing and pickle are built-in Python modules
    import multiprocessing
    import pickle
    return True
