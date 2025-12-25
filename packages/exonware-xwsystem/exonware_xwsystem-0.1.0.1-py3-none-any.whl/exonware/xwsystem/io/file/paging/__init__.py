#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/paging/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Modular paging system with strategy pattern.

Like codec system but for paging algorithms!

Priority 1 (Security): Safe paging operations
Priority 2 (Usability): Auto-detection of best strategy
Priority 3 (Maintainability): Pluggable strategies
Priority 4 (Performance): Efficient strategy selection
Priority 5 (Extensibility): Easy to add new strategies
"""

from .byte_paging import BytePagingStrategy
from .line_paging import LinePagingStrategy
from .record_paging import RecordPagingStrategy
from .registry import (
    PagingStrategyRegistry,
    get_global_paging_registry,
    register_paging_strategy,
    get_paging_strategy,
    auto_detect_paging_strategy,
)

__all__ = [
    # Strategies
    "BytePagingStrategy",
    "LinePagingStrategy",
    "RecordPagingStrategy",
    
    # Registry
    "PagingStrategyRegistry",
    "get_global_paging_registry",
    "register_paging_strategy",
    "get_paging_strategy",
    "auto_detect_paging_strategy",
]

