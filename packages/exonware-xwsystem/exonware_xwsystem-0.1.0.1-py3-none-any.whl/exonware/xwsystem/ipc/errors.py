#exonware/xwsystem/ipc/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

IPC module errors - exception classes for inter-process communication functionality.
"""


class IPCError(Exception):
    """Base exception for IPC errors."""
    pass


class MessageQueueError(IPCError):
    """Raised when message queue operation fails."""
    pass


class QueueFullError(MessageQueueError):
    """Raised when message queue is full."""
    pass


class QueueEmptyError(MessageQueueError):
    """Raised when message queue is empty."""
    pass


class QueueTimeoutError(MessageQueueError):
    """Raised when message queue operation times out."""
    pass


class PipeError(IPCError):
    """Raised when pipe operation fails."""
    pass


class PipeClosedError(PipeError):
    """Raised when pipe is closed."""
    pass


class PipeBrokenError(PipeError):
    """Raised when pipe is broken."""
    pass


class SharedMemoryError(IPCError):
    """Raised when shared memory operation fails."""
    pass


class SharedMemoryNotFoundError(SharedMemoryError):
    """Raised when shared memory segment is not found."""
    pass


class SharedMemoryPermissionError(SharedMemoryError):
    """Raised when shared memory permission is denied."""
    pass


class SharedMemorySizeError(SharedMemoryError):
    """Raised when shared memory size is invalid."""
    pass


class ProcessError(IPCError):
    """Raised when process operation fails."""
    pass


class ProcessNotFoundError(ProcessError):
    """Raised when process is not found."""
    pass


class ProcessStartError(ProcessError):
    """Raised when process start fails."""
    pass


class ProcessStopError(ProcessError):
    """Raised when process stop fails."""
    pass


class ProcessTimeoutError(ProcessError):
    """Raised when process operation times out."""
    pass


class ProcessPoolError(IPCError):
    """Raised when process pool operation fails."""
    pass


class ProcessPoolFullError(ProcessPoolError):
    """Raised when process pool is full."""
    pass


class ProcessPoolEmptyError(ProcessPoolError):
    """Raised when process pool is empty."""
    pass


class ProcessPoolShutdownError(ProcessPoolError):
    """Raised when process pool shutdown fails."""
    pass
