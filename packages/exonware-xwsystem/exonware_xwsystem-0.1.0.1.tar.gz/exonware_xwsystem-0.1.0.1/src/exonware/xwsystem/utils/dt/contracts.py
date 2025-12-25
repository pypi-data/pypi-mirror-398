"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

DateTime module contracts - interfaces and enums for date/time functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from datetime import datetime, date, time, timezone

# Import enums from types module
from .defs import (
    TimeFormat,
    DateFormat,
    TimezoneType,
    HumanizeUnit,
    DateTimeFormat,
    HumanizeStyle
)


class IDateTimeFormatter(ABC):
    """Interface for date/time formatting."""
    
    @abstractmethod
    def format_datetime(self, dt: datetime, format_type: TimeFormat) -> str:
        """Format datetime object."""
        pass
    
    @abstractmethod
    def format_date(self, d: date, format_type: DateFormat) -> str:
        """Format date object."""
        pass
    
    @abstractmethod
    def format_time(self, t: time, format_type: TimeFormat) -> str:
        """Format time object."""
        pass


class IDateTimeParser(ABC):
    """Interface for date/time parsing."""
    
    @abstractmethod
    def parse_datetime(self, date_string: str, format_type: Optional[TimeFormat] = None) -> datetime:
        """Parse datetime string."""
        pass
    
    @abstractmethod
    def parse_date(self, date_string: str, format_type: Optional[DateFormat] = None) -> date:
        """Parse date string."""
        pass
    
    @abstractmethod
    def parse_time(self, time_string: str, format_type: Optional[TimeFormat] = None) -> time:
        """Parse time string."""
        pass


class IDateTimeHumanizer(ABC):
    """Interface for humanizing time differences."""
    
    @abstractmethod
    def humanize(self, dt: datetime, reference: Optional[datetime] = None) -> str:
        """Humanize datetime relative to reference."""
        pass
    
    @abstractmethod
    def natural_time(self, dt: datetime, reference: Optional[datetime] = None) -> str:
        """Get natural time representation."""
        pass


class ITimezoneUtils(ABC):
    """Interface for timezone utilities."""
    
    @abstractmethod
    def get_timezone(self, tz_name: str) -> timezone:
        """Get timezone object."""
        pass
    
    @abstractmethod
    def convert_timezone(self, dt: datetime, target_tz: timezone) -> datetime:
        """Convert datetime to target timezone."""
        pass
    
    @abstractmethod
    def get_local_timezone(self) -> timezone:
        """Get local timezone."""
        pass