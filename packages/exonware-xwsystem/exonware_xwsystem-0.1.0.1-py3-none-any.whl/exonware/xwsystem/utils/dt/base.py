#exonware/xwsystem/datetime/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

DateTime module base classes - abstract classes for date/time functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from datetime import datetime, date, time, timedelta
from .contracts import DateTimeFormat, TimezoneType, HumanizeStyle


class ADateTimeBase(ABC):
    """Abstract base class for datetime operations."""
    
    @abstractmethod
    def parse(self, date_string: str, format_string: Optional[str] = None) -> datetime:
        """Parse datetime string."""
        pass
    
    @abstractmethod
    def format(self, dt: datetime, format_string: str) -> str:
        """Format datetime object."""
        pass
    
    @abstractmethod
    def now(self, timezone: Optional[str] = None) -> datetime:
        """Get current datetime."""
        pass
    
    @abstractmethod
    def utcnow(self) -> datetime:
        """Get current UTC datetime."""
        pass
    
    @abstractmethod
    def from_timestamp(self, timestamp: Union[int, float], timezone: Optional[str] = None) -> datetime:
        """Create datetime from timestamp."""
        pass
    
    @abstractmethod
    def to_timestamp(self, dt: datetime) -> float:
        """Convert datetime to timestamp."""
        pass


class ATimezoneBase(ABC):
    """Abstract base class for timezone operations."""
    
    @abstractmethod
    def get_timezone(self, timezone_name: str) -> Any:
        """Get timezone object."""
        pass
    
    @abstractmethod
    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime between timezones."""
        pass
    
    @abstractmethod
    def get_local_timezone(self) -> str:
        """Get local timezone."""
        pass
    
    @abstractmethod
    def get_utc_offset(self, timezone_name: str, dt: Optional[datetime] = None) -> timedelta:
        """Get UTC offset for timezone."""
        pass
    
    @abstractmethod
    def is_dst(self, dt: datetime, timezone_name: str) -> bool:
        """Check if datetime is in daylight saving time."""
        pass
    
    @abstractmethod
    def list_timezones(self) -> list[str]:
        """List available timezones."""
        pass


class AHumanizeBase(ABC):
    """Abstract base class for datetime humanization."""
    
    @abstractmethod
    def humanize(self, dt: datetime, style: HumanizeStyle = HumanizeStyle.RELATIVE) -> str:
        """Humanize datetime."""
        pass
    
    @abstractmethod
    def natural_time(self, dt: datetime) -> str:
        """Get natural time representation."""
        pass
    
    @abstractmethod
    def time_ago(self, dt: datetime) -> str:
        """Get time ago representation."""
        pass
    
    @abstractmethod
    def time_until(self, dt: datetime) -> str:
        """Get time until representation."""
        pass
    
    @abstractmethod
    def format_duration(self, duration: timedelta) -> str:
        """Format duration."""
        pass
    
    @abstractmethod
    def format_interval(self, start: datetime, end: datetime) -> str:
        """Format time interval."""
        pass


class ADateFormatBase(ABC):
    """Abstract base class for date formatting."""
    
    @abstractmethod
    def format_date(self, date_obj: date, format_string: str) -> str:
        """Format date object."""
        pass
    
    @abstractmethod
    def format_time(self, time_obj: time, format_string: str) -> str:
        """Format time object."""
        pass
    
    @abstractmethod
    def get_common_formats(self) -> dict[str, str]:
        """Get common date/time formats."""
        pass
    
    @abstractmethod
    def validate_format(self, format_string: str) -> bool:
        """Validate format string."""
        pass
    
    @abstractmethod
    def auto_detect_format(self, date_string: str) -> Optional[str]:
        """Auto-detect date format."""
        pass


class ADateTimeValidatorBase(ABC):
    """Abstract base class for datetime validation."""
    
    @abstractmethod
    def validate_date(self, date_string: str) -> bool:
        """Validate date string."""
        pass
    
    @abstractmethod
    def validate_time(self, time_string: str) -> bool:
        """Validate time string."""
        pass
    
    @abstractmethod
    def validate_datetime(self, datetime_string: str) -> bool:
        """Validate datetime string."""
        pass
    
    @abstractmethod
    def is_valid_timezone(self, timezone_name: str) -> bool:
        """Validate timezone name."""
        pass
    
    @abstractmethod
    def is_leap_year(self, year: int) -> bool:
        """Check if year is leap year."""
        pass
    
    @abstractmethod
    def get_validation_errors(self) -> list[str]:
        """Get validation errors."""
        pass


class BaseDateTime(ADateTimeBase):
    """Base implementation of datetime operations."""
    
    def __init__(self):
        """Initialize base datetime."""
        self._default_format = "%Y-%m-%d %H:%M:%S"
    
    def parse(self, date_string: str, format_string: Optional[str] = None) -> datetime:
        """Parse datetime string."""
        try:
            if format_string:
                return datetime.strptime(date_string, format_string)
            else:
                # Try common formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                    "%d/%m/%Y",
                    "%m/%d/%Y",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ"
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_string, fmt)
                    except ValueError:
                        continue
                
                # If no format works, try ISO format
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except Exception:
            raise ValueError(f"Unable to parse datetime string: {date_string}")
    
    def format(self, dt: datetime, format_string: str) -> str:
        """Format datetime object."""
        return dt.strftime(format_string)
    
    def now(self, timezone: Optional[str] = None) -> datetime:
        """Get current datetime."""
        if timezone:
            import pytz
            tz = pytz.timezone(timezone)
            return datetime.now(tz)
        return datetime.now()
    
    def utcnow(self) -> datetime:
        """Get current UTC datetime."""
        return datetime.utcnow()
    
    def from_timestamp(self, timestamp: Union[int, float], timezone: Optional[str] = None) -> datetime:
        """Create datetime from timestamp."""
        dt = datetime.fromtimestamp(timestamp)
        if timezone:
            import pytz
            tz = pytz.timezone(timezone)
            dt = tz.localize(dt)
        return dt
    
    def to_timestamp(self, dt: datetime) -> float:
        """Convert datetime to timestamp."""
        return dt.timestamp()