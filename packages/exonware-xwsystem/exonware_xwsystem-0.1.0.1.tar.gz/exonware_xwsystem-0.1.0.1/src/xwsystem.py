#exonware/xwsystem/src/xwsystem.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 05, 2025

Top-level xwsystem import alias for convenience.

This module provides a convenient top-level import alias so users can:
- import xwsystem
- from xwsystem import *

Instead of the full path:
- import exonware.xwsystem
- from exonware.xwsystem import *

DESIGN RATIONALE FOR WILDCARD IMPORT:
This file intentionally uses a wildcard import (from exonware.xwsystem import *) as an 
alias import technique. This is an EXCEPTION to the explicit imports rule because:

1. This is a convenience alias module, not core functionality
2. The wildcard import is the standard Python pattern for creating import aliases
3. It provides the same functionality as the main module without code duplication
4. All actual functionality is defined in the main exonware.xwsystem module
5. This approach is commonly used in Python libraries for backward compatibility

The wildcard import here is intentional and follows Python best practices for alias modules.
"""

# Import everything from the main xwsystem module
# NOTE: Wildcard import is intentional for alias import technique
# Temporarily importing just XWSerialization for testing
from exonware.xwsystem import *

# Import version from centralized location
from exonware.xwsystem.version import __version__

