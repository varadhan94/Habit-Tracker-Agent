"""Tests for date_utils module."""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.date_utils import (
    format_date_for_sheet,
    get_day_name,
    get_short_day_date,
    get_past_n_days,
    parse_sheet_date,
)


def test_format_date_for_sheet():
    """Should format dates as D-Mon-YYYY."""
    d = date(2026, 1, 24)
    assert format_date_for_sheet(d) == "24-Jan-2026"

    # Single digit day
    d = date(2026, 1, 2)
    assert format_date_for_sheet(d) == "2-Jan-2026"

    # Different month
    d = date(2025, 10, 15)
    assert format_date_for_sheet(d) == "15-Oct-2025"


def test_get_day_name():
    """Should return correct day names."""
    d = date(2026, 1, 24)  # Saturday
    assert get_day_name(d) == "Saturday"

    d = date(2026, 1, 19)  # Monday
    assert get_day_name(d) == "Monday"


def test_get_short_day_date():
    """Should return 'DayName, D-Mon' format."""
    d = date(2026, 1, 24)
    result = get_short_day_date(d)
    assert "Saturday" in result
    assert "24-Jan" in result


def test_get_past_n_days():
    """Should return n dates in chronological order."""
    dates = get_past_n_days(7)
    assert len(dates) == 7
    # Should be in ascending order
    for i in range(1, len(dates)):
        assert dates[i] > dates[i - 1]


def test_get_past_n_days_includes_today():
    """Last date should be today."""
    from shared.date_utils import get_today_ist

    dates = get_past_n_days(7)
    assert dates[-1] == get_today_ist()


def test_parse_sheet_date():
    """Should parse sheet date format back to date object."""
    result = parse_sheet_date("24-Jan-2026")
    assert result == date(2026, 1, 24)

    result = parse_sheet_date("2-Oct-2025")
    assert result == date(2025, 10, 2)
