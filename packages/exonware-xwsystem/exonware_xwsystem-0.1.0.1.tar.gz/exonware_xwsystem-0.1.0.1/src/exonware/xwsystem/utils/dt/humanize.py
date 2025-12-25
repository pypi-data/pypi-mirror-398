"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Human-friendly datetime formatting and parsing utilities.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union

from exonware.xwsystem.config.logging_setup import get_logger

logger = get_logger("xwsystem.utils.dt.humanize")


def humanize_timedelta(td: timedelta, precision: int = 2, max_units: int = 2) -> str:
    """
    Convert timedelta to human-readable string.
    
    Args:
        td: Timedelta to humanize
        precision: Number of decimal places for seconds
        max_units: Maximum number of units to show
        
    Returns:
        Human-readable string like "2 days, 3 hours"
        
    Examples:
        >>> humanize_timedelta(timedelta(days=1, hours=2, minutes=30))
        "1 day, 2 hours"
        >>> humanize_timedelta(timedelta(seconds=90))
        "1 minute, 30 seconds"
    """
    if td.total_seconds() == 0:
        return "0 seconds"
    
    # Handle negative timedeltas
    negative = td.total_seconds() < 0
    if negative:
        td = -td
    
    # Break down into components
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Add microseconds to seconds
    if td.microseconds:
        seconds += td.microseconds / 1000000
    
    # Build components list
    components = []
    
    if days > 0:
        components.append(f"{days} day{'s' if days != 1 else ''}")
    
    if hours > 0:
        components.append(f"{hours} hour{'s' if hours != 1 else ''}")
    
    if minutes > 0:
        components.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    if seconds > 0 or not components:
        if precision > 0 and seconds != int(seconds):
            seconds_str = f"{seconds:.{precision}f}"
        else:
            seconds_str = str(int(seconds))
        components.append(f"{seconds_str} second{'s' if seconds != 1 else ''}")
    
    # Limit to max_units
    components = components[:max_units]
    
    # Join components
    if len(components) == 1:
        result = components[0]
    elif len(components) == 2:
        result = f"{components[0]} and {components[1]}"
    else:
        result = ", ".join(components[:-1]) + f", and {components[-1]}"
    
    return f"{'-' if negative else ''}{result}"


def humanize_timestamp(timestamp: Union[datetime, float], 
                      reference: Optional[datetime] = None,
                      precision: int = 2) -> str:
    """
    Convert timestamp to human-readable relative time.
    
    Args:
        timestamp: Datetime or Unix timestamp
        reference: Reference time (defaults to now)
        precision: Precision for time differences
        
    Returns:
        Human-readable string like "2 hours ago" or "in 3 days"
        
    Examples:
        >>> humanize_timestamp(datetime.now() - timedelta(hours=2))
        "2 hours ago"
        >>> humanize_timestamp(datetime.now() + timedelta(days=1))
        "in 1 day"
    """
    if reference is None:
        reference = datetime.now()
    
    # Convert timestamp to datetime if needed
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.fromtimestamp(timestamp)
    
    # Calculate difference
    diff = timestamp - reference
    
    if diff.total_seconds() == 0:
        return "now"
    
    # Determine if past or future
    if diff.total_seconds() > 0:
        prefix = "in "
        suffix = ""
    else:
        prefix = ""
        suffix = " ago"
        diff = -diff
    
    # Get human-readable difference
    human_diff = humanize_timedelta(diff, precision=precision, max_units=1)
    
    return f"{prefix}{human_diff}{suffix}"


def time_ago(timestamp: Union[datetime, float], precision: int = 2) -> str:
    """
    Get time ago string from timestamp.
    
    Args:
        timestamp: Datetime or Unix timestamp
        precision: Precision for time differences
        
    Returns:
        String like "2 hours ago"
    """
    return humanize_timestamp(timestamp, precision=precision)


def time_until(timestamp: Union[datetime, float], precision: int = 2) -> str:
    """
    Get time until string from timestamp.
    
    Args:
        timestamp: Datetime or Unix timestamp
        precision: Precision for time differences
        
    Returns:
        String like "in 2 hours"
    """
    return humanize_timestamp(timestamp, precision=precision)


def format_relative_time(dt: datetime, relative_to: Optional[datetime] = None, precision: int = 2) -> str:
    """
    Format a datetime relative to a reference point.

    Args:
        dt: Datetime to format.
        relative_to: Reference datetime. Defaults to now if not supplied.
        precision: Number of decimal places for sub-second precision.

    Returns:
        Human-readable relative time string (e.g., "3 hours ago", "in 2 days").
    """
    if relative_to is None:
        base = datetime.now(tz=dt.tzinfo) if isinstance(dt, datetime) and dt.tzinfo else datetime.now()
        relative_to = base

    return humanize_timestamp(dt, reference=relative_to, precision=precision)


