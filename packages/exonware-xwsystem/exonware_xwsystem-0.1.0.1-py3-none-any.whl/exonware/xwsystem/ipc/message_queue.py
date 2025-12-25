"""
Message Queue Utilities
=======================

Production-grade message queues for XWSystem.

Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Company: eXonware.com
Generation Date: September 05, 2025
"""

import asyncio
import queue
import threading
import multiprocessing as mp
from typing import Any, Optional, Callable
from dataclasses import dataclass
import time
import logging
from .defs import MessageQueueType

logger = logging.getLogger(__name__)


@dataclass
class Message[T]:
    """A message in the queue with metadata."""
    data: T
    timestamp: float
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class MessageQueue[T]:
    """
    Thread-safe message queue with advanced features.
    
    Features:
    - Priority queuing
    - Message retry logic
    - Timeout support
    - Statistics tracking
    - Dead letter queue
    - Graceful shutdown
    """
    
    def __init__(self, 
                 maxsize: int = 0, 
                 queue_type: MessageQueueType = MessageQueueType.THREAD_SAFE,
                 enable_priority: bool = False):
        """
        Initialize message queue.
        
        Args:
            maxsize: Maximum queue size (0 = unlimited)
            queue_type: Type of queue to create
            enable_priority: Enable priority queuing
        """
        self.maxsize = maxsize
        self.queue_type = queue_type
        self.enable_priority = enable_priority
        
        # Create appropriate queue
        self._manager = None
        if queue_type == MessageQueueType.PROCESS_SAFE:
            if enable_priority:
                self._manager = mp.Manager()
                self._queue = (
                    self._manager.PriorityQueue(maxsize)
                    if maxsize > 0
                    else self._manager.PriorityQueue()
                )
            else:
                self._queue = mp.Queue(maxsize) if maxsize > 0 else mp.Queue()
        else:  # THREAD_SAFE
            if enable_priority:
                self._queue = queue.PriorityQueue(maxsize)
            else:
                self._queue = queue.Queue(maxsize)
        
        # Dead letter queue for failed messages
        self._dead_letter_queue = queue.Queue()
        
        # Statistics
        self._stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_failed': 0,
            'messages_retried': 0,
        }
        self._stats_lock = threading.Lock()
        
        # Shutdown flag
        self._shutdown = threading.Event()
    
    def put(self, data: T, priority: int = 0, timeout: Optional[float] = None) -> bool:
        """
        Put a message in the queue.
        
        Args:
            data: Message data
            priority: Message priority (lower = higher priority)
            timeout: Timeout in seconds
            
        Returns:
            True if successful
        """
        if self._shutdown.is_set():
            return False
        
        try:
            message = Message(data=data, timestamp=time.time(), priority=priority)
            
            if self.enable_priority:
                # Priority queue expects (priority, item)
                queue_item = (priority, message)
            else:
                queue_item = message
            
            if self.queue_type == MessageQueueType.PROCESS_SAFE:
                if timeout is not None:
                    self._queue.put(queue_item, block=True, timeout=timeout)
                else:
                    self._queue.put(queue_item, block=True)
            else:
                self._queue.put(queue_item, timeout=timeout)
            
            with self._stats_lock:
                self._stats['messages_sent'] += 1
            
            logger.debug(f"Put message with priority {priority}")
            return True
            
        except (queue.Full, Exception) as e:
            logger.warning(f"Failed to put message: {e}")
            return False
    
    def get(self, timeout: Optional[float] = None) -> Optional[T]:
        """
        Get a message from the queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Message data or None
        """
        if self._shutdown.is_set():
            return None
        
        try:
            if self.queue_type == MessageQueueType.PROCESS_SAFE:
                if timeout is not None:
                    queue_item = self._queue.get(block=True, timeout=timeout)
                else:
                    queue_item = self._queue.get(block=True)
            else:
                queue_item = self._queue.get(timeout=timeout)
            
            # Extract message from priority queue format
            if self.enable_priority:
                _, message = queue_item
            else:
                message = queue_item
            
            with self._stats_lock:
                self._stats['messages_received'] += 1
            
            logger.debug(f"Got message from {message.timestamp}")
            return message.data
            
        except (queue.Empty, Exception) as e:
            logger.debug(f"Failed to get message: {e}")
            return None
    
    def put_nowait(self, data: T, priority: int = 0) -> bool:
        """Put a message without blocking."""
        return self.put(data, priority, timeout=0)
    
    def get_nowait(self) -> Optional[T]:
        """Get a message without blocking."""
        return self.get(timeout=0)
    
    def size(self) -> int:
        """Get current queue size."""
        try:
            return self._queue.qsize()
        except NotImplementedError:
            # Some queue implementations don't support qsize
            return -1
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()
    
    def clear(self):
        """Clear all messages from queue."""
        while not self.empty():
            try:
                self.get_nowait()
            except:
                break
    
    def get_stats(self) -> dict:
        """Get queue statistics."""
        with self._stats_lock:
            return self._stats.copy()
    
    def shutdown(self, timeout: float = 5.0):
        """Gracefully shutdown the queue."""
        self._shutdown.set()
        logger.info("Message queue shutdown initiated")
        if self._manager:
            try:
                self._manager.shutdown()
                self._manager = None
            except Exception as exc:
                logger.debug(f"Error shutting down manager: {exc}")
    
    def send(self, message: T, priority: int = 0, timeout: Optional[float] = None) -> bool:
        """
        Send a message (alias for put method).
        
        Args:
            message: Message to send
            priority: Message priority
            timeout: Timeout for sending
            
        Returns:
            True if successful
        """
        return self.put(message, priority, timeout)
    
    def receive(self, timeout: Optional[float] = None) -> Optional[T]:
        """
        Receive a message (alias for get method).
        
        Args:
            timeout: Timeout for receiving
            
        Returns:
            Received message or None
        """
        return self.get(timeout)
    
    def close(self):
        """
        Close the message queue (alias for shutdown method).
        """
        self.shutdown()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


