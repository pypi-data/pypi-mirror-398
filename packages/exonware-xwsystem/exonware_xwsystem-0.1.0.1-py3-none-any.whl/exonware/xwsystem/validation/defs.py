#!/usr/bin/env python3
#exonware/xwsystem/validation/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Validation types and enums for XWSystem.
"""

from enum import Enum
from ..shared.defs import ValidationLevel


# ============================================================================
# VALIDATION ENUMS
# ============================================================================


class ValidationType(Enum):
    """Validation types."""
    SCHEMA = "schema"
    TYPE = "type"
    RANGE = "range"
    PATTERN = "pattern"
    CUSTOM = "custom"


class ValidationResult(Enum):
    """Validation results."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    ERROR = "error"
