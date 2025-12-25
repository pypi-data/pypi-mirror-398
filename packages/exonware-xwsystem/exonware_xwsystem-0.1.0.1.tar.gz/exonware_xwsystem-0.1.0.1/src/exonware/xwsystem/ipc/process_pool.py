"""
Process Pool Utilities
======================

Production-grade process pools for XSystem.

Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Company: eXonware.com
Generation Date: September 05, 2025
"""

import asyncio
import concurrent.futures
import functools
import logging
import multiprocessing as mp
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of a process pool task."""
    task_id: str
    result: Any
    success: bool
    error: Optional[str] = None
    execution_time: float = 0.0
    worker_pid: Optional[int] = None


class ProcessPool:
    """
    Production-grade process pool with monitoring and error handling.
    
    Features:
    - Automatic worker management
    - Task timeout handling
    - Error recovery
    - Performance monitoring
    - Graceful shutdown
    - Load balancing
    """
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 size: Optional[int] = None,  # Alias for max_workers for backward compatibility
                 initializer: Optional[Callable] = None,
                 initargs: tuple = (),
                 timeout: Optional[float] = None):
        """
        Initialize process pool.
        
        Args:
            max_workers: Maximum number of worker processes
            size: Alias for max_workers (for backward compatibility)
            initializer: Function to run in each worker on startup
            initargs: Arguments for initializer function
            timeout: Default timeout for tasks
        """
        # Handle backward compatibility with 'size' parameter
        if size is not None and max_workers is None:
            max_workers = size
        
        self.max_workers = max_workers or mp.cpu_count()
        self.initializer = initializer
        self.initargs = initargs
        self.timeout = timeout
        
        # Create process pool
        self._executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=initializer,
            initargs=initargs
        )
        
        # Task tracking
        self._active_tasks: dict[str, concurrent.futures.Future] = {}
        self._completed_tasks: list[TaskResult] = []
        self._task_counter = 0
        
        # Statistics
        self._stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0,
        }
    
    def submit(self, 
               fn: Callable, 
               *args, 
               task_id: Optional[str] = None,
               timeout: Optional[float] = None,
               **kwargs) -> str:
        """
        Submit a task to the process pool.
        
        Args:
            fn: Function to execute
            *args: Positional arguments for function
            task_id: Optional task identifier
            timeout: Task timeout (overrides default)
            **kwargs: Keyword arguments for function
            
        Returns:
            Task ID
        """
        if task_id is None:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}"
        
        start_time = time.time()
        
        # Submit task to executor
        try:
            future = self._executor.submit(fn, *args, **kwargs)
            self._active_tasks[task_id] = future
            
            # Add completion callback
            def task_completed(fut):
                execution_time = time.time() - start_time
                
                try:
                    result = fut.result(timeout=timeout or self.timeout)
                    task_result = TaskResult(
                        task_id=task_id,
                        result=result,
                        success=True,
                        execution_time=execution_time
                    )
                    self._stats['tasks_completed'] += 1
                    self._stats['total_execution_time'] += execution_time
                    
                except Exception as e:
                    task_result = TaskResult(
                        task_id=task_id,
                        result=None,
                        success=False,
                        error=str(e),
                        execution_time=execution_time
                    )
                    self._stats['tasks_failed'] += 1
                
                # Store result and cleanup
                self._completed_tasks.append(task_result)
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]
                
                logger.debug(f"Task {task_id} completed in {execution_time:.3f}s")
            
            future.add_done_callback(task_completed)
            self._stats['tasks_submitted'] += 1
            
            logger.debug(f"Submitted task {task_id}")
            return task_id
            
        except Exception as e:
            # Handle any submission errors
            logger.error(f"Failed to submit task {task_id}: {e}")
            raise
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Get result of a completed task.
        
        Args:
            task_id: Task identifier
            timeout: Timeout for waiting
            
        Returns:
            Task result or None if not found
        """
        # Check completed tasks first
        for result in self._completed_tasks:
            if result.task_id == task_id:
                logger.debug(f"Found completed task {task_id} with result: {result.result}")
                return result.result
        
        # Check if task is still active
        if task_id in self._active_tasks:
            future = self._active_tasks[task_id]
            try:
                # Wait for completion
                future.result(timeout=timeout)
                
                # Should be in completed tasks now
                for result in self._completed_tasks:
                    if result.task_id == task_id:
                        return result.result
                        
            except concurrent.futures.TimeoutError:
                logger.warning(f"Task {task_id} timed out")
                return None
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                return None
        
        return None
    
    def wait_for_all(self, timeout: Optional[float] = None) -> list[TaskResult]:
        """
        Wait for all active tasks to complete.
        
        Args:
            timeout: Timeout for waiting
            
        Returns:
            List of all task results
        """
        if not self._active_tasks:
            return self._completed_tasks.copy()
        
        try:
            # Wait for all active futures
            active_futures = list(self._active_tasks.values())
            concurrent.futures.wait(active_futures, timeout=timeout)
            
        except Exception as e:
            logger.error(f"Error waiting for tasks: {e}")
        
        return self._completed_tasks.copy()
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel an active task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if cancelled successfully
        """
        if task_id not in self._active_tasks:
            return False
        
        future = self._active_tasks[task_id]
        cancelled = future.cancel()
        
        if cancelled:
            del self._active_tasks[task_id]
            logger.info(f"Cancelled task {task_id}")
        
        return cancelled
    
    def get_active_tasks(self) -> list[str]:
        """Get list of active task IDs."""
        return list(self._active_tasks.keys())
    
    def get_stats(self) -> dict:
        """Get process pool statistics."""
        stats = self._stats.copy()
        stats['active_tasks'] = len(self._active_tasks)
        stats['completed_tasks'] = len(self._completed_tasks)
        stats['max_workers'] = self.max_workers
        
        if stats['tasks_completed'] > 0:
            stats['avg_execution_time'] = stats['total_execution_time'] / stats['tasks_completed']
        else:
            stats['avg_execution_time'] = 0.0
        
        return stats
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None):
        """
        Shutdown the process pool.
        
        Args:
            wait: Whether to wait for active tasks
            timeout: Timeout for shutdown
        """
        logger.info("Shutting down process pool")
        
        if wait and timeout:
            self.wait_for_all(timeout)
        
        self._executor.shutdown(wait=wait)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


class AsyncProcessPool:
    """
    Async-compatible process pool wrapper.
    
    Features:
    - Asyncio integration
    - Non-blocking task submission
    - Async result retrieval
    - Graceful async shutdown
    """
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 initializer: Optional[Callable] = None,
                 initargs: tuple = ()):
        """
        Initialize async process pool.
        
        Args:
            max_workers: Maximum number of worker processes
            initializer: Function to run in each worker on startup
            initargs: Arguments for initializer function
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.initializer = initializer
        self.initargs = initargs
        
        # Will be created when first used
        self._executor: Optional[concurrent.futures.ProcessPoolExecutor] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Task tracking
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._task_counter = 0
    
    def _ensure_executor(self):
        """Ensure executor is created in the correct event loop."""
        if self._executor is None:
            self._executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=self.max_workers,
                initializer=self.initializer,
                initargs=self.initargs
            )
            self._loop = asyncio.get_event_loop()
    
    async def submit(self, 
                    fn: Callable, 
                    *args, 
                    task_id: Optional[str] = None,
                    **kwargs) -> str:
        """
        Submit a task to the async process pool.
        
        Args:
            fn: Function to execute
            *args: Positional arguments for function
            task_id: Optional task identifier
            **kwargs: Keyword arguments for function
            
        Returns:
            Task ID
        """
        self._ensure_executor()
        
        if task_id is None:
            self._task_counter += 1
            task_id = f"async_task_{self._task_counter}"
        
        # Create async task
        async def run_task():
            loop = asyncio.get_event_loop()
            callable_fn = functools.partial(fn, *args, **kwargs)
            return await loop.run_in_executor(self._executor, callable_fn)
        
        task = asyncio.create_task(run_task())
        self._active_tasks[task_id] = task
        
        # Add completion callback
        def task_done(t):
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
        
        task.add_done_callback(task_done)
        
        logger.debug(f"Submitted async task {task_id}")
        return task_id
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get result of a task.
        
        Args:
            task_id: Task identifier
            timeout: Timeout for waiting
            
        Returns:
            Task result
        """
        if task_id not in self._active_tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self._active_tasks[task_id]
        
        if timeout is not None:
            return await asyncio.wait_for(task, timeout=timeout)
        else:
            return await task
    
    async def wait_for_all(self, timeout: Optional[float] = None) -> list[Any]:
        """
        Wait for all active tasks to complete.
        
        Args:
            timeout: Timeout for waiting
            
        Returns:
            List of all results
        """
        if not self._active_tasks:
            return []
        
        tasks = list(self._active_tasks.values())
        
        if timeout is not None:
            done, pending = await asyncio.wait(tasks, timeout=timeout)
            results = []
            
            # Get results from completed tasks
            for task in done:
                try:
                    results.append(await task)
                except Exception as e:
                    logger.error(f"Task failed: {e}")
                    results.append(None)
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            return results
        else:
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel an active task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if cancelled successfully
        """
        if task_id not in self._active_tasks:
            return False
        
        task = self._active_tasks[task_id]
        cancelled = task.cancel()
        
        if cancelled:
            del self._active_tasks[task_id]
            logger.info(f"Cancelled async task {task_id}")
        
        return cancelled
    
    def get_active_tasks(self) -> list[str]:
        """Get list of active task IDs."""
        return list(self._active_tasks.keys())
    
    async def shutdown(self, timeout: Optional[float] = None):
        """
        Shutdown the async process pool.
        
        Args:
            timeout: Timeout for shutdown
        """
        logger.info("Shutting down async process pool")
        
        # Cancel all active tasks
        for task_id in list(self._active_tasks.keys()):
            self.cancel_task(task_id)
        
        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


def is_process_pool_available() -> bool:
    """Check if process pool functionality is available."""
    # multiprocessing and concurrent.futures are built-in Python modules
    import multiprocessing
    import concurrent.futures
    return True