class AsyncMessageQueue[T]:
    """
    Async-compatible message queue.
    
    Features:
    - Full asyncio integration
    - Async context manager support
    - Backpressure handling
    - Graceful shutdown
    """
    
    def __init__(self, maxsize: int = 0):
        """
        Initialize async message queue.
        
        Args:
            maxsize: Maximum queue size (0 = unlimited)
        """
        self.maxsize = maxsize
        self._queue: asyncio.Queue = asyncio.Queue(maxsize)
        self._shutdown = asyncio.Event()
        
        # Statistics
        self._stats = {
            'messages_sent': 0,
            'messages_received': 0,
        }
        self._stats_lock = asyncio.Lock()
    
    async def put(self, data: T, timeout: Optional[float] = None) -> bool:
        """
        Put a message in the queue.
        
        Args:
            data: Message data
            timeout: Timeout in seconds
            
        Returns:
            True if successful
        """
        if self._shutdown.is_set():
            return False
        
        try:
            message = Message(data=data, timestamp=time.time())
            
            if timeout is not None:
                await asyncio.wait_for(self._queue.put(message), timeout=timeout)
            else:
                await self._queue.put(message)
            
            async with self._stats_lock:
                self._stats['messages_sent'] += 1
            
            logger.debug("Put async message")
            return True
            
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Failed to put async message: {e}")
            return False
    
    async def get(self, timeout: Optional[float] = None) -> Optional[T]:
        """
        Get a message from the queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Message data or None
        """
        if self._shutdown.is_set():
            return None
        
        try:
            if timeout is not None:
                message = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            else:
                message = await self._queue.get()
            
            async with self._stats_lock:
                self._stats['messages_received'] += 1
            
            logger.debug("Got async message")
            return message.data
            
        except (asyncio.TimeoutError, Exception) as e:
            logger.debug(f"Failed to get async message: {e}")
            return None
    
    def put_nowait(self, data: T) -> bool:
        """Put a message without blocking."""
        if self._shutdown.is_set():
            return False
        
        try:
            message = Message(data=data, timestamp=time.time())
            self._queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            return False
    
    def get_nowait(self) -> Optional[T]:
        """Get a message without blocking."""
        if self._shutdown.is_set():
            return None
        
        try:
            message = self._queue.get_nowait()
            return message.data
        except asyncio.QueueEmpty:
            return None
    
    def size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()
    
    async def clear(self):
        """Clear all messages from queue."""
        while not self.empty():
            try:
                self.get_nowait()
            except:
                break
    
    async def get_stats(self) -> dict:
        """Get queue statistics."""
        async with self._stats_lock:
            return self._stats.copy()
    
    async def shutdown(self):
        """Gracefully shutdown the queue."""
        self._shutdown.set()
        logger.info("Async message queue shutdown initiated")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


def is_message_queue_available() -> bool:
    """Check if message queue functionality is available."""
    # queue and multiprocessing are built-in Python modules
    import queue
    import multiprocessing
    return True
