#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/serialization/utils/path_ops.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 9, 2025

Path operations utilities for serialization formats.

Provides JSONPointer path parsing and manipulation utilities that serializers
can use for path-based operations. Includes path validation for security.
"""

from typing import Any, Union
from pathlib import Path

from ...errors import SerializationError


class PathOperationError(SerializationError):
    """Raised when path operations fail."""
    pass


def validate_json_pointer(path: str) -> bool:
    """
    Validate a JSONPointer path expression.
    
    JSONPointer syntax: /path/to/key or /path/to/0 for arrays
    
    Args:
        path: JSONPointer path to validate
    
    Returns:
        True if path is valid
    
    Raises:
        ValueError: If path is invalid
    
    Example:
        >>> validate_json_pointer("/users/0/name")  # Valid
        True
        >>> validate_json_pointer("invalid")  # Invalid - must start with /
        ValueError
    """
    if not isinstance(path, str):
        raise ValueError(f"Path must be a string, got {type(path)}")
    
    if not path:
        raise ValueError("Path cannot be empty")
    
    # JSONPointer must start with / for non-empty paths
    if path != "/" and not path.startswith("/"):
        raise ValueError(f"JSONPointer path must start with '/', got: {path}")
    
    # Validate path segments (basic validation)
    if path != "/":
        segments = path.strip("/").split("/")
        for segment in segments:
            if not segment and segment != "0":  # Empty segments not allowed except for root
                raise ValueError(f"Invalid path segment in JSONPointer: {path}")
    
    return True


def parse_json_pointer(path: str) -> list[Union[str, int]]:
    """
    Parse a JSONPointer path into a list of keys/indices.
    
    Args:
        path: JSONPointer path (e.g., "/users/0/name")
    
    Returns:
        List of path components (strings for keys, ints for array indices)
    
    Raises:
        ValueError: If path is invalid
    
    Example:
        >>> parse_json_pointer("/users/0/name")
        ['users', 0, 'name']
        >>> parse_json_pointer("/")
        []
    """
    validate_json_pointer(path)
    
    if path == "/":
        return []
    
    segments = path.strip("/").split("/")
    result = []
    
    for segment in segments:
        # Handle escaped characters in JSONPointer
        segment = segment.replace("~1", "/").replace("~0", "~")
        
        # Try to convert to int if it looks like a number (for array indices)
        if segment.isdigit():
            result.append(int(segment))
        else:
            result.append(segment)
    
    return result


def get_value_by_path(data: Any, path: str) -> Any:
    """
    Get value from data structure using JSONPointer path.
    
    Args:
        data: Data structure (dict, list, etc.)
        path: JSONPointer path
    
    Returns:
        Value at the specified path
    
    Raises:
        KeyError: If path doesn't exist
        ValueError: If path is invalid or cannot navigate
    
    Example:
        >>> data = {"users": [{"name": "John"}]}
        >>> get_value_by_path(data, "/users/0/name")
        'John'
    """
    path_parts = parse_json_pointer(path)
    current = data
    
    for part in path_parts:
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(f"Path not found: {path} (missing key: {part})")
            current = current[part]
        elif isinstance(current, list):
            if not isinstance(part, int):
                raise ValueError(f"Cannot use non-integer index '{part}' on list at path: {path}")
            if part < 0 or part >= len(current):
                raise IndexError(f"Index {part} out of range for list at path: {path}")
            current = current[part]
        else:
            raise ValueError(
                f"Cannot navigate path {path}: reached non-container type {type(current)}"
            )
    
    return current


def set_value_by_path(data: Any, path: str, value: Any, create: bool = False) -> None:
    """
    Set value in data structure using JSONPointer path.
    
    Args:
        data: Data structure (dict, list, etc.)
        path: JSONPointer path
        value: Value to set
        create: If True, create missing intermediate paths
    
    Raises:
        KeyError: If path doesn't exist and create=False
        ValueError: If path is invalid or cannot navigate
    
    Example:
        >>> data = {"users": [{"name": "John"}]}
        >>> set_value_by_path(data, "/users/0/name", "Jane")
        >>> data["users"][0]["name"]
        'Jane'
    """
    path_parts = parse_json_pointer(path)
    
    if not path_parts:
        raise ValueError("Cannot set value at root path '/'")
    
    current = data
    
    # Navigate to parent of target
    for i, part in enumerate(path_parts[:-1]):
        if isinstance(current, dict):
            if part not in current:
                if create:
                    # Create intermediate dict
                    current[part] = {}
                else:
                    raise KeyError(f"Path not found: {path} (missing key: {part})")
            current = current[part]
        elif isinstance(current, list):
            if not isinstance(part, int):
                raise ValueError(f"Cannot use non-integer index '{part}' on list")
            if part < 0 or part >= len(current):
                if create:
                    # Extend list if needed
                    while len(current) <= part:
                        current.append({})
                else:
                    raise IndexError(f"Index {part} out of range")
            current = current[part]
        else:
            if create:
                # Convert to dict if possible
                raise ValueError(
                    f"Cannot create path {path}: intermediate value is {type(current)}"
                )
            raise ValueError(
                f"Cannot navigate path {path}: reached non-container type {type(current)}"
            )
    
    # Set the value
    final_key = path_parts[-1]
    if isinstance(current, dict):
        current[final_key] = value
    elif isinstance(current, list):
        if not isinstance(final_key, int):
            raise ValueError(f"Cannot use non-integer index '{final_key}' on list")
        if final_key < 0 or final_key >= len(current):
            if create:
                # Extend list if needed
                while len(current) <= final_key:
                    current.append(None)
            else:
                raise IndexError(f"Index {final_key} out of range")
        current[final_key] = value
    else:
        raise ValueError(
            f"Cannot set value at {path}: parent is {type(current)}, not dict or list"
        )


def validate_path_security(path: str, max_depth: int = 100) -> bool:
    """
    Validate path for security concerns (injection prevention).
    
    Checks for:
    - Path traversal attempts (../, ..\\)
    - Excessive depth
    - Suspicious patterns
    
    Args:
        path: Path to validate
        max_depth: Maximum allowed path depth
    
    Returns:
        True if path is safe
    
    Raises:
        ValueError: If path contains security issues
    
    Note:
        This is a basic security check. Format-specific serializers should
        implement additional validation as needed.
    """
    if not isinstance(path, str):
        raise ValueError(f"Path must be a string, got {type(path)}")
    
    # Check for path traversal
    if ".." in path or "..\\" in path or "../" in path:
        raise ValueError(f"Path traversal detected in path: {path}")
    
    # Check depth
    depth = path.count("/")
    if depth > max_depth:
        raise ValueError(f"Path depth {depth} exceeds maximum {max_depth}: {path}")
    
    # Check for null bytes
    if "\x00" in path:
        raise ValueError(f"Null byte detected in path: {path}")
    
    return True


def normalize_path(path: str) -> str:
    """
    Normalize a JSONPointer path.
    
    Ensures path follows JSONPointer standard format.
    
    Args:
        path: Path to normalize
    
    Returns:
        Normalized path
    
    Example:
        >>> normalize_path("users/0/name")
        '/users/0/name'
        >>> normalize_path("/users/0/name/")
        '/users/0/name'
    """
    if not path:
        return "/"
    
    # Ensure starts with /
    if not path.startswith("/"):
        path = "/" + path
    
    # Remove trailing /
    path = path.rstrip("/")
    
    # Handle root case
    if path == "":
        return "/"
    
    return path

