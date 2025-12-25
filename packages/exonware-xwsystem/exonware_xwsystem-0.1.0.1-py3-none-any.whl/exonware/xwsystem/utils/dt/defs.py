#!/usr/bin/env python3
#exonware/xwsystem/datetime/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

DateTime types and enums for XWSystem.
"""

from enum import Enum


# ============================================================================
# DATETIME ENUMS
# ============================================================================

class TimeFormat(Enum):
    """Time format types."""
    ISO = "iso"
    RFC2822 = "rfc2822"
    RFC3339 = "rfc3339"
    CUSTOM = "custom"


class DateFormat(Enum):
    """Date format types."""
    ISO = "iso"
    US = "us"
    EU = "eu"
    CUSTOM = "custom"


class TimezoneType(Enum):
    """Timezone types."""
    UTC = "utc"
    LOCAL = "local"
    CUSTOM = "custom"


class HumanizeUnit(Enum):
    """Humanize time units."""
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


class DateTimeFormat(Enum):
    """DateTime format types."""
    ISO = "iso"
    RFC2822 = "rfc2822"
    RFC3339 = "rfc3339"
    US = "us"
    EU = "eu"
    CUSTOM = "custom"


class HumanizeStyle(Enum):
    """Humanize styles."""
    RELATIVE = "relative"
    ABSOLUTE = "absolute"
    NATURAL = "natural"
    PRECISE = "precise"
