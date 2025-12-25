#exonware/xwsystem/datetime/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

DateTime module errors - exception classes for date/time functionality.
"""


class DateTimeError(Exception):
    """Base exception for datetime errors."""
    pass


class DateTimeParseError(DateTimeError):
    """Raised when datetime parsing fails."""
    pass


class DateTimeFormatError(DateTimeError):
    """Raised when datetime format is invalid."""
    pass


class DateTimeValidationError(DateTimeError):
    """Raised when datetime validation fails."""
    pass


class TimezoneError(DateTimeError):
    """Raised when timezone operation fails."""
    pass


class TimezoneNotFoundError(TimezoneError):
    """Raised when timezone is not found."""
    pass


class TimezoneConversionError(TimezoneError):
    """Raised when timezone conversion fails."""
    pass


class HumanizeError(DateTimeError):
    """Raised when datetime humanization fails."""
    pass


class DateRangeError(DateTimeError):
    """Raised when date range is invalid."""
    pass


class TimeCalculationError(DateTimeError):
    """Raised when time calculation fails."""
    pass


class DateTimeOverflowError(DateTimeError):
    """Raised when datetime value overflows."""
    pass


class DateTimeUnderflowError(DateTimeError):
    """Raised when datetime value underflows."""
    pass


# Aliases for backward compatibility
FormatError = DateTimeFormatError
ParseError = DateTimeParseError