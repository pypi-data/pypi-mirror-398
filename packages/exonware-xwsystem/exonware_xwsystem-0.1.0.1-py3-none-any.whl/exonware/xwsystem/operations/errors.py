"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Operations Errors

Exception classes for data operations.
"""


class OperationError(Exception):
    """Base exception for operation errors."""
    pass


class MergeError(OperationError):
    """Exception raised during merge operations."""
    pass


class DiffError(OperationError):
    """Exception raised during diff operations."""
    pass


class PatchError(OperationError):
    """Exception raised during patch operations."""
    pass


class InvalidPathError(PatchError):
    """Exception raised when a path is invalid."""
    pass


class InvalidOperationError(OperationError):
    """Exception raised when an operation is invalid."""
    pass

