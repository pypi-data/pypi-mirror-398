#exonware/xwsystem/tests/1.unit/utils/dt/test_core_xwsystem_utls_dt.py
"""
XSystem DateTime Unit Tests

Validates the public datetime utility APIs including formatting, parsing,
humanization, timezone helpers, and the legacy base datetime facade.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# Add the src directory to the path for local runs
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Pytest marker enforcement (pytest.ini uses --strict-markers)
pytestmark = pytest.mark.xwsystem_unit

pytz = pytest.importorskip("pytz", reason="xwsystem datetime utilities rely on pytz")

from exonware.xwsystem.utils.dt.base import BaseDateTime
from exonware.xwsystem.utils.dt.contracts import TimeFormat
from exonware.xwsystem.utils.dt.errors import DateTimeError, DateTimeFormatError, FormatError, ParseError
from exonware.xwsystem.utils.dt.formatting import DateTimeFormatter
from exonware.xwsystem.utils.dt.humanize import DateTimeHumanizer
from exonware.xwsystem.utils.dt.parsing import DateTimeParser
from exonware.xwsystem.utils.dt.timezone_utils import TimezoneUtils


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_datetime() -> datetime:
    """Stable reference datetime for deterministic assertions."""
    return datetime(2025, 1, 2, 15, 45, 30, tzinfo=timezone.utc)


@pytest.fixture
def formatter() -> DateTimeFormatter:
    return DateTimeFormatter()


@pytest.fixture
def parser() -> DateTimeParser:
    return DateTimeParser(default_timezone=timezone.utc)


@pytest.fixture
def humanizer() -> DateTimeHumanizer:
    return DateTimeHumanizer()


# ---------------------------------------------------------------------------
# Formatter Tests
# ---------------------------------------------------------------------------


class TestDateTimeFormatter:
    def test_format_datetime_iso(self, formatter: DateTimeFormatter, sample_datetime: datetime) -> None:
        """Formatter should produce ISO output identical to datetime.isoformat."""
        result = formatter.format_datetime(sample_datetime, TimeFormat.ISO)
        assert result == sample_datetime.isoformat()

    def test_format_datetime_rfc3339(self, formatter: DateTimeFormatter, sample_datetime: datetime) -> None:
        """RFC3339 formatting should preserve tz offset structure."""
        result = formatter.format_datetime(sample_datetime, TimeFormat.RFC3339)
        assert result.endswith("+00:00")
        assert "T" in result

    @pytest.mark.parametrize("pattern,expected", [("%Y-%m-%d", "2025-01-02"), ("%H:%M", "15:45")])
    def test_format_custom_patterns(
        self,
        formatter: DateTimeFormatter,
        sample_datetime: datetime,
        pattern: str,
        expected: str,
    ) -> None:
        """Custom formatting should respect explicit strftime patterns."""
        result = formatter.format_custom(sample_datetime, pattern)
        assert result == expected

    def test_get_available_formats_exposes_documented_keys(self, formatter: DateTimeFormatter) -> None:
        """Documented human descriptions should be present for supported formats."""
        available = formatter.get_available_formats()
        assert {"ISO", "US", "EU"}.issubset(available.keys())


# ---------------------------------------------------------------------------
# Parser Tests
# ---------------------------------------------------------------------------


class TestDateTimeParser:
    def test_parse_iso_string(self, parser: DateTimeParser, sample_datetime: datetime) -> None:
        """ISO strings should round-trip through the parser."""
        iso_text = sample_datetime.isoformat()
        result = parser.parse(iso_text)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None
        assert result.isoformat() == iso_text

    def test_parse_date_preserves_naive_result(self, parser: DateTimeParser) -> None:
        """Date-only strings should return naive datetimes when no timezone is provided."""
        result = parser.parse("2025-01-02")
        assert isinstance(result, datetime)
        assert result.year == 2025 and result.month == 1 and result.day == 2
        assert result.tzinfo is None

    def test_parse_timestamp_handles_milliseconds(self, parser: DateTimeParser, sample_datetime: datetime) -> None:
        """Millisecond timestamps should be interpreted correctly."""
        timestamp_ms = int(sample_datetime.timestamp() * 1000)
        result = parser.parse_timestamp(timestamp_ms)
        assert result is not None
        assert abs(result.timestamp() - sample_datetime.timestamp()) < 1


# ---------------------------------------------------------------------------
# Humanizer Tests
# ---------------------------------------------------------------------------


class TestDateTimeHumanizer:
    def test_humanize_timedelta_multicomponent(self, humanizer: DateTimeHumanizer) -> None:
        """Humanizer should include multiple units when requested."""
        delta = timedelta(days=1, hours=2, minutes=30)
        result = humanizer.humanize_timedelta(delta, precision=0, max_units=3)
        assert "1 day" in result
        assert "2 hours" in result or "2 hour" in result

    def test_format_relative_time_past(self, humanizer: DateTimeHumanizer) -> None:
        """Relative formatting should mention 'ago' for past datetimes."""
        reference = datetime(2025, 1, 3, tzinfo=timezone.utc)
        past = reference - timedelta(hours=3)
        result = humanizer.format_relative_time(past, relative_to=reference)
        assert "ago" in result

    def test_natural_time_range_same_day(self, humanizer: DateTimeHumanizer) -> None:
        """Natural time range should condense same-day intervals."""
        start = datetime(2025, 1, 2, 9, 0)
        end = datetime(2025, 1, 2, 11, 30)
        result = humanizer.natural_time_range(start, end)
        assert "AM" in result or "am" in result
        assert "-" in result


# ---------------------------------------------------------------------------
# Timezone Utility Tests
# ---------------------------------------------------------------------------


class TestTimezoneUtils:
    def test_convert_timezone_changes_offset(self, sample_datetime: datetime) -> None:
        """Conversion to a new timezone should update tzinfo and offset."""
        target_tz = "Asia/Riyadh"
        converted = TimezoneUtils.convert_timezone(sample_datetime, target_tz)
        assert converted.tzinfo is not None
        assert converted.tzinfo.zone == target_tz
        assert converted.utcoffset() == timedelta(hours=3)

    def test_get_timezone_info_includes_expected_keys(self) -> None:
        """Metadata lookup should expose offset, dst, and zone fields."""
        info = TimezoneUtils.get_timezone_info("UTC")
        assert set(info.keys()) == {"name", "offset", "dst", "zone"}


# ---------------------------------------------------------------------------
# Base DateTime Facade Tests
# ---------------------------------------------------------------------------


class TestBaseDateTime:
    def test_parse_and_format_roundtrip(self) -> None:
        """Parsing and formatting should round-trip cleanly."""
        base = BaseDateTime()
        text = "2025-01-02 12:34:56"
        parsed = base.parse(text)
        assert parsed.year == 2025
        assert base.format(parsed, "%Y-%m-%d %H:%M:%S") == text

    def test_timestamp_roundtrip_preserves_seconds(self) -> None:
        """Conversion to and from timestamps should keep second precision."""
        base = BaseDateTime()
        dt = datetime(2025, 1, 2, 12, 0, 5)
        ts = base.to_timestamp(dt)
        restored = base.from_timestamp(ts)
        assert abs(restored.timestamp() - dt.timestamp()) < 1e-6


# ---------------------------------------------------------------------------
# Error Hierarchy Tests
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    def test_datetime_errors_are_distinct(self) -> None:
        """Ensure the custom error hierarchy carries the expected types."""
        assert issubclass(FormatError, DateTimeError)
        assert issubclass(ParseError, DateTimeError)
        with pytest.raises(DateTimeFormatError):
            raise DateTimeFormatError("format failure")


# ---------------------------------------------------------------------------
# Legacy Runner Entry Point
# ---------------------------------------------------------------------------


def main() -> int:
    """
    Allow the module to be executed directly via `python test_core_xwsystem_utls_dt.py`.

    Returns:
        Process exit code compatible with legacy runners.
    """
    exit_code = pytest.main([str(Path(__file__).resolve())])
    return int(exit_code)


if __name__ == "__main__":
    sys.exit(main())

