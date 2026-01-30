"""
IST timezone handling and date formatting for the habit tracker.
"""

from datetime import datetime, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")

# Date format used in the Google Sheet (e.g., "24-Jan-2026")
SHEET_DATE_FORMAT = "%-d-%b-%Y"


def get_now_ist():
    """Get current datetime in IST."""
    return datetime.now(IST)


def get_today_ist():
    """Get today's date in IST."""
    return get_now_ist().date()


def format_date_for_sheet(date):
    """Format a date object to match the sheet format: 'D-Mon-YYYY' (e.g., '24-Jan-2026')."""
    return date.strftime(SHEET_DATE_FORMAT)


def get_day_name(date):
    """Get the day name (e.g., 'Monday', 'Tuesday')."""
    return date.strftime("%A")


def get_short_day_date(date):
    """Get a short display string like 'Friday, 24-Jan'."""
    return f"{get_day_name(date)}, {date.strftime('%-d-%b')}"


def get_week_range():
    """Get the date range for the past 7 days (Monday to Sunday).
    Returns (start_date, end_date) as date objects.
    """
    today = get_today_ist()
    # Go back to last Monday
    days_since_monday = today.weekday()
    start_date = today - timedelta(days=days_since_monday)
    end_date = today
    return start_date, end_date


def get_past_n_days(n=7):
    """Get a list of the past n dates (including today)."""
    today = get_today_ist()
    return [today - timedelta(days=i) for i in range(n - 1, -1, -1)]


def parse_sheet_date(date_str):
    """Parse a date string from the sheet format back to a date object."""
    try:
        return datetime.strptime(date_str, "%d-%b-%Y").date()
    except ValueError:
        # Handle single-digit day without leading zero
        return datetime.strptime(date_str, "%-d-%b-%Y").date()
