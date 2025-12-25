#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 26, 2025

Merge operations implementation.
"""

import threading
from typing import Any, Optional, Union
from .base import IMergeOperation, MergeError
from .defs import MergeStrategy
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.operations.merge")


class MergeOperation(IMergeOperation):
    """Thread-safe merge operation implementation."""
    
    def __init__(self):
        self._lock = threading.RLock()
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute merge operation."""
        if len(args) < 2:
            raise MergeError("Merge requires at least target and source")
        
        target, source = args[0], args[1]
        strategy = kwargs.get('strategy', MergeStrategy.DEEP)
        
        return self.merge(target, source, strategy)
    
    def merge(self, target: Any, source: Any, strategy: MergeStrategy = MergeStrategy.DEEP) -> Any:
        """
        Merge source into target using specified strategy.
        
        Args:
            target: Target data structure
            source: Source data structure to merge
            strategy: Merge strategy to use
            
        Returns:
            Merged data structure
            
        Raises:
            MergeError: If merge operation fails
        """
        with self._lock:
            try:
                if strategy == MergeStrategy.DEEP:
                    return self._deep_merge(target, source)
                elif strategy == MergeStrategy.SHALLOW:
                    return self._shallow_merge(target, source)
                elif strategy == MergeStrategy.OVERWRITE:
                    return self._overwrite_merge(target, source)
                elif strategy == MergeStrategy.APPEND:
                    return self._append_merge(target, source)
                elif strategy == MergeStrategy.UNIQUE:
                    return self._unique_merge(target, source)
                else:
                    raise MergeError(f"Unknown merge strategy: {strategy}")
                    
            except Exception as e:
                raise MergeError(f"Merge operation failed: {e}", "merge")
    
    def _deep_merge(self, target: Any, source: Any) -> Any:
        """Deep recursive merge."""
        if not isinstance(target, dict) or not isinstance(source, dict):
            return source
        
        result = target.copy()
        
        for key, value in source.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _shallow_merge(self, target: Any, source: Any) -> Any:
        """Shallow merge (top-level only)."""
        if not isinstance(target, dict) or not isinstance(source, dict):
            return source
        
        result = target.copy()
        result.update(source)
        return result
    
    def _overwrite_merge(self, target: Any, source: Any) -> Any:
        """Overwrite merge (replace entirely)."""
        return source
    
    def _append_merge(self, target: Any, source: Any) -> Any:
        """Append merge (append lists instead of replacing)."""
        if isinstance(target, list) and isinstance(source, list):
            return target + source
        elif isinstance(target, dict) and isinstance(source, dict):
            result = target.copy()
            for key, value in source.items():
                if key in result and isinstance(result[key], list) and isinstance(value, list):
                    result[key] = result[key] + value
                else:
                    result[key] = value
            return result
        else:
            return source
    
    def _unique_merge(self, target: Any, source: Any) -> Any:
        """Unique merge (merge lists with uniqueness)."""
        if isinstance(target, list) and isinstance(source, list):
            seen = set()
            result = []
            
            # Add items from target first
            for item in target:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            
            # Add unique items from source
            for item in source:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            
            return result
        elif isinstance(target, dict) and isinstance(source, dict):
            result = target.copy()
            for key, value in source.items():
                if key in result and isinstance(result[key], list) and isinstance(value, list):
                    result[key] = self._unique_merge(result[key], value)
                else:
                    result[key] = value
            return result
        else:
            return source


# Convenience function
def deep_merge(target: Any, source: Any, strategy: MergeStrategy = MergeStrategy.DEEP) -> Any:
    """
    Convenience function for deep merge operations.
    
    Args:
        target: Target data structure
        source: Source data structure to merge
        strategy: Merge strategy to use
        
    Returns:
        Merged data structure
    """
    merger = MergeOperation()
    return merger.merge(target, source, strategy)


__all__ = [
    "MergeOperation",
    "deep_merge",
]