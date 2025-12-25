#exonware/xwsystem/patterns/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Abstract base classes for XSystem patterns.
"""

from abc import ABC, abstractmethod
from typing import Any

from .contracts import IHandler, IPattern


class AHandler(IHandler[Any]):
    """
    Abstract base class for handlers that work with GenericHandlerFactory.

    This provides a standard interface that handlers should implement.
    """

    @abstractmethod
    def handle(self, data: Any) -> Any:
        """
        Handle the given data.

        Args:
            data: Data to handle

        Returns:
            Handled data
        """
        pass

    @abstractmethod
    def can_handle(self, data: Any) -> bool:
        """
        Check if this handler can process the given data.

        Args:
            data: Data to check

        Returns:
            True if handler can process the data
        """
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """
        Get the priority of this handler (higher = more important).

        Returns:
            Priority value
        """
        pass

    def process(self, data: Any, **kwargs) -> Any:
        """
        Process the data (convenience method that calls handle).

        Args:
            data: Data to process
            **kwargs: Additional processing options

        Returns:
            Processed data
        """
        return self.handle(data)

    def validate_input(self, data: Any) -> bool:
        """
        Validate input data before processing.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        return True

    def get_supported_formats(self) -> list[str]:
        """
        Get list of formats this handler supports.

        Returns:
            List of supported format names
        """
        return []


class BasePattern(IPattern):
    """Base pattern implementation."""
    
    def __init__(self, name: str = "base_pattern"):
        """Initialize the pattern.
        
        Args:
            name: Pattern name
        """
        self._name = name
        self._enabled = True
    
    @property
    def name(self) -> str:
        """Get pattern name."""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """Check if pattern is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable the pattern."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the pattern."""
        self._enabled = False
    
    def apply(self, data: Any) -> Any:
        """Apply the pattern to data.
        
        Args:
            data: Data to apply pattern to
            
        Returns:
            Processed data
        """
        if not self._enabled:
            return data
        return self._process(data)
    
    def _process(self, data: Any) -> Any:
        """Process data with the pattern.
        
        Args:
            data: Data to process
            
        Returns:
            Processed data
        """
        # Base implementation - can be overridden
        return data
    
    def validate(self, data: Any) -> bool:
        """Validate data for pattern application.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid
        """
        return True
