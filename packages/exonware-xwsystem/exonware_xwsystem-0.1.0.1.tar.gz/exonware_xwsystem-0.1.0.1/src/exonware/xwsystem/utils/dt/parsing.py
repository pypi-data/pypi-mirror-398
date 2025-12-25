"""
Datetime Parsing Utilities
==========================

Production-grade datetime parsing for XSystem.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generated: 2025-01-27
"""

import re
from datetime import datetime, date, time, timezone, timedelta
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


# Common datetime patterns
DATETIME_PATTERNS = [
    # ISO 8601 formats
    (r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(?:Z|([+-]\d{2}):?(\d{2}))?', 'iso_datetime'),
    (r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(?:\s*([+-]\d{2}):?(\d{2}))?', 'iso_datetime_space'),
    
    # Date only formats
    (r'(\d{4})-(\d{2})-(\d{2})', 'iso_date'),
    (r'(\d{2})/(\d{2})/(\d{4})', 'us_date'),  # MM/DD/YYYY
    (r'(\d{2})-(\d{2})-(\d{4})', 'eu_date'),  # DD-MM-YYYY
    (r'(\d{1,2})/(\d{1,2})/(\d{4})', 'us_date_short'),
    (r'(\d{1,2})-(\d{1,2})-(\d{4})', 'eu_date_short'),
    
    # Time only formats
    (r'(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.(\d+))?\s*(AM|PM)?', 'time_12h'),
    (r'(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.(\d+))?', 'time_24h'),
    
    # Relative formats
    (r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago', 'relative_past'),
    (r'in\s*(\d+)\s*(second|minute|hour|day|week|month|year)s?', 'relative_future'),
    
    # Natural language
    (r'(yesterday|today|tomorrow)', 'natural_day'),
    (r'(now)', 'natural_now'),
]


def parse_datetime(text: str, default_timezone: Optional[timezone] = None) -> Optional[datetime]:
    """
    Parse datetime from text.
    
    Args:
        text: Text to parse
        default_timezone: Default timezone
        
    Returns:
        Parsed datetime or None
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    tz = default_timezone or timezone.utc
    
    # Try ISO 8601 first
    try:
        if hasattr(datetime, 'fromisoformat'):
            if text.endswith('Z'):
                text_iso = text[:-1] + '+00:00'
            else:
                text_iso = text
            return datetime.fromisoformat(text_iso)
    except (ValueError, AttributeError):
        pass
    
    # Try common formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%m/%d/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            if tz and dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            return dt
        except ValueError:
            continue
    
    return None


def parse_date(text: str) -> Optional[date]:
    """Parse date from text."""
    dt = parse_datetime(text)
    return dt.date() if dt else None


def parse_time(text: str) -> Optional[time]:
    """Parse time from text."""
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Try common time formats
    formats = [
        '%H:%M:%S',
        '%H:%M:%S.%f',
        '%H:%M',
        '%I:%M:%S %p',
        '%I:%M %p',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.time()
        except ValueError:
            continue
    
    return None


def parse_iso8601(text: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string."""
    try:
        if hasattr(datetime, 'fromisoformat'):
            if text.endswith('Z'):
                text = text[:-1] + '+00:00'
            return datetime.fromisoformat(text)
    except (ValueError, AttributeError):
        pass
    
    return parse_datetime(text)


def parse_timestamp(timestamp: Union[int, float, str]) -> Optional[datetime]:
    """Parse Unix timestamp to datetime."""
    try:
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        
        # Handle both seconds and milliseconds
        if timestamp > 1e10:  # Likely milliseconds
            timestamp = timestamp / 1000
        
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
    except (ValueError, OSError, OverflowError) as e:
        logger.debug(f"Failed to parse timestamp '{timestamp}': {e}")
        return None


class DateTimeParser:
    """Advanced datetime parser with multiple format support."""
    
    def __init__(self, default_timezone: Optional[timezone] = None):
        self.default_timezone = default_timezone or timezone.utc
        self._cache = {}
    
    def parse(self, text: str) -> Optional[datetime]:
        """Parse datetime from text with caching."""
        if not text:
            return None
        
        # Check cache first
        if text in self._cache:
            return self._cache[text]
        
        result = parse_datetime(text, self.default_timezone)
        if result:
            self._cache[text] = result
        
        return result
    
    def parse_date(self, text: str) -> Optional[date]:
        """Parse date from text."""
        dt = self.parse(text)
        return dt.date() if dt else None
    
    def parse_time(self, text: str) -> Optional[time]:
        """Parse time from text."""
        return parse_time(text)
    
    def parse_iso8601(self, text: str) -> Optional[datetime]:
        """Parse ISO 8601 datetime string."""
        return parse_iso8601(text)
    
    def parse_timestamp(self, timestamp: Union[int, float, str]) -> Optional[datetime]:
        """Parse Unix timestamp to datetime."""
        return parse_timestamp(timestamp)
    
    def clear_cache(self):
        """Clear parsing cache."""
        self._cache.clear()
    
    def get_cache_size(self) -> int:
        """Get cache size."""
        return len(self._cache)
    
    def is_valid_datetime(self, text: str) -> bool:
        """Check if text is a valid datetime."""
        return self.parse(text) is not None
    
    def is_valid_date(self, text: str) -> bool:
        """Check if text is a valid date."""
        return self.parse_date(text) is not None
    
    def is_valid_time(self, text: str) -> bool:
        """Check if text is a valid time."""
        return self.parse_time(text) is not None