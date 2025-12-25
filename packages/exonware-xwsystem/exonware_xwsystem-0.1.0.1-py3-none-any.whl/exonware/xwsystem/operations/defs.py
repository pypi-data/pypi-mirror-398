#!/usr/bin/env python3
"""
#exonware/xwsystem/src/exonware/xwsystem/operations/defs.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Operations definitions and data structures.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any


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
    """JSON Patch operation types (RFC 6902)."""
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


__all__ = [
    "MergeStrategy",
    "DiffMode",
    "PatchOperation",
    "DiffResult",
    "PatchResult",
]
