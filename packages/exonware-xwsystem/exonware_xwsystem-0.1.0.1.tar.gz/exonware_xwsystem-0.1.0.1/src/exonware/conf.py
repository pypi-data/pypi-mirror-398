#exonware/conf.py
"""
Public-facing configuration for all exonware packages.

This module is self-contained and can be imported without triggering
any library initialization. It provides lazy mode configuration that
works across all exonware packages (xwsystem, xwnode, xwdata, etc.).

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 11-Nov-2025
"""

from __future__ import annotations

import sys
import types

# CRITICAL: Set up warning filter BEFORE any other imports to catch early warnings
# This suppresses the decimal module mpd_setminalloc warning that appears on stderr
_original_stderr = sys.stderr

class _FilteredStderr:
    """Stderr wrapper that filters out decimal module warnings."""
    def __init__(self, original_stderr):
        self._original = original_stderr
        # Match various forms of the decimal warning
        self._filter_patterns = [
            "mpd_setminalloc",
            "MPD_MINALLOC", 
            "ignoring request to set",
            "libmpdec",
            "context.c:57"
        ]
    
    def write(self, text: str) -> int:
        """Write to stderr, filtering out unwanted warnings."""
        # Check if this line contains any of our filter patterns
        if any(pattern.lower() in text.lower() for pattern in self._filter_patterns):
            return len(text)  # Pretend we wrote it, but don't actually write
        return self._original.write(text)
    
    def flush(self) -> None:
        """Flush the original stderr."""
        self._original.flush()
    
    def reconfigure(self, *args, **kwargs):
        """Handle reconfigure calls - update original reference and reapply filter."""
        # Update the original reference after reconfigure
        result = self._original.reconfigure(*args, **kwargs)
        # Ensure filter stays active
        if sys.stderr is not self:
            sys.stderr = self  # type: ignore[assignment]
        return result
    
    def __getattr__(self, name: str):
        """Delegate all other attributes to original stderr."""
        return getattr(self._original, name)

# Set up filter immediately (default: suppress warnings)
_filtered_stderr = _FilteredStderr(_original_stderr)
sys.stderr = _filtered_stderr  # type: ignore[assignment]

# CRITICAL: Configure UTF-8 encoding on Windows for emoji support
# This ensures emojis work automatically when exonware.conf is imported
# Root cause: Windows console defaults to cp1252 encoding, which can't encode emojis
# Trigger: This code runs at import time, before any prints, ensuring UTF-8 is active
if sys.platform == "win32":
    try:
        # Try to reconfigure stdout/stderr to UTF-8 (Python 3.7+)
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass  # May fail if already reconfigured or not supported
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass  # May fail if already reconfigured or not supported
    except Exception:
        # Fallback: wrap stdout/stderr with UTF-8 TextIOWrapper
        import io
        try:
            if hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
                )
            if hasattr(_filtered_stderr._original, "buffer"):
                _filtered_stderr._original = io.TextIOWrapper(
                    _filtered_stderr._original.buffer, encoding="utf-8", errors="replace", line_buffering=True
                )
        except Exception:
            pass  # Silently fail if wrapping is not possible

# Configuration module - self-contained without xwlazy dependency
class _ConfModule(types.ModuleType):
    """Self-contained configuration module without xwlazy dependency."""
    def __getattr__(self, name: str):
        # Return a simple configuration object
        # This can be extended later if needed
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

_module_instance = _ConfModule(__name__, __doc__)

sys.modules[__name__] = _module_instance