def duration_to_human(seconds: Union[int, float], 
                     precision: int = 2, 
                     max_units: int = 2) -> str:
    """
    Convert duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        precision: Number of decimal places
        max_units: Maximum number of units to show
        
    Returns:
        Human-readable duration string
        
    Examples:
        >>> duration_to_human(3661)
        "1 hour, 1 minute"
        >>> duration_to_human(90.5)
        "1 minute, 30.5 seconds"
    """
    td = timedelta(seconds=seconds)
    return humanize_timedelta(td, precision=precision, max_units=max_units)


def parse_human_duration(duration_str: str) -> timedelta:
    """
    Parse human-readable duration string to timedelta.
    
    Args:
        duration_str: String like "2 hours 30 minutes" or "1h 30m"
        
    Returns:
        Parsed timedelta
        
    Raises:
        ValueError: If duration string cannot be parsed
        
    Examples:
        >>> parse_human_duration("2 hours 30 minutes")
        timedelta(hours=2, minutes=30)
        >>> parse_human_duration("1h 30m 45s")
        timedelta(hours=1, minutes=30, seconds=45)
    """
    duration_str = duration_str.lower().strip()
    
    if not duration_str:
        return timedelta()
    
    # Define patterns for different units
    patterns = {
        'weeks': [r'(\d+(?:\.\d+)?)\s*(?:weeks?|w)', 7 * 24 * 3600],
        'days': [r'(\d+(?:\.\d+)?)\s*(?:days?|d)', 24 * 3600],
        'hours': [r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)', 3600],
        'minutes': [r'(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)', 60],
        'seconds': [r'(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|s)', 1],
    }
    
    total_seconds = 0.0
    
    for unit, (pattern, multiplier) in patterns.items():
        matches = re.findall(pattern, duration_str)
        for match in matches:
            try:
                value = float(match)
                total_seconds += value * multiplier
                logger.debug(f"Parsed {value} {unit} = {value * multiplier} seconds")
            except ValueError:
                continue
    
    if total_seconds == 0:
        # Try some common shorthand formats
        shorthand_patterns = [
            (r'^(\d+(?:\.\d+)?)$', 1),  # Just a number = seconds
            (r'^(\d+):(\d+)$', lambda h, m: int(h) * 3600 + int(m) * 60),  # HH:MM
            (r'^(\d+):(\d+):(\d+)$', lambda h, m, s: int(h) * 3600 + int(m) * 60 + int(s)),  # HH:MM:SS
        ]
        
        for pattern, handler in shorthand_patterns:
            match = re.match(pattern, duration_str)
            if match:
                if callable(handler):
                    total_seconds = handler(*match.groups())
                else:
                    total_seconds = float(match.group(1)) * handler
                break
    
    if total_seconds == 0:
        raise ValueError(f"Could not parse duration: '{duration_str}'")
    
    return timedelta(seconds=total_seconds)


