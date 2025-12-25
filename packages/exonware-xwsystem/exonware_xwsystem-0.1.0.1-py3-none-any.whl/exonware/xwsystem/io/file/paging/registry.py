#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/paging/registry.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Paging strategy registry - LIKE CodecRegistry!

Enables pluggable, extensible paging algorithms.

Priority 1 (Security): Safe strategy selection
Priority 2 (Usability): Auto-detection of best strategy
Priority 3 (Maintainability): Clean registry pattern
Priority 4 (Performance): Fast strategy lookup
Priority 5 (Extensibility): Easy to add new strategies
"""

from typing import Optional
from ...contracts import IPagingStrategy
from ...defs import PagingMode

__all__ = [
    'PagingStrategyRegistry',
    'get_global_paging_registry',
    'register_paging_strategy',
    'get_paging_strategy',
    'auto_detect_paging_strategy',
]


class PagingStrategyRegistry:
    """
    Registry for paging strategies (LIKE CodecRegistry!).
    
    Manages available paging strategies and enables auto-detection.
    
    Examples:
        >>> registry = PagingStrategyRegistry()
        >>> registry.register(BytePagingStrategy)
        >>> strategy = registry.get("byte")
        >>> strategy = registry.auto_detect(mode='rb')  # Returns BytePagingStrategy
    """
    
    def __init__(self):
        """Initialize registry."""
        self._strategies: dict[str, type[IPagingStrategy]] = {}
        self._instances: dict[str, IPagingStrategy] = {}
    
    def register(self, strategy_class: type[IPagingStrategy]) -> None:
        """
        Register a paging strategy.
        
        Args:
            strategy_class: Strategy class to register
        
        Example:
            >>> registry.register(BytePagingStrategy)
        """
        # Instantiate to get strategy_id
        instance = strategy_class()
        strategy_id = instance.strategy_id
        
        self._strategies[strategy_id] = strategy_class
        self._instances[strategy_id] = instance
    
    def get(self, strategy_id: str) -> Optional[IPagingStrategy]:
        """
        Get strategy by ID.
        
        Args:
            strategy_id: Strategy identifier (byte, line, record)
        
        Returns:
            Strategy instance or None
        
        Example:
            >>> strategy = registry.get("byte")
        """
        return self._instances.get(strategy_id)
    
    def auto_detect(self, mode: str = 'rb', **hints) -> IPagingStrategy:
        """
        Auto-detect best paging strategy.
        
        Args:
            mode: File mode ('rb' → byte, 'r' → line)
            **hints: Additional hints (file_extension, content_type, etc.)
        
        Returns:
            Best strategy for the given mode
        
        Example:
            >>> strategy = registry.auto_detect(mode='rb')  # Returns BytePagingStrategy
            >>> strategy = registry.auto_detect(mode='r')   # Returns LinePagingStrategy
        """
        # Simple auto-detection logic
        if 'b' in mode:
            # Binary mode → byte paging
            return self.get("byte") or self.get("line")  # Fallback
        else:
            # Text mode → line paging
            return self.get("line") or self.get("byte")  # Fallback
    
    def list_strategies(self) -> list[str]:
        """List all registered strategy IDs."""
        return list(self._strategies.keys())


# Global registry instance
_global_paging_registry: Optional[PagingStrategyRegistry] = None


def get_global_paging_registry() -> PagingStrategyRegistry:
    """Get or create global paging strategy registry."""
    global _global_paging_registry
    if _global_paging_registry is None:
        _global_paging_registry = PagingStrategyRegistry()
        
        # Register default strategies
        from .byte_paging import BytePagingStrategy
        from .line_paging import LinePagingStrategy
        from .record_paging import RecordPagingStrategy
        
        _global_paging_registry.register(BytePagingStrategy)
        _global_paging_registry.register(LinePagingStrategy)
        _global_paging_registry.register(RecordPagingStrategy)
    
    return _global_paging_registry


def register_paging_strategy(strategy_class):
    """
    Decorator to register a paging strategy.
    
    Example:
        >>> @register_paging_strategy
        ... class MyCustomPaging:
        ...     @property
        ...     def strategy_id(self): return "custom"
        ...     def read_page(self, ...): ...
    """
    get_global_paging_registry().register(strategy_class)
    return strategy_class


def get_paging_strategy(strategy_id: str) -> Optional[IPagingStrategy]:
    """
    Get paging strategy by ID.
    
    Args:
        strategy_id: Strategy identifier
    
    Returns:
        Strategy instance or None
    
    Example:
        >>> strategy = get_paging_strategy("byte")
    """
    return get_global_paging_registry().get(strategy_id)


def auto_detect_paging_strategy(mode: str = 'rb', **hints) -> IPagingStrategy:
    """
    Auto-detect best paging strategy.
    
    Args:
        mode: File mode
        **hints: Additional hints
    
    Returns:
        Best strategy for the mode
    
    Example:
        >>> strategy = auto_detect_paging_strategy(mode='r')
    """
    return get_global_paging_registry().auto_detect(mode, **hints)

