#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 26, 2025

Universal operations library for data manipulation.
"""

from typing import Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.operations")


class MergeStrategy(Enum):
    """Merge strategies for data operations."""
    DEEP = "deep"           # Recursive merge (default)
    SHALLOW = "shallow"     # Top-level only
    OVERWRITE = "overwrite" # Replace entirely
    APPEND = "append"       # Append lists instead of replacing
    UNIQUE = "unique"       # Merge lists with uniqueness


class DiffMode(Enum):
    """Diff operation modes."""
    STRUCTURAL = "structural"  # Compare structure only
    CONTENT = "content"        # Compare content only
    FULL = "full"              # Compare both structure and content


class PatchOperation(Enum):
    """JSON Patch operation types."""
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    MOVE = "move"
    COPY = "copy"
    TEST = "test"


@dataclass
class DiffResult:
    """Result of a diff operation."""
    operations: list[dict[str, Any]]
    mode: DiffMode
    paths_changed: list[str]
    total_changes: int


@dataclass
class PatchResult:
    """Result of a patch operation."""
    success: bool
    operations_applied: int
    errors: list[str]
    result: Any


# Import from submodules
from .defs import MergeStrategy, DiffMode, PatchOperation, DiffResult, PatchResult
from .base import (
    OperationError, MergeError, DiffError, PatchError,
    IOperation, IMergeOperation, IDiffOperation, IPatchOperation
)
from .merge import MergeOperation, deep_merge
from .diff import DiffOperation, generate_diff
from .patch import PatchOperationImpl, apply_patch

__all__ = [
    # Enums and data classes
    "MergeStrategy",
    "DiffMode", 
    "PatchOperation",
    "DiffResult",
    "PatchResult",
    # Exceptions
    "OperationError",
    "MergeError", 
    "DiffError",
    "PatchError",
    # Interfaces
    "IOperation",
    "IMergeOperation",
    "IDiffOperation",
    "IPatchOperation",
    # Operations
    "MergeOperation",
    "DiffOperation",
    "PatchOperationImpl",
    # Convenience functions
    "deep_merge",
    "generate_diff",
    "apply_patch",
]