"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Operations Contracts

Protocol definitions for data operations.
"""

from typing import Any, Protocol, runtime_checkable
from .defs import MergeStrategy, DiffMode


@runtime_checkable
class IOperation(Protocol):
    """Base protocol for all operations."""
    
    def validate(self, data: Any) -> bool:
        """Validate input data."""
        ...


@runtime_checkable
class IMerge(Protocol):
    """Protocol for merge operations."""
    
    def merge(
        self,
        base: Any,
        other: Any,
        strategy: MergeStrategy = MergeStrategy.DEEP
    ) -> Any:
        """Merge two data structures."""
        ...


@runtime_checkable
class IDiff(Protocol):
    """Protocol for diff operations."""
    
    def diff(
        self,
        old: Any,
        new: Any,
        mode: DiffMode = DiffMode.STANDARD
    ) -> list[dict[str, Any]]:
        """Generate diff between two data structures."""
        ...


@runtime_checkable
class IPatch(Protocol):
    """Protocol for patch operations."""
    
    def patch(
        self,
        data: Any,
        operations: list[dict[str, Any]]
    ) -> Any:
        """Apply patch operations to data."""
        ...

