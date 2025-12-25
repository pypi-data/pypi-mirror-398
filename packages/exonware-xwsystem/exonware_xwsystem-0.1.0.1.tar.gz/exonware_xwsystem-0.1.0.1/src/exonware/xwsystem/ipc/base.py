#exonware/xwsystem/ipc/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

IPC module base classes - abstract classes for inter-process communication functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from .contracts import MessageType, QueueType, ProcessState, SharedMemoryType


class AMessageQueueBase(ABC):
    """Abstract base class for message queue operations."""
    
    def __init__(self, queue_name: str, queue_type: QueueType = QueueType.FIFO):
        """
        Initialize message queue.
        
        Args:
            queue_name: Name of the message queue
            queue_type: Type of queue (FIFO, LIFO, Priority)
        """
        self.queue_name = queue_name
        self.queue_type = queue_type
        self._connected = False
    
    @abstractmethod
    def connect(self) -> None:
        """Connect to message queue."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from message queue."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to message queue."""
        pass
    
    @abstractmethod
    def send(self, message: Any, message_type: MessageType = MessageType.DATA) -> bool:
        """Send message to queue."""
        pass
    
    @abstractmethod
    def receive(self, timeout: Optional[int] = None) -> Optional[Any]:
        """Receive message from queue."""
        pass
    
    @abstractmethod
    def peek(self) -> Optional[Any]:
        """Peek at next message without removing it."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get queue size."""
        pass
    
    @abstractmethod
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        pass
    
    @abstractmethod
    def is_full(self) -> bool:
        """Check if queue is full."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all messages from queue."""
        pass


class APipeBase(ABC):
    """Abstract base class for pipe operations."""
    
    def __init__(self, pipe_name: Optional[str] = None):
        """
        Initialize pipe.
        
        Args:
            pipe_name: Name of the pipe (optional)
        """
        self.pipe_name = pipe_name
        self._connected = False
        self._read_end = None
        self._write_end = None
    
    @abstractmethod
    def create(self) -> None:
        """Create pipe."""
        pass
    
    @abstractmethod
    def connect(self) -> None:
        """Connect to pipe."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from pipe."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to pipe."""
        pass
    
    @abstractmethod
    def write(self, data: Union[str, bytes]) -> int:
        """Write data to pipe."""
        pass
    
    @abstractmethod
    def read(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Read data from pipe."""
        pass
    
    @abstractmethod
    def close_read(self) -> None:
        """Close read end of pipe."""
        pass
    
    @abstractmethod
    def close_write(self) -> None:
        """Close write end of pipe."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close pipe."""
        pass


class ASharedMemoryBase(ABC):
    """Abstract base class for shared memory operations."""
    
    def __init__(self, memory_name: str, size: int, memory_type: SharedMemoryType = SharedMemoryType.SYSTEM_V):
        """
        Initialize shared memory.
        
        Args:
            memory_name: Name of shared memory segment
            size: Size of shared memory segment
            memory_type: Type of shared memory
        """
        self.memory_name = memory_name
        self.size = size
        self.memory_type = memory_type
        self._attached = False
        self._memory_handle = None
    
    @abstractmethod
    def create(self) -> bool:
        """Create shared memory segment."""
        pass
    
    @abstractmethod
    def attach(self) -> bool:
        """Attach to shared memory segment."""
        pass
    
    @abstractmethod
    def detach(self) -> None:
        """Detach from shared memory segment."""
        pass
    
    @abstractmethod
    def destroy(self) -> bool:
        """Destroy shared memory segment."""
        pass
    
    @abstractmethod
    def is_attached(self) -> bool:
        """Check if attached to shared memory."""
        pass
    
    @abstractmethod
    def write(self, data: bytes, offset: int = 0) -> int:
        """Write data to shared memory."""
        pass
    
    @abstractmethod
    def read(self, size: int, offset: int = 0) -> bytes:
        """Read data from shared memory."""
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """Get shared memory size."""
        pass
    
    @abstractmethod
    def lock(self) -> None:
        """Lock shared memory for exclusive access."""
        pass
    
    @abstractmethod
    def unlock(self) -> None:
        """Unlock shared memory."""
        pass


class AProcessManagerBase(ABC):
    """Abstract base class for process management."""
    
    def __init__(self):
        """Initialize process manager."""
        self._processes: dict[str, Any] = {}
    
    @abstractmethod
    def start_process(self, name: str, command: list[str], **kwargs) -> bool:
        """Start new process."""
        pass
    
    @abstractmethod
    def stop_process(self, name: str, timeout: Optional[int] = None) -> bool:
        """Stop process."""
        pass
    
    @abstractmethod
    def kill_process(self, name: str) -> bool:
        """Kill process."""
        pass
    
    @abstractmethod
    def get_process(self, name: str) -> Optional[Any]:
        """Get process by name."""
        pass
    
    @abstractmethod
    def list_processes(self) -> list[str]:
        """List all managed processes."""
        pass
    
    @abstractmethod
    def get_process_state(self, name: str) -> ProcessState:
        """Get process state."""
        pass
    
    @abstractmethod
    def is_process_running(self, name: str) -> bool:
        """Check if process is running."""
        pass
    
    @abstractmethod
    def get_process_pid(self, name: str) -> Optional[int]:
        """Get process PID."""
        pass
    
    @abstractmethod
    def get_process_output(self, name: str) -> Optional[str]:
        """Get process output."""
        pass
    
    @abstractmethod
    def get_process_error(self, name: str) -> Optional[str]:
        """Get process error output."""
        pass


class AProcessPoolBase(ABC):
    """Abstract base class for process pool management."""
    
    def __init__(self, max_processes: int = 4):
        """
        Initialize process pool.
        
        Args:
            max_processes: Maximum number of processes in pool
        """
        self.max_processes = max_processes
        self._processes: list[Any] = []
        self._available_processes: list[Any] = []
        self._busy_processes: list[Any] = []
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize process pool."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown process pool."""
        pass
    
    @abstractmethod
    def get_process(self) -> Optional[Any]:
        """Get available process from pool."""
        pass
    
    @abstractmethod
    def return_process(self, process: Any) -> None:
        """Return process to pool."""
        pass
    
    @abstractmethod
    def execute_task(self, task: callable, *args, **kwargs) -> Any:
        """Execute task using process from pool."""
        pass
    
    @abstractmethod
    def get_pool_size(self) -> int:
        """Get current pool size."""
        pass
    
    @abstractmethod
    def get_available_count(self) -> int:
        """Get number of available processes."""
        pass
    
    @abstractmethod
    def get_busy_count(self) -> int:
        """Get number of busy processes."""
        pass
    
    @abstractmethod
    def is_pool_full(self) -> bool:
        """Check if pool is full."""
        pass


class BaseIPC:
    """
    Base IPC class for backward compatibility.
    
    Provides a simple interface for IPC operations.
    """
    
    def __init__(self):
        """Initialize base IPC."""
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize IPC components.
        
        Returns:
            True if successful
        """
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """
        Cleanup IPC components.
        
        Returns:
            True if successful
        """
        self._initialized = False
        return True
    
    def is_initialized(self) -> bool:
        """
        Check if IPC is initialized.
        
        Returns:
            True if initialized
        """
        return self._initialized
    
    def shutdown(self) -> bool:
        """
        Shutdown IPC components.
        
        Returns:
            True if successful
        """
        return self.cleanup()
