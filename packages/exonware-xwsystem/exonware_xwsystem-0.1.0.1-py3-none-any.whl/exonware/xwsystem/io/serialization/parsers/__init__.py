"""JSON Parser abstraction layer for pluggable performance optimizations.

This module provides a pluggable parser system that allows switching between
different JSON parsing implementations (stdlib, orjson, etc.) for performance.
"""

from .base import IJsonParser
from .registry import get_parser, get_best_available_parser, register_parser

__all__ = [
    'IJsonParser',
    'get_parser',
    'get_best_available_parser',
    'register_parser',
]
