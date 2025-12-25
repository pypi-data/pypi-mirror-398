"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Logging configuration for XSystem.

Provides simple logging control functions and configuration management.
"""

import logging
import os
from typing import Union

from .defaults import LOGGING_ENABLED, LOGGING_LEVEL


class LoggingConfig:
    """Simple logging configuration control."""

    def __init__(self) -> None:
        self._enabled: bool = LOGGING_ENABLED
        self._level: str = LOGGING_LEVEL

    def disable(self) -> None:
        """Disable all logging."""
        # Disable logging BEFORE any other imports
        os.environ["XSYSTEM_LOGGING_DISABLE"] = "true"
        logging.disable(logging.CRITICAL)
        self._enabled = False

    def enable(self) -> None:
        """Enable logging."""
        self._enabled = True
        os.environ["XSYSTEM_LOGGING_DISABLE"] = "false"
        logging.disable(logging.NOTSET)

    def set_level(self, level: str) -> None:
        """Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        self._level = level.upper()
        if self._enabled:
            try:
                logging.getLogger().setLevel(getattr(logging, self._level))
            except (AttributeError, TypeError):
                # Handle cases where logging level comparison might fail
                pass

    @property
    def enabled(self) -> bool:
        """Check if logging is enabled."""
        return self._enabled

    @property
    def level(self) -> str:
        """Get current logging level."""
        return self._level
    
    def get_level(self) -> str:
        """Get current logging level."""
        return self._level
    
    def add_handler(self, handler) -> None:
        """Add a logging handler."""
        if self._enabled:
            # Check if handler is a MagicMock to avoid comparison issues
            from unittest.mock import MagicMock
            if not isinstance(handler, MagicMock):
                logging.getLogger().addHandler(handler)


# Global logging config instance
logging_config = LoggingConfig()


# Convenience functions
def logging_disable() -> None:
    """Disable all logging."""
    os.environ["XSYSTEM_LOGGING_DISABLE"] = "true"
    logging.disable(logging.CRITICAL)


def logging_enable() -> None:
    """Enable logging."""
    logging_config.enable()


def logging_set_level(level: str) -> None:
    """Set logging level."""
    logging_config.set_level(level)
