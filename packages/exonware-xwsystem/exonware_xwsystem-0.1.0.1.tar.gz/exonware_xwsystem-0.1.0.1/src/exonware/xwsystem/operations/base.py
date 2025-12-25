#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 26, 2025

Base classes and contracts for operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from .defs import MergeStrategy, DiffMode, PatchOperation, DiffResult, PatchResult


class OperationError(Exception):
    """Base exception for operation errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message)
        self.operation = operation


class MergeError(OperationError):
    """Error during merge operations."""
    pass


class DiffError(OperationError):
    """Error during diff operations."""
    pass


class PatchError(OperationError):
    """Error during patch operations."""
    pass


class IOperation(ABC):
    """Interface for operations."""
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the operation."""
        pass


class IMergeOperation(IOperation):
    """Interface for merge operations."""
    
    @abstractmethod
    def merge(self, target: Any, source: Any, strategy: MergeStrategy = MergeStrategy.DEEP) -> Any:
        """Merge source into target."""
        pass


class IDiffOperation(IOperation):
    """Interface for diff operations."""
    
    @abstractmethod
    def diff(self, original: Any, modified: Any, mode: DiffMode = DiffMode.FULL) -> DiffResult:
        """Generate diff between original and modified."""
        pass


class IPatchOperation(IOperation):
    """Interface for patch operations."""
    
    @abstractmethod
    def apply_patch(self, data: Any, operations: list[dict[str, Any]]) -> PatchResult:
        """Apply patch operations to data."""
        pass


__all__ = [
    "OperationError",
    "MergeError", 
    "DiffError",
    "PatchError",
    "IOperation",
    "IMergeOperation",
    "IDiffOperation", 
    "IPatchOperation",
]