"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Async-aware concurrency primitives and synchronization utilities.
"""

import asyncio
import logging
import time
import weakref
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager, Optional, Union
from collections import defaultdict

from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.threading.async_primitives")

# Performance-aware logging - only log if debug is enabled
def _debug_log(message: str) -> None:
    """Log debug message only if debug logging is enabled."""
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(message)


class AsyncLock:
    """
    Enhanced async lock with timeout support and debugging capabilities.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize async lock.
        
        Args:
            name: Optional name for debugging
        """
        self._lock = asyncio.Lock()
        self.name = name or f"AsyncLock-{id(self)}"
        self._acquired_at: Optional[float] = None
        self._acquired_by: Optional[str] = None

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire the lock with optional timeout.
        
        Args:
            timeout: Maximum time to wait for lock (None = wait forever)
            
        Returns:
            True if lock was acquired, False if timeout
        """
        if timeout is None:
            await self._lock.acquire()
            self._acquired_at = time.time()
            self._acquired_by = f"Task-{id(asyncio.current_task())}"
            _debug_log(f"Lock {self.name} acquired by {self._acquired_by}")
            return True
        
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=timeout)
            self._acquired_at = time.time()
            self._acquired_by = f"Task-{id(asyncio.current_task())}"
            logger.debug(f"Lock {self.name} acquired by {self._acquired_by} (timeout: {timeout}s)")
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Lock {self.name} acquisition timeout after {timeout}s")
            return False

    def release(self) -> None:
        """Release the lock."""
        if self._acquired_at:
            duration = time.time() - self._acquired_at
            logger.debug(f"Lock {self.name} released by {self._acquired_by} (held for {duration:.3f}s)")
        
        self._lock.release()
        self._acquired_at = None
        self._acquired_by = None

    def locked(self) -> bool:
        """Check if lock is currently held."""
        return self._lock.locked()

    @asynccontextmanager
    async def acquire_with_timeout(self, timeout: float) -> AsyncContextManager[bool]:
        """
        Context manager for lock acquisition with timeout.
        
        Args:
            timeout: Maximum time to wait for lock
            
        Yields:
            True if lock was acquired, False if timeout
        """
        acquired = await self.acquire(timeout)
        try:
            yield acquired
        finally:
            if acquired:
                self.release()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.release()


class AsyncSemaphore:
    """
    Enhanced async semaphore with monitoring and debugging.
    """

    def __init__(self, value: int = 1, name: Optional[str] = None):
        """
        Initialize async semaphore.
        
        Args:
            value: Initial semaphore value
            name: Optional name for debugging
        """
        self._semaphore = asyncio.Semaphore(value)
        self.name = name or f"AsyncSemaphore-{id(self)}"
        self._initial_value = value
        self._acquired_tasks: set[str] = set()

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire semaphore with optional timeout.
        
        Args:
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            True if acquired, False if timeout
        """
        task_id = f"Task-{id(asyncio.current_task())}"
        
        if timeout is None:
            await self._semaphore.acquire()
            self._acquired_tasks.add(task_id)
            logger.debug(f"Semaphore {self.name} acquired by {task_id} ({len(self._acquired_tasks)}/{self._initial_value})")
            return True
        
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout)
            self._acquired_tasks.add(task_id)
            logger.debug(f"Semaphore {self.name} acquired by {task_id} (timeout: {timeout}s) ({len(self._acquired_tasks)}/{self._initial_value})")
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Semaphore {self.name} acquisition timeout after {timeout}s")
            return False

    def release(self) -> None:
        """Release semaphore."""
        task_id = f"Task-{id(asyncio.current_task())}"
        self._acquired_tasks.discard(task_id)
        self._semaphore.release()
        logger.debug(f"Semaphore {self.name} released by {task_id} ({len(self._acquired_tasks)}/{self._initial_value})")

    def locked(self) -> bool:
        """Check if semaphore is fully acquired."""
        return self._semaphore.locked()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.release()


class AsyncEvent:
    """
    Enhanced async event with timeout and debugging.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize async event.
        
        Args:
            name: Optional name for debugging
        """
        self._event = asyncio.Event()
        self.name = name or f"AsyncEvent-{id(self)}"
        self._set_at: Optional[float] = None
        self._waiting_tasks: set[str] = set()

    async def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for event with optional timeout.
        
        Args:
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            True if event was set, False if timeout
        """
        task_id = f"Task-{id(asyncio.current_task())}"
        self._waiting_tasks.add(task_id)
        
        try:
            if timeout is None:
                await self._event.wait()
                logger.debug(f"Event {self.name} received by {task_id}")
                return True
            
            try:
                await asyncio.wait_for(self._event.wait(), timeout=timeout)
                logger.debug(f"Event {self.name} received by {task_id} (timeout: {timeout}s)")
                return True
            except asyncio.TimeoutError:
                logger.warning(f"Event {self.name} wait timeout after {timeout}s for {task_id}")
                return False
        finally:
            self._waiting_tasks.discard(task_id)

    def set(self) -> None:
        """Set the event."""
        self._set_at = time.time()
        waiting_count = len(self._waiting_tasks)
        self._event.set()
        logger.debug(f"Event {self.name} set, notifying {waiting_count} waiting tasks")

    def clear(self) -> None:
        """Clear the event."""
        self._event.clear()
        self._set_at = None
        logger.debug(f"Event {self.name} cleared")

    def is_set(self) -> bool:
        """Check if event is set."""
        return self._event.is_set()


