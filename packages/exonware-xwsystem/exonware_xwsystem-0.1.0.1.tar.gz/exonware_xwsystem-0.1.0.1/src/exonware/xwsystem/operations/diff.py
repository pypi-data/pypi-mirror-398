#!/usr/bin/env python3
"""
#exonware/xwsystem/src/exonware/xwsystem/operations/diff.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Diff operations implementation.
"""

import threading
from typing import Any, Optional, Union
from .base import IDiffOperation, DiffError
from .defs import DiffMode, DiffResult
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.operations.diff")


class DiffOperation(IDiffOperation):
    """Thread-safe diff operation implementation."""
    
    def __init__(self):
        self._lock = threading.RLock()
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute diff operation."""
        if len(args) < 2:
            raise DiffError("Diff requires original and modified data")
        
        original, modified = args[0], args[1]
        mode = kwargs.get('mode', DiffMode.FULL)
        
        return self.diff(original, modified, mode)
    
    def diff(self, original: Any, modified: Any, mode: DiffMode = DiffMode.FULL) -> DiffResult:
        """
        Generate diff between original and modified data.
        
        Args:
            original: Original data structure
            modified: Modified data structure
            mode: Diff mode to use
            
        Returns:
            DiffResult with operations and statistics
            
        Raises:
            DiffError: If diff operation fails
        """
        with self._lock:
            try:
                operations = []
                paths_changed = []
                
                if mode == DiffMode.STRUCTURAL:
                    operations = self._structural_diff(original, modified, "", operations, paths_changed)
                elif mode == DiffMode.CONTENT:
                    operations = self._content_diff(original, modified, "", operations, paths_changed)
                elif mode == DiffMode.FULL:
                    operations = self._full_diff(original, modified, "", operations, paths_changed)
                else:
                    raise DiffError(f"Unknown diff mode: {mode}")
                
                return DiffResult(
                    operations=operations,
                    mode=mode,
                    paths_changed=paths_changed,
                    total_changes=len(operations)
                )
                
            except Exception as e:
                raise DiffError(f"Diff operation failed: {e}", "diff")
    
    def _structural_diff(self, original: Any, modified: Any, path: str, 
                        operations: list, paths_changed: list) -> list:
        """Compare structure only (keys, types)."""
        # Compare types
        if type(original) != type(modified):
            operations.append({
                "op": "replace",
                "path": path or "/",
                "value": modified,
                "old_value": original,
                "reason": "type_changed"
            })
            paths_changed.append(path or "/")
            return operations
        
        # Compare dict keys
        if isinstance(original, dict) and isinstance(modified, dict):
            all_keys = set(original.keys()) | set(modified.keys())
            
            for key in all_keys:
                key_path = f"{path}/{key}" if path else f"/{key}"
                
                if key not in original:
                    operations.append({
                        "op": "add",
                        "path": key_path,
                        "value": modified[key],
                        "reason": "key_added"
                    })
                    paths_changed.append(key_path)
                elif key not in modified:
                    operations.append({
                        "op": "remove",
                        "path": key_path,
                        "old_value": original[key],
                        "reason": "key_removed"
                    })
                    paths_changed.append(key_path)
                else:
                    # Recurse for nested structures
                    self._structural_diff(original[key], modified[key], key_path, 
                                        operations, paths_changed)
        
        # Compare list lengths
        elif isinstance(original, list) and isinstance(modified, list):
            if len(original) != len(modified):
                operations.append({
                    "op": "replace",
                    "path": path or "/",
                    "value": modified,
                    "old_value": original,
                    "reason": "list_length_changed"
                })
                paths_changed.append(path or "/")
        
        return operations
    
    def _content_diff(self, original: Any, modified: Any, path: str,
                     operations: list, paths_changed: list) -> list:
        """Compare content only (values)."""
        if original != modified:
            operations.append({
                "op": "replace",
                "path": path or "/",
                "value": modified,
                "old_value": original,
                "reason": "value_changed"
            })
            paths_changed.append(path or "/")
        
        return operations
    
    def _full_diff(self, original: Any, modified: Any, path: str,
                  operations: list, paths_changed: list) -> list:
        """
        Compare both structure and content recursively.
        
        Root cause: Previous implementation didn't recurse properly.
        Fix: Proper recursive comparison of nested structures.
        Priority: Maintainability #3 - Correct, clean implementation
        """
        # Handle type mismatches
        if type(original) != type(modified):
            operations.append({
                "op": "replace",
                "path": path or "/",
                "value": modified,
                "old_value": original,
                "reason": "type_changed"
            })
            paths_changed.append(path or "/")
            return operations
        
        # Compare dictionaries recursively
        if isinstance(original, dict) and isinstance(modified, dict):
            all_keys = set(original.keys()) | set(modified.keys())
            
            for key in all_keys:
                key_path = f"{path}/{key}" if path else f"/{key}"
                
                if key not in original:
                    operations.append({
                        "op": "add",
                        "path": key_path,
                        "value": modified[key],
                        "reason": "key_added"
                    })
                    paths_changed.append(key_path)
                elif key not in modified:
                    operations.append({
                        "op": "remove",
                        "path": key_path,
                        "old_value": original[key],
                        "reason": "key_removed"
                    })
                    paths_changed.append(key_path)
                else:
                    # Recurse for nested comparison
                    self._full_diff(original[key], modified[key], key_path, 
                                  operations, paths_changed)
        
        # Compare lists
        elif isinstance(original, list) and isinstance(modified, list):
            if original != modified:
                operations.append({
                    "op": "replace",
                    "path": path or "/",
                    "value": modified,
                    "old_value": original,
                    "reason": "list_changed"
                })
                paths_changed.append(path or "/")
        
        # Compare scalars
        elif original != modified:
            operations.append({
                "op": "replace",
                "path": path or "/",
                "value": modified,
                "old_value": original,
                "reason": "value_changed"
            })
            paths_changed.append(path or "/")
        
        return operations


# Convenience function
def generate_diff(original: Any, modified: Any, mode: DiffMode = DiffMode.FULL) -> DiffResult:
    """
    Convenience function for diff operations.
    
    Args:
        original: Original data structure
        modified: Modified data structure
        mode: Diff mode to use
        
    Returns:
        DiffResult with operations and statistics
    """
    differ = DiffOperation()
    return differ.diff(original, modified, mode)


__all__ = [
    "DiffOperation",
    "generate_diff",
]
