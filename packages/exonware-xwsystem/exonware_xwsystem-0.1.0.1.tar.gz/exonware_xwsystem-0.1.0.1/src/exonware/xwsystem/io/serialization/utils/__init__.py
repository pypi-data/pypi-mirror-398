#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/serialization/utils/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 9, 2025

Serialization utilities module.
"""

from .path_ops import (
    PathOperationError,
    validate_json_pointer,
    parse_json_pointer,
    get_value_by_path,
    set_value_by_path,
    validate_path_security,
    normalize_path,
)

__all__ = [
    "PathOperationError",
    "validate_json_pointer",
    "parse_json_pointer",
    "get_value_by_path",
    "set_value_by_path",
    "validate_path_security",
    "normalize_path",
]

