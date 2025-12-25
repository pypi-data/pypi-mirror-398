"""
Public-facing configuration shorthands.

This module delegates to exonware.conf for backward compatibility.
For new code, prefer: import exonware.conf as conf
"""

from __future__ import annotations

import sys
import types

# Delegate to top-level conf for backward compatibility
# This allows both import patterns to work:
# - import exonware.conf as conf (preferred - no xwsystem initialization)
# - import exonware.xwsystem.conf as conf (backward compatible)


class _ConfModule(types.ModuleType):
    """Expose selected config toggles as module-level attributes."""

    def __getattr__(self, name: str):
        # Delegate to top-level conf module
        try:
            import exonware.conf as top_conf
            return getattr(top_conf.xwsystem, name)
        except (ImportError, AttributeError):
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value) -> None:
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
        
        # Delegate to top-level conf module
        try:
            import exonware.conf as top_conf
            setattr(top_conf.xwsystem, name, value)
        except (ImportError, AttributeError):
            super().__setattr__(name, value)


sys.modules[__name__].__class__ = _ConfModule

