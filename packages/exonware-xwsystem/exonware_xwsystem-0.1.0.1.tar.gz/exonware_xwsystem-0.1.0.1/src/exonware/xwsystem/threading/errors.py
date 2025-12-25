#exonware/xwsystem/threading/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Threading module errors - exception classes for threading functionality.
"""


class ThreadingError(Exception):
    """Base exception for threading errors."""
    pass


class ThreadError(ThreadingError):
    """Raised when thread operation fails."""
    pass


class ThreadCreationError(ThreadError):
    """Raised when thread creation fails."""
    pass


class ThreadStartError(ThreadError):
    """Raised when thread start fails."""
    pass


class ThreadStopError(ThreadError):
    """Raised when thread stop fails."""
    pass


class ThreadJoinError(ThreadError):
    """Raised when thread join fails."""
    pass


class ThreadTimeoutError(ThreadError):
    """Raised when thread operation times out."""
    pass


class LockError(ThreadingError):
    """Raised when lock operation fails."""
    pass


class LockAcquisitionError(LockError):
    """Raised when lock acquisition fails."""
    pass


class LockReleaseError(LockError):
    """Raised when lock release fails."""
    pass


class LockTimeoutError(LockError):
    """Raised when lock operation times out."""
    pass


class DeadlockError(ThreadingError):
    """Raised when deadlock is detected."""
    pass


class RaceConditionError(ThreadingError):
    """Raised when race condition is detected."""
    pass


class AsyncError(ThreadingError):
    """Raised when async operation fails."""
    pass


class AsyncPrimitiveError(AsyncError):
    """Raised when async primitive operation fails."""
    pass


class AsyncTimeoutError(AsyncError):
    """Raised when async operation times out."""
    pass


class SafeFactoryError(ThreadingError):
    """Raised when safe factory operation fails."""
    pass


class ThreadSafetyError(ThreadingError):
    """Raised when thread safety is violated."""
    pass


class ConcurrencyError(ThreadingError):
    """Raised when concurrency operation fails."""
    pass