class AsyncQueue:
    """
    Enhanced async queue with monitoring and timeout support.
    """

    def __init__(self, maxsize: int = 0, name: Optional[str] = None):
        """
        Initialize async queue.
        
        Args:
            maxsize: Maximum queue size (0 = unlimited)
            name: Optional name for debugging
        """
        self._queue = asyncio.Queue(maxsize=maxsize)
        self.name = name or f"AsyncQueue-{id(self)}"
        self._maxsize = maxsize
        self._put_count = 0
        self._get_count = 0

    async def put(self, item: Any, timeout: Optional[float] = None) -> bool:
        """
        Put item in queue with optional timeout.
        
        Args:
            item: Item to put in queue
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            True if item was put, False if timeout
        """
        if timeout is None:
            await self._queue.put(item)
            self._put_count += 1
            logger.debug(f"Queue {self.name} put item #{self._put_count} (size: {self.qsize()})")
            return True
        
        try:
            await asyncio.wait_for(self._queue.put(item), timeout=timeout)
            self._put_count += 1
            logger.debug(f"Queue {self.name} put item #{self._put_count} (timeout: {timeout}s) (size: {self.qsize()})")
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Queue {self.name} put timeout after {timeout}s")
            return False

    async def get(self, timeout: Optional[float] = None) -> Union[Any, None]:
        """
        Get item from queue with optional timeout.
        
        Args:
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            Item from queue, or None if timeout
        """
        if timeout is None:
            item = await self._queue.get()
            self._get_count += 1
            logger.debug(f"Queue {self.name} got item #{self._get_count} (size: {self.qsize()})")
            return item
        
        try:
            item = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            self._get_count += 1
            logger.debug(f"Queue {self.name} got item #{self._get_count} (timeout: {timeout}s) (size: {self.qsize()})")
            return item
        except asyncio.TimeoutError:
            logger.warning(f"Queue {self.name} get timeout after {timeout}s")
            return None

    def put_nowait(self, item: Any) -> bool:
        """
        Put item in queue without waiting.
        
        Args:
            item: Item to put
            
        Returns:
            True if successful, False if queue is full
        """
        try:
            self._queue.put_nowait(item)
            self._put_count += 1
            logger.debug(f"Queue {self.name} put_nowait item #{self._put_count} (size: {self.qsize()})")
            return True
        except asyncio.QueueFull:
            logger.warning(f"Queue {self.name} is full, put_nowait failed")
            return False

    def get_nowait(self) -> Union[Any, None]:
        """
        Get item from queue without waiting.
        
        Returns:
            Item from queue, or None if queue is empty
        """
        try:
            item = self._queue.get_nowait()
            self._get_count += 1
            logger.debug(f"Queue {self.name} get_nowait item #{self._get_count} (size: {self.qsize()})")
            return item
        except asyncio.QueueEmpty:
            logger.debug(f"Queue {self.name} is empty, get_nowait returned None")
            return None

    def task_done(self) -> None:
        """Mark task as done."""
        self._queue.task_done()

    async def join(self) -> None:
        """Wait for all tasks to be done."""
        await self._queue.join()

    def qsize(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()


class AsyncCondition:
    """
    Async condition variable with timeout support.
    """

    def __init__(self, lock: Optional[AsyncLock] = None, name: Optional[str] = None):
        """
        Initialize async condition.
        
        Args:
            lock: Optional lock to use (creates new one if None)
            name: Optional name for debugging
        """
        self._lock = lock or AsyncLock()
        self._condition = asyncio.Condition(self._lock._lock)
        self.name = name or f"AsyncCondition-{id(self)}"
        self._waiting_tasks: set[str] = set()

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire the underlying lock."""
        return await self._lock.acquire(timeout)

    def release(self) -> None:
        """Release the underlying lock."""
        self._lock.release()

    async def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for condition with optional timeout.
        
        Args:
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            True if notified, False if timeout
        """
        task_id = f"Task-{id(asyncio.current_task())}"
        self._waiting_tasks.add(task_id)
        
        try:
            if timeout is None:
                await self._condition.wait()
                logger.debug(f"Condition {self.name} notified to {task_id}")
                return True
            
            try:
                await asyncio.wait_for(self._condition.wait(), timeout=timeout)
                logger.debug(f"Condition {self.name} notified to {task_id} (timeout: {timeout}s)")
                return True
            except asyncio.TimeoutError:
                logger.warning(f"Condition {self.name} wait timeout after {timeout}s for {task_id}")
                return False
        finally:
            self._waiting_tasks.discard(task_id)

    def notify(self, n: int = 1) -> None:
        """
        Notify n waiting tasks.
        
        Args:
            n: Number of tasks to notify
        """
        waiting_count = len(self._waiting_tasks)
        self._condition.notify(n)
        logger.debug(f"Condition {self.name} notified {min(n, waiting_count)} of {waiting_count} waiting tasks")

    def notify_all(self) -> None:
        """Notify all waiting tasks."""
        waiting_count = len(self._waiting_tasks)
        self._condition.notify_all()
        logger.debug(f"Condition {self.name} notified all {waiting_count} waiting tasks")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.release()


class AsyncResourcePool:
    """
    Async resource pool for managing limited resources.
    """

    def __init__(self, resources: list, name: Optional[str] = None):
        """
        Initialize resource pool.
        
        Args:
            resources: List of resources to manage
            name: Optional name for debugging
        """
        self.name = name or f"AsyncResourcePool-{id(self)}"
        self._available = asyncio.Queue()
        self._in_use: dict[Any, str] = {}
        self._total_resources = len(resources)
        
        # Put all resources in the available queue
        for resource in resources:
            self._available.put_nowait(resource)
        
        logger.debug(f"Resource pool {self.name} initialized with {self._total_resources} resources")

    async def acquire(self, timeout: Optional[float] = None) -> Union[Any, None]:
        """
        Acquire a resource from the pool.
        
        Args:
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            Resource object, or None if timeout
        """
        task_id = f"Task-{id(asyncio.current_task())}"
        
        if timeout is None:
            resource = await self._available.get()
            self._in_use[resource] = task_id
            logger.debug(f"Resource pool {self.name} acquired resource by {task_id} ({len(self._in_use)}/{self._total_resources} in use)")
            return resource
        
        try:
            resource = await asyncio.wait_for(self._available.get(), timeout=timeout)
            self._in_use[resource] = task_id
            logger.debug(f"Resource pool {self.name} acquired resource by {task_id} (timeout: {timeout}s) ({len(self._in_use)}/{self._total_resources} in use)")
            return resource
        except asyncio.TimeoutError:
            logger.warning(f"Resource pool {self.name} acquisition timeout after {timeout}s")
            return None

    def release(self, resource: Any) -> None:
        """
        Release a resource back to the pool.
        
        Args:
            resource: Resource to release
        """
        if resource in self._in_use:
            task_id = self._in_use.pop(resource)
            self._available.put_nowait(resource)
            logger.debug(f"Resource pool {self.name} released resource by {task_id} ({len(self._in_use)}/{self._total_resources} in use)")
        else:
            logger.warning(f"Resource pool {self.name} attempted to release unknown resource")

    @asynccontextmanager
    async def get_resource(self, timeout: Optional[float] = None) -> AsyncContextManager[Any]:
        """
        Context manager for resource acquisition.
        
        Args:
            timeout: Maximum time to wait for resource
            
        Yields:
            Resource object, or None if timeout
        """
        resource = await self.acquire(timeout)
        try:
            yield resource
        finally:
            if resource is not None:
                self.release(resource)

    def available_count(self) -> int:
        """Get number of available resources."""
        return self._available.qsize()

    def in_use_count(self) -> int:
        """Get number of resources in use."""
        return len(self._in_use)

    def total_count(self) -> int:
        """Get total number of resources."""
        return self._total_resources
