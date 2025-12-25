#exonware/xwsystem/ipc/async_fabric.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 09-Nov-2025

Async Process Fabric
====================

High-level async orchestration facade that coordinates the IPC building blocks:
process pools, message queues, and shared memory managers.  The fabric exposes a
single context-managed session that provides consistent lifecycle management and
typed helpers for task submission, result streaming, queue operations, and
shared-memory provisioning.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Iterable,
    Optional,
    Sequence,
    Union,
)

from .process_pool import AsyncProcessPool
from .message_queue import AsyncMessageQueue
from .shared_memory import SharedData, SharedMemoryManager

logger = logging.getLogger("xwsystem.ipc.async_fabric")

CallableRef = Union[str, Callable[..., Any]]
TaskId = str


def _resolve_callable(callable_or_path: CallableRef) -> Callable[..., Any]:
    """
    Resolve a dotted-path string to a callable, or return the callable directly.

    Args:
        callable_or_path: Callable object or dotted import path.

    Returns:
        A callable ready to be executed inside the process pool.
    """
    if callable(callable_or_path):
        return callable_or_path

    if not isinstance(callable_or_path, str) or "." not in callable_or_path:
        raise ValueError(f"Callable reference must be a dotted path string: {callable_or_path!r}")

    module_path, _, attr_name = callable_or_path.rpartition(".")
    if not module_path or not attr_name:
        raise ValueError(f"Invalid callable path: {callable_or_path!r}")

    module = importlib.import_module(module_path)
    target = getattr(module, attr_name, None)
    if target is None or not callable(target):
        raise TypeError(f"Resolved attribute is not callable: {callable_or_path!r}")

    return target


@dataclass
class FabricConfig:
    """Configuration used when provisioning a fabric session."""

    pool_factory: Callable[..., AsyncProcessPool] = AsyncProcessPool
    queue_factory: Callable[..., AsyncMessageQueue] = AsyncMessageQueue
    shared_memory_factory: Callable[..., SharedMemoryManager] = SharedMemoryManager
    pool_kwargs: dict[str, Any] = field(default_factory=dict)
    queue_kwargs: dict[str, Any] = field(default_factory=dict)
    shared_memory_kwargs: dict[str, Any] = field(default_factory=dict)