def smart_time_format(dt: datetime, reference: Optional[datetime] = None) -> str:
    """
    Smart time formatting that chooses appropriate format based on time difference.
    
    Args:
        dt: Datetime to format
        reference: Reference time (defaults to now)
        
    Returns:
        Appropriately formatted time string
        
    Examples:
        - Less than 1 minute: "just now"
        - Less than 1 hour: "15 minutes ago"
        - Same day: "2:30 PM"
        - Same year: "Mar 15, 2:30 PM"
        - Different year: "Mar 15, 2023"
    """
    if reference is None:
        reference = datetime.now()
    
    diff = abs((dt - reference).total_seconds())
    
    # Less than 1 minute
    if diff < 60:
        return "just now"
    
    # Less than 1 hour
    if diff < 3600:
        minutes = int(diff // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    
    # Same day
    if dt.date() == reference.date():
        return dt.strftime("%I:%M %p").lstrip('0')
    
    # Same year
    if dt.year == reference.year:
        return dt.strftime("%b %d, %I:%M %p").lstrip('0')
    
    # Different year
    return dt.strftime("%b %d, %Y")


def approximate_duration(seconds: Union[int, float]) -> str:
    """
    Get approximate duration in natural language.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Approximate duration string
        
    Examples:
        >>> approximate_duration(45)
        "about a minute"
        >>> approximate_duration(3700)
        "about an hour"
    """
    if seconds < 30:
        return "a few seconds"
    elif seconds < 90:
        return "about a minute"
    elif seconds < 45 * 60:  # 45 minutes
        minutes = round(seconds / 60)
        return f"about {minutes} minutes"
    elif seconds < 90 * 60:  # 1.5 hours
        return "about an hour"
    elif seconds < 24 * 3600:  # 24 hours
        hours = round(seconds / 3600)
        return f"about {hours} hours"
    elif seconds < 48 * 3600:  # 48 hours
        return "about a day"
    elif seconds < 30 * 24 * 3600:  # 30 days
        days = round(seconds / (24 * 3600))
        return f"about {days} days"
    elif seconds < 60 * 24 * 3600:  # 60 days
        return "about a month"
    elif seconds < 365 * 24 * 3600:  # 365 days
        months = round(seconds / (30 * 24 * 3600))
        return f"about {months} months"
    else:
        years = round(seconds / (365 * 24 * 3600))
        return f"about {years} year{'s' if years != 1 else ''}"


def natural_time_range(start: datetime, end: datetime) -> str:
    """
    Format time range in natural language.
    
    Args:
        start: Start datetime
        end: End datetime
        
    Returns:
        Natural time range string
        
    Examples:
        >>> natural_time_range(datetime(2023, 3, 15, 14, 0), datetime(2023, 3, 15, 16, 30))
        "2:00 PM - 4:30 PM"
        >>> natural_time_range(datetime(2023, 3, 15, 14, 0), datetime(2023, 3, 16, 10, 0))
        "Mar 15, 2:00 PM - Mar 16, 10:00 AM"
    """
    # Same day
    if start.date() == end.date():
        start_time = start.strftime("%I:%M %p").lstrip('0')
        end_time = end.strftime("%I:%M %p").lstrip('0')
        return f"{start_time} - {end_time}"
    
    # Same year
    if start.year == end.year:
        start_str = start.strftime("%b %d, %I:%M %p").lstrip('0')
        end_str = end.strftime("%b %d, %I:%M %p").lstrip('0')
        return f"{start_str} - {end_str}"
    
    # Different years
    start_str = start.strftime("%b %d, %Y %I:%M %p").lstrip('0')
    end_str = end.strftime("%b %d, %Y %I:%M %p").lstrip('0')
    return f"{start_str} - {end_str}"


class DateTimeHumanizer:
    """Human-friendly datetime formatting and parsing utilities."""
    
    def __init__(self, locale: str = "en_US"):
        """Initialize humanizer with locale."""
        self.locale = locale
    
    def humanize_timedelta(self, td: timedelta, precision: int = 2, max_units: int = 2) -> str:
        """Convert timedelta to human-readable string."""
        return humanize_timedelta(td, precision, max_units)
    
    def humanize_datetime(self, dt: datetime, relative_to: Optional[datetime] = None) -> str:
        """Convert datetime to human-readable string."""
        return smart_time_format(dt, relative_to)
    
    def humanize_date(self, date_obj: Union[datetime, str], relative_to: Optional[datetime] = None) -> str:
        """Convert date to human-readable string."""
        if isinstance(date_obj, datetime):
            return smart_time_format(date_obj, relative_to)
        elif isinstance(date_obj, str):
            try:
                dt = datetime.strptime(date_obj, "%Y-%m-%d")
                return smart_time_format(dt, relative_to)
            except ValueError:
                return date_obj
        return str(date_obj)
    
    def humanize_time(self, time_obj: Union[datetime, str], relative_to: Optional[datetime] = None) -> str:
        """Convert time to human-readable string."""
        if isinstance(time_obj, datetime):
            return smart_time_format(time_obj, relative_to)
        elif isinstance(time_obj, str):
            try:
                dt = datetime.strptime(time_obj, "%H:%M:%S")
                return smart_time_format(dt, relative_to)
            except ValueError:
                return time_obj
        return str(time_obj)
    
    def natural_time_range(self, start: datetime, end: datetime) -> str:
        """Convert time range to natural string."""
        return natural_time_range(start, end)
    
    def parse_natural_time(self, text: str, relative_to: Optional[datetime] = None) -> Optional[datetime]:
        """Parse natural time expressions."""
        # This method is not fully implemented in the original file,
        # so it will return None as a placeholder.
        # A proper implementation would involve a DateTimeParser.
        return None
    
    def format_relative_time(self, dt: datetime, relative_to: Optional[datetime] = None) -> str:
        """Format datetime as relative time."""
        return format_relative_time(dt, relative_to)