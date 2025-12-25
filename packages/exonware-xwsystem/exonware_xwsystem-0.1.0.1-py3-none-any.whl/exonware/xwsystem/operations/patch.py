#!/usr/bin/env python3
"""
#exonware/xwsystem/src/exonware/xwsystem/operations/patch.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Patch operations implementation (RFC 6902 JSON Patch).
"""

import threading
import copy
from typing import Any, Optional, Union
from .base import IPatchOperation, PatchError
from .defs import PatchOperation, PatchResult
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.operations.patch")


class PatchOperationImpl(IPatchOperation):
    """Thread-safe patch operation implementation."""
    
    def __init__(self):
        self._lock = threading.RLock()
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute patch operation."""
        if len(args) < 2:
            raise PatchError("Patch requires data and operations")
        
        data, operations = args[0], args[1]
        
        return self.apply_patch(data, operations)
    
    def apply_patch(self, data: Any, operations: list[dict[str, Any]]) -> PatchResult:
        """
        Apply patch operations to data (RFC 6902 JSON Patch).
        
        Args:
            data: Data structure to patch
            operations: List of patch operations
            
        Returns:
            PatchResult with result and statistics
            
        Raises:
            PatchError: If patch operation fails
        """
        with self._lock:
            try:
                result = copy.deepcopy(data)
                operations_applied = 0
                errors = []
                
                for i, operation in enumerate(operations):
                    try:
                        op_type = operation.get("op")
                        path = operation.get("path", "/")
                        
                        if op_type == "add":
                            result = self._apply_add(result, path, operation.get("value"))
                            operations_applied += 1
                        elif op_type == "remove":
                            result = self._apply_remove(result, path)
                            operations_applied += 1
                        elif op_type == "replace":
                            result = self._apply_replace(result, path, operation.get("value"))
                            operations_applied += 1
                        elif op_type == "move":
                            from_path = operation.get("from")
                            result = self._apply_move(result, from_path, path)
                            operations_applied += 1
                        elif op_type == "copy":
                            from_path = operation.get("from")
                            result = self._apply_copy(result, from_path, path)
                            operations_applied += 1
                        elif op_type == "test":
                            self._apply_test(result, path, operation.get("value"))
                            operations_applied += 1
                        else:
                            errors.append(f"Operation {i}: Unknown operation type: {op_type}")
                    
                    except Exception as e:
                        errors.append(f"Operation {i}: {str(e)}")
                
                return PatchResult(
                    success=len(errors) == 0,
                    operations_applied=operations_applied,
                    errors=errors,
                    result=result
                )
                
            except Exception as e:
                raise PatchError(f"Patch operation failed: {e}", "patch")
    
    def _parse_path(self, path: str) -> list[str]:
        """Parse JSON Pointer path."""
        if path == "/":
            return []
        
        # Remove leading slash and split
        parts = path.lstrip("/").split("/")
        
        # Unescape special characters
        return [part.replace("~1", "/").replace("~0", "~") for part in parts]
    
    def _get_value(self, data: Any, path: str) -> Any:
        """Get value at path."""
        parts = self._parse_path(path)
        
        current = data
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    raise PatchError(f"Path not found: {path}")
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    raise PatchError(f"Invalid array index: {part}")
            else:
                raise PatchError(f"Cannot navigate path: {path}")
        
        return current
    
    def _set_value(self, data: Any, path: str, value: Any) -> Any:
        """Set value at path."""
        parts = self._parse_path(path)
        
        if not parts:
            return value
        
        current = data
        for i, part in enumerate(parts[:-1]):
            if isinstance(current, dict):
                if part not in current:
                    # Create intermediate structure
                    next_part = parts[i + 1]
                    current[part] = [] if next_part.isdigit() else {}
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    raise PatchError(f"Invalid array index: {part}")
        
        # Set the final value
        last_part = parts[-1]
        if isinstance(current, dict):
            current[last_part] = value
        elif isinstance(current, list):
            try:
                index = int(last_part)
                if index == len(current):
                    current.append(value)
                else:
                    current[index] = value
            except ValueError:
                raise PatchError(f"Invalid array index: {last_part}")
        
        return data
    
    def _apply_add(self, data: Any, path: str, value: Any) -> Any:
        """Apply add operation."""
        return self._set_value(data, path, value)
    
    def _apply_remove(self, data: Any, path: str) -> Any:
        """Apply remove operation."""
        parts = self._parse_path(path)
        
        if not parts:
            raise PatchError("Cannot remove root")
        
        current = data
        for part in parts[:-1]:
            if isinstance(current, dict):
                current = current[part]
            elif isinstance(current, list):
                current = current[int(part)]
        
        last_part = parts[-1]
        if isinstance(current, dict):
            del current[last_part]
        elif isinstance(current, list):
            del current[int(last_part)]
        
        return data
    
    def _apply_replace(self, data: Any, path: str, value: Any) -> Any:
        """Apply replace operation."""
        # First remove, then add
        data = self._apply_remove(data, path)
        return self._apply_add(data, path, value)
    
    def _apply_move(self, data: Any, from_path: str, to_path: str) -> Any:
        """Apply move operation."""
        value = self._get_value(data, from_path)
        data = self._apply_remove(data, from_path)
        return self._apply_add(data, to_path, value)
    
    def _apply_copy(self, data: Any, from_path: str, to_path: str) -> Any:
        """Apply copy operation."""
        value = self._get_value(data, from_path)
        return self._apply_add(data, to_path, copy.deepcopy(value))
    
    def _apply_test(self, data: Any, path: str, value: Any) -> None:
        """Apply test operation."""
        current_value = self._get_value(data, path)
        if current_value != value:
            raise PatchError(f"Test failed at {path}: expected {value}, got {current_value}")


# Convenience function
def apply_patch(data: Any, operations: list[dict[str, Any]]) -> PatchResult:
    """
    Convenience function for patch operations.
    
    Args:
        data: Data structure to patch
        operations: List of patch operations
        
    Returns:
        PatchResult with result and statistics
    """
    patcher = PatchOperationImpl()
    return patcher.apply_patch(data, operations)


__all__ = [
    "PatchOperationImpl",
    "apply_patch",
]