class AsyncProcessFabric:
    """
    High-level orchestration facade for IPC subsystems.

    Example:

        fabric = AsyncProcessFabric()

        async with fabric.session() as session:
            task_id = await session.submit("myapp.jobs.transform", payload)
            async for result in session.iter_results(task_id):
                consume(result)
            await session.publish("events.ingest", {"status": "done"})
            event = await session.consume("events.ingest")
    """

    def __init__(
        self,
        *,
        pool_factory: Optional[Callable[..., AsyncProcessPool]] = None,
        queue_factory: Optional[Callable[..., AsyncMessageQueue]] = None,
        shared_memory_factory: Optional[Callable[..., SharedMemoryManager]] = None,
        pool_kwargs: Optional[dict[str, Any]] = None,
        queue_kwargs: Optional[dict[str, Any]] = None,
        shared_memory_kwargs: Optional[dict[str, Any]] = None,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:
        self._config = FabricConfig(
            pool_factory=pool_factory or AsyncProcessPool,
            queue_factory=queue_factory or AsyncMessageQueue,
            shared_memory_factory=shared_memory_factory or SharedMemoryManager,
            pool_kwargs=pool_kwargs or {},
            queue_kwargs=queue_kwargs or {},
            shared_memory_kwargs=shared_memory_kwargs or {},
        )
        self._logger = logger_instance or logger

    @asynccontextmanager
    async def session(self) -> AsyncIterator["AsyncProcessFabricSession"]:
        """
        Provision an async session that owns the pooled IPC resources.

        Yields:
            AsyncProcessFabricSession that manages pool, queue, and shared memory within
            an async context block.
        """
        session = AsyncProcessFabricSession(self._config, self._logger)
        await session.__aenter__()
        try:
            yield session
        finally:
            await session.__aexit__(None, None, None)


class AsyncProcessFabricSession:
    """Session object returned by `AsyncProcessFabric.session()`."""

    def __init__(self, config: FabricConfig, logger_instance: logging.Logger) -> None:
        self._config = config
        self._logger = logger_instance
        self._pool: Optional[AsyncProcessPool] = None
        self._queue: Optional[AsyncMessageQueue] = None
        self._shared_memory: Optional[SharedMemoryManager] = None
        self._active_task_ids: set[TaskId] = set()

    async def __aenter__(self) -> "AsyncProcessFabricSession":
        self._logger.debug("Initializing AsyncProcessFabric session")
        self._pool = self._config.pool_factory(**self._config.pool_kwargs)
        self._queue = self._config.queue_factory(**self._config.queue_kwargs)
        self._shared_memory = self._config.shared_memory_factory(**self._config.shared_memory_kwargs)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._logger.debug("Tearing down AsyncProcessFabric session")
        try:
            if self._pool is not None:
                await self._pool.shutdown()
        finally:
            if self._queue is not None:
                await self._queue.shutdown()
            if self._shared_memory is not None:
                self._shared_memory.cleanup_all()
        self._active_task_ids.clear()

    # --------------------------------------------------------------------- #
    # Process pool orchestration
    # --------------------------------------------------------------------- #

    async def submit(
        self,
        fn: CallableRef,
        *args: Any,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> TaskId:
        """
        Submit a callable (or dotted-path string) to the process pool.

        Args:
            fn: Callable reference or dotted-path string.
            *args: Positional arguments forwarded to the callable.
            task_id: Optional explicit task identifier.
            **kwargs: Keyword arguments forwarded to the callable.

        Returns:
            Task identifier issued by the async process pool.
        """
        if self._pool is None:
            raise RuntimeError("Process pool not available. Did you forget to use the session context?")

        callable_fn = _resolve_callable(fn)
        task_identifier = await self._pool.submit(callable_fn, *args, task_id=task_id, **kwargs)
        self._active_task_ids.add(task_identifier)
        self._logger.debug("Submitted task %s to process pool", task_identifier)
        return task_identifier

    async def gather_results(
        self,
        task_ids: Optional[Sequence[TaskId]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> Sequence[Any]:
        """
        Collect results for the provided task identifiers.

        Args:
            task_ids: Optional explicit list of task IDs. Defaults to all active tasks.
            timeout: Optional timeout in seconds applied per task.

        Returns:
            List of task results (order follows the provided task_ids).
        """
        if self._pool is None:
            raise RuntimeError("Process pool not available")

        ids = list(task_ids or self._active_task_ids)
        results = []
        for task_id in ids:
            try:
                result = await self._pool.get_result(task_id, timeout=timeout)
                results.append(result)
            finally:
                self._active_task_ids.discard(task_id)
        return results

    async def iter_results(
        self,
        task_ids: Union[TaskId, Sequence[TaskId]],
        *,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[Any]:
        """
        Async iterator yielding results as they are retrieved from the pool.

        Args:
            task_ids: Single task ID or sequence of IDs to stream.
            timeout: Optional timeout per task.
        """
        if isinstance(task_ids, (str, bytes)):
            task_id_list: Iterable[TaskId] = [task_ids]  # type: ignore[assignment]
        else:
            task_id_list = task_ids

        for task_id in task_id_list:
            result = await self._pool.get_result(task_id, timeout=timeout)  # type: ignore[arg-type]
            self._active_task_ids.discard(task_id)
            yield result

    def cancel(self, task_id: TaskId) -> bool:
        """Attempt to cancel an active task."""
        if self._pool is None:
            raise RuntimeError("Process pool not available")

        cancelled = self._pool.cancel_task(task_id)
        if cancelled:
            self._active_task_ids.discard(task_id)
        return cancelled

    # --------------------------------------------------------------------- #
    # Message queue facade
    # --------------------------------------------------------------------- #

    async def publish(self, channel: str, message: Any, *, timeout: Optional[float] = None) -> bool:
        """
        Publish a message to the async queue.

        Args:
            channel: Logical channel name (currently informational, reserved for sharding).
            message: Payload to enqueue.
            timeout: Optional timeout when queue is full.
        """
        if self._queue is None:
            raise RuntimeError("Message queue not available")

        # Channel support reserved for future sharding, currently single queue.
        return await self._queue.put({"channel": channel, "payload": message}, timeout=timeout)

    async def consume(self, channel: Optional[str] = None, *, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Consume a message from the async queue.

        Args:
            channel: Currently informational. When provided, only messages from the
                     matching channel are returned (others are re-queued).
            timeout: Optional timeout when waiting for messages.
        """
        if self._queue is None:
            raise RuntimeError("Message queue not available")

        # Simple implementation for single-queue usage. When a channel is provided we
        # loop until matching payload is found or timeout elapses.
        if channel is None:
            envelope = await self._queue.get(timeout=timeout)
            return None if envelope is None else envelope.get("payload")

        deadline = None if timeout is None else (asyncio.get_event_loop().time() + timeout)
        buffer: list[dict[str, Any]] = []
        while True:
            remaining = None if deadline is None else max(0.0, deadline - asyncio.get_event_loop().time())
            envelope = await self._queue.get(timeout=remaining)
            if envelope is None:
                # Restore buffered messages before exiting
                for pending in buffer:
                    await self._queue.put(pending, timeout=None)
                return None
            if envelope.get("channel") == channel:
                for pending in buffer:
                    await self._queue.put(pending, timeout=None)
                return envelope.get("payload")
            # Mismatch: requeue without channel filtering to avoid drops.
            buffer.append(envelope)

    # --------------------------------------------------------------------- #
    # Shared memory helpers
    # --------------------------------------------------------------------- #

    def share(self, name: str, *, size: int = 1024 * 1024, create_if_missing: bool = True) -> SharedData:
        """
        Create or retrieve a shared memory segment.

        Args:
            name: Unique segment name.
            size: Default size when creating a new segment.
            create_if_missing: Whether to create the segment when absent.

        Returns:
            SharedData handle.
        """
        if self._shared_memory is None:
            raise RuntimeError("Shared memory manager not available")

        segment = self._shared_memory.get_segment(name)
        if segment or not create_if_missing:
            if segment is None:
                raise ValueError(f"Shared memory segment '{name}' not found")
            return segment

        return self._shared_memory.create_segment(name, size=size)

    def release_shared(self, name: str) -> bool:
        """Remove the specified shared memory segment."""
        if self._shared_memory is None:
            raise RuntimeError("Shared memory manager not available")
        return self._shared_memory.remove_segment(name)

    # --------------------------------------------------------------------- #
    # Introspection
    # --------------------------------------------------------------------- #

    def active_tasks(self) -> Sequence[TaskId]:
        """Return snapshot of currently tracked task IDs."""
        return tuple(self._active_task_ids)

