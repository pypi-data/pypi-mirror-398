#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Threading protocol interfaces for XWSystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Iterator, Callable, Coroutine, Awaitable
import threading
import asyncio

# Import enums from types module
from .defs import (
    ThreadState,
    LockType,
    ThreadPriority,
    AsyncState,
    ConcurrencyMode
)


# ============================================================================
# LOCK INTERFACES
# ============================================================================

class ILockable(ABC):
    """
    Interface for lockable objects.
    
    Enforces consistent locking behavior across XWSystem.
    """
    
    @abstractmethod
    def acquire_lock(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire lock.
        
        Args:
            blocking: Whether to block until lock is acquired
            timeout: Timeout in seconds
            
        Returns:
            True if lock acquired
        """
        pass
    
    @abstractmethod
    def release_lock(self) -> None:
        """
        Release lock.
        """
        pass
    
    @abstractmethod
    def is_locked(self) -> bool:
        """
        Check if object is locked.
        
        Returns:
            True if locked
        """
        pass
    
    @abstractmethod
    def try_lock(self, timeout: Optional[float] = None) -> bool:
        """
        Try to acquire lock without blocking.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if lock acquired
        """
        pass
    
    @abstractmethod
    def get_lock_type(self) -> LockType:
        """
        Get lock type.
        
        Returns:
            Lock type
        """
        pass
    
    @abstractmethod
    def get_lock_owner(self) -> Optional[str]:
        """
        Get lock owner thread ID.
        
        Returns:
            Thread ID of lock owner or None
        """
        pass
    
    @abstractmethod
    def get_lock_count(self) -> int:
        """
        Get lock acquisition count.
        
        Returns:
            Number of times lock has been acquired
        """
        pass


# ============================================================================
# ASYNC INTERFACES
# ============================================================================

class IAsync(ABC):
    """
    Interface for async operations.
    
    Enforces consistent async behavior across XWSystem.
    """
    
    @abstractmethod
    async def async_method(self, *args, **kwargs) -> Any:
        """
        Execute method asynchronously.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Method result
        """
        pass
    
    @abstractmethod
    def await_result(self, coroutine: Coroutine) -> Any:
        """
        Await coroutine result.
        
        Args:
            coroutine: Coroutine to await
            
        Returns:
            Coroutine result
        """
        pass
    
    @abstractmethod
    def is_async(self) -> bool:
        """
        Check if object supports async operations.
        
        Returns:
            True if async supported
        """
        pass
    
    @abstractmethod
    def get_future(self) -> asyncio.Future:
        """
        Get future for async operation.
        
        Returns:
            Future object
        """
        pass
    
    @abstractmethod
    def get_async_state(self) -> AsyncState:
        """
        Get async operation state.
        
        Returns:
            Current async state
        """
        pass
    
    @abstractmethod
    def cancel_async(self) -> bool:
        """
        Cancel async operation.
        
        Returns:
            True if cancelled
        """
        pass
    
    @abstractmethod
    def is_async_completed(self) -> bool:
        """
        Check if async operation is completed.
        
        Returns:
            True if completed
        """
        pass
    
    @abstractmethod
    def get_async_result(self) -> Any:
        """
        Get async operation result.
        
        Returns:
            Async operation result
        """
        pass


# ============================================================================
# THREAD SAFETY INTERFACES
# ============================================================================

class IThreadSafe(ABC):
    """
    Interface for thread-safe objects.
    
    Enforces consistent thread safety across XWSystem.
    """
    
    @abstractmethod
    def thread_safe_method(self, *args, **kwargs) -> Any:
        """
        Execute method in thread-safe manner.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Method result
        """
        pass
    
    @abstractmethod
    def get_thread_id(self) -> int:
        """
        Get current thread ID.
        
        Returns:
            Thread ID
        """
        pass
    
    @abstractmethod
    def is_thread_safe(self) -> bool:
        """
        Check if object is thread-safe.
        
        Returns:
            True if thread-safe
        """
        pass
    
    @abstractmethod
    def get_thread_count(self) -> int:
        """
        Get number of active threads.
        
        Returns:
            Number of active threads
        """
        pass
    
    @abstractmethod
    def get_thread_info(self) -> dict[str, Any]:
        """
        Get thread information.
        
        Returns:
            Thread information dictionary
        """
        pass
    
    @abstractmethod
    def wait_for_threads(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all threads to complete.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if all threads completed
        """
        pass
    
    @abstractmethod
    def interrupt_threads(self) -> None:
        """
        Interrupt all threads.
        """
        pass
    
    @abstractmethod
    def join_threads(self) -> None:
        """
        Join all threads.
        """
        pass


# ============================================================================
# THREAD POOL INTERFACES
# ============================================================================

class IThreadPool(ABC):
    """
    Interface for thread pool management.
    
    Enforces consistent thread pool behavior across XWSystem.
    """
    
    @abstractmethod
    def submit_task(self, func: Callable, *args, **kwargs) -> Any:
        """
        Submit task to thread pool.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Task result or future
        """
        pass
    
    @abstractmethod
    def submit_async_task(self, func: Callable, *args, **kwargs) -> asyncio.Future:
        """
        Submit async task to thread pool.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Future object
        """
        pass
    
    @abstractmethod
    def get_pool_size(self) -> int:
        """
        Get thread pool size.
        
        Returns:
            Number of threads in pool
        """
        pass
    
    @abstractmethod
    def set_pool_size(self, size: int) -> None:
        """
        Set thread pool size.
        
        Args:
            size: New pool size
        """
        pass
    
    @abstractmethod
    def get_active_count(self) -> int:
        """
        Get number of active threads.
        
        Returns:
            Number of active threads
        """
        pass
    
    @abstractmethod
    def get_queue_size(self) -> int:
        """
        Get task queue size.
        
        Returns:
            Number of queued tasks
        """
        pass
    
    @abstractmethod
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown thread pool.
        
        Args:
            wait: Whether to wait for tasks to complete
        """
        pass
    
    @abstractmethod
    def is_shutdown(self) -> bool:
        """
        Check if thread pool is shutdown.
        
        Returns:
            True if shutdown
        """
        pass


# ============================================================================
# CONCURRENCY CONTROL INTERFACES
# ============================================================================

class IConcurrencyControl(ABC):
    """
    Interface for concurrency control.
    
    Enforces consistent concurrency control across XWSystem.
    """
    
    @abstractmethod
    def acquire_resource(self, resource_id: str, timeout: Optional[float] = None) -> bool:
        """
        Acquire resource for exclusive access.
        
        Args:
            resource_id: Resource identifier
            timeout: Timeout in seconds
            
        Returns:
            True if resource acquired
        """
        pass
    
    @abstractmethod
    def release_resource(self, resource_id: str) -> None:
        """
        Release resource.
        
        Args:
            resource_id: Resource identifier
        """
        pass
    
    @abstractmethod
    def is_resource_available(self, resource_id: str) -> bool:
        """
        Check if resource is available.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            True if available
        """
        pass
    
    @abstractmethod
    def get_resource_owner(self, resource_id: str) -> Optional[str]:
        """
        Get resource owner.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Owner thread ID or None
        """
        pass
    
    @abstractmethod
    def wait_for_resource(self, resource_id: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for resource to become available.
        
        Args:
            resource_id: Resource identifier
            timeout: Timeout in seconds
            
        Returns:
            True if resource became available
        """
        pass
    
    @abstractmethod
    def get_concurrency_mode(self) -> ConcurrencyMode:
        """
        Get concurrency mode.
        
        Returns:
            Current concurrency mode
        """
        pass
    
    @abstractmethod
    def set_concurrency_mode(self, mode: ConcurrencyMode) -> None:
        """
        Set concurrency mode.
        
        Args:
            mode: Concurrency mode to set
        """
        pass


# ============================================================================
# SYNCHRONIZATION INTERFACES
# ============================================================================

class ISynchronization(ABC):
    """
    Interface for synchronization primitives.
    
    Enforces consistent synchronization across XWSystem.
    """
    
    @abstractmethod
    def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for condition.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if condition met
        """
        pass
    
    @abstractmethod
    def notify(self) -> None:
        """
        Notify waiting threads.
        """
        pass
    
    @abstractmethod
    def notify_all(self) -> None:
        """
        Notify all waiting threads.
        """
        pass
    
    @abstractmethod
    def signal(self) -> None:
        """
        Signal condition.
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """
        Reset synchronization primitive.
        """
        pass
    
    @abstractmethod
    def is_set(self) -> bool:
        """
        Check if condition is set.
        
        Returns:
            True if set
        """
        pass
    
    @abstractmethod
    def get_waiting_count(self) -> int:
        """
        Get number of waiting threads.
        
        Returns:
            Number of waiting threads
        """
        pass


# ============================================================================
# DEADLOCK DETECTION INTERFACES
# ============================================================================

class IDeadlockDetection(ABC):
    """
    Interface for deadlock detection.
    
    Enforces consistent deadlock detection across XWSystem.
    """
    
    @abstractmethod
    def detect_deadlock(self) -> list[dict[str, Any]]:
        """
        Detect deadlocks.
        
        Returns:
            List of deadlock information
        """
        pass
    
    @abstractmethod
    def is_deadlocked(self) -> bool:
        """
        Check if system is deadlocked.
        
        Returns:
            True if deadlocked
        """
        pass
    
    @abstractmethod
    def resolve_deadlock(self, deadlock_info: dict[str, Any]) -> bool:
        """
        Resolve deadlock.
        
        Args:
            deadlock_info: Deadlock information
            
        Returns:
            True if resolved
        """
        pass
    
    @abstractmethod
    def get_lock_graph(self) -> dict[str, list[str]]:
        """
        Get lock dependency graph.
        
        Returns:
            Lock dependency graph
        """
        pass
    
    @abstractmethod
    def add_lock_dependency(self, resource1: str, resource2: str) -> None:
        """
        Add lock dependency.
        
        Args:
            resource1: First resource
            resource2: Second resource
        """
        pass
    
    @abstractmethod
    def remove_lock_dependency(self, resource1: str, resource2: str) -> None:
        """
        Remove lock dependency.
        
        Args:
            resource1: First resource
            resource2: Second resource
        """
        pass
    
    @abstractmethod
    def get_deadlock_prevention_mode(self) -> bool:
        """
        Get deadlock prevention mode.
        
        Returns:
            True if prevention enabled
        """
        pass
    
    @abstractmethod
    def set_deadlock_prevention_mode(self, enabled: bool) -> None:
        """
        Set deadlock prevention mode.
        
        Args:
            enabled: Whether to enable prevention
        """
        pass


# ============================================================================
# THREAD MONITORING INTERFACES
# ============================================================================

class IThreadMonitor(ABC):
    """
    Interface for thread monitoring.
    
    Enforces consistent thread monitoring across XWSystem.
    """
    
    @abstractmethod
    def get_thread_stats(self) -> dict[str, Any]:
        """
        Get thread statistics.
        
        Returns:
            Thread statistics dictionary
        """
        pass
    
    @abstractmethod
    def get_thread_list(self) -> list[dict[str, Any]]:
        """
        Get list of all threads.
        
        Returns:
            List of thread information
        """
        pass
    
    @abstractmethod
    def get_thread_by_id(self, thread_id: int) -> Optional[dict[str, Any]]:
        """
        Get thread by ID.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread information or None
        """
        pass
    
    @abstractmethod
    def monitor_thread_performance(self, thread_id: int) -> dict[str, Any]:
        """
        Monitor thread performance.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Performance metrics
        """
        pass
    
    @abstractmethod
    def detect_thread_leaks(self) -> list[int]:
        """
        Detect thread leaks.
        
        Returns:
            List of leaked thread IDs
        """
        pass
    
    @abstractmethod
    def cleanup_thread_leaks(self, thread_ids: list[int]) -> int:
        """
        Cleanup thread leaks.
        
        Args:
            thread_ids: Thread IDs to cleanup
            
        Returns:
            Number of threads cleaned up
        """
        pass
    
    @abstractmethod
    def get_thread_priority(self, thread_id: int) -> ThreadPriority:
        """
        Get thread priority.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread priority
        """
        pass
    
    @abstractmethod
    def set_thread_priority(self, thread_id: int, priority: ThreadPriority) -> bool:
        """
        Set thread priority.
        
        Args:
            thread_id: Thread ID
            priority: New priority
            
        Returns:
            True if set successfully
        """
        pass


# ============================================================================
# ASYNC CONTEXT MANAGER INTERFACES
# ============================================================================

class IAsyncContextManager(ABC):
    """
    Interface for async context managers.
    
    Enforces consistent async context management across XWSystem.
    """
    
    @abstractmethod
    async def __aenter__(self) -> 'IAsyncContextManager':
        """
        Async context manager entry.
        
        Returns:
            Self
        """
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type: type, exc_val: Exception, exc_tb: Any) -> bool:
        """
        Async context manager exit.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
            
        Returns:
            True if exception handled
        """
        pass
    
    @abstractmethod
    def is_async_context_active(self) -> bool:
        """
        Check if async context is active.
        
        Returns:
            True if active
        """
        pass
    
    @abstractmethod
    def get_async_context_info(self) -> dict[str, Any]:
        """
        Get async context information.
        
        Returns:
            Context information dictionary
        """
        pass
