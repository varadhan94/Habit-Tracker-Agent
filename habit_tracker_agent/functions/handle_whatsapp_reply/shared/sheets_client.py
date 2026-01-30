"""
Google Sheets client for reading and writing habit tracking data.
"""

import json
import os
import gspread
from google.oauth2.service_account import Credentials

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SHEET_ID, SHEET_NAME
from shared.habit_config import (
    DATA_START_ROW,
    DATE_COLUMN,
    DAY_COLUMN,
    TOTAL_COLUMN,
    PERCENTAGE_COLUMN,
    HABITS,
    DAILY_TARGET_MINUTES,
)
from shared.date_utils import format_date_for_sheet, get_day_name

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheets_client():
    """Authenticate and return a gspread client."""
    creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH")
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON")

    if creds_json:
        # For Cloud Functions: credentials stored as JSON string in env/secret
        creds_info = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    elif creds_path and os.path.exists(creds_path):
        # For local development: credentials file path
        credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    else:
        raise RuntimeError(
            "No Google Sheets credentials found. Set GOOGLE_SHEETS_CREDENTIALS_JSON "
            "or GOOGLE_SHEETS_CREDENTIALS_PATH."
        )

    return gspread.authorize(credentials)


def get_worksheet():
    """Get the habits tracker worksheet."""
    client = get_sheets_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    return spreadsheet.worksheet(SHEET_NAME)


def find_row_by_date(worksheet, date):
    """Find the row number for a given date.

    Args:
        worksheet: gspread worksheet object
        date: date object to find

    Returns:
        Row number (1-indexed) or None if not found
    """
    date_str = format_date_for_sheet(date)
    date_column_values = worksheet.col_values(DATE_COLUMN)

    for i, cell_value in enumerate(date_column_values):
        if cell_value.strip() == date_str:
            return i + 1  # gspread is 1-indexed

    return None


def update_habit_row(date, habit_data):
    """Write habit data to the sheet for a given date.

    Args:
        date: date object for the row to update
        habit_data: dict mapping habit names to minutes (e.g., {"Walking/Running": 45})

    Returns:
        dict with total_minutes, percentage, and row_number
    """
    worksheet = get_worksheet()
    row_num = find_row_by_date(worksheet, date)

    if row_num is None:
        raise ValueError(
            f"Row not found for date {format_date_for_sheet(date)}. "
            "Please ensure the date exists in the sheet."
        )

    # Build the cell updates
    cells_to_update = []

    for habit in HABITS:
        col_index = habit["column_index"] + 1  # gspread is 1-indexed
        value = habit_data.get(habit["name"], "")
        cells_to_update.append(
            gspread.Cell(row_num, col_index, value if value else "")
        )

    # Calculate total minutes
    total_minutes = sum(v for v in habit_data.values() if isinstance(v, (int, float)))

    # Calculate percentage
    percentage = (total_minutes / DAILY_TARGET_MINUTES) * 100

    # Add total and percentage cells
    cells_to_update.append(
        gspread.Cell(row_num, TOTAL_COLUMN, int(total_minutes))
    )
    cells_to_update.append(
        gspread.Cell(row_num, PERCENTAGE_COLUMN, f"{percentage:.2f}%")
    )

    # Batch update all cells
    worksheet.update_cells(cells_to_update)

    return {
        "total_minutes": int(total_minutes),
        "percentage": round(percentage, 2),
        "row_number": row_num,
    }


def get_today_data(date):
    """Read today's habit data from the sheet.

    Args:
        date: date object to read

    Returns:
        dict with habit data, or None if row not found or empty
    """
    worksheet = get_worksheet()
    row_num = find_row_by_date(worksheet, date)

    if row_num is None:
        return None

    row_values = worksheet.row_values(row_num)
    if len(row_values) < PERCENTAGE_COLUMN:
        return None

    habit_data = {}
    for habit in HABITS:
        col_idx = habit["column_index"]  # 0-indexed for list access
        if col_idx < len(row_values) and row_values[col_idx]:
            try:
                habit_data[habit["name"]] = int(row_values[col_idx])
            except ValueError:
                # Non-numeric value (like "SICK", "HOLIDAY")
                habit_data[habit["name"]] = row_values[col_idx]

    return habit_data if habit_data else None


def get_week_data(dates):
    """Read habit data for a list of dates.

    Args:
        dates: list of date objects

    Returns:
        list of dicts, each with 'date', 'day', 'habits', 'total', 'percentage'
    """
    worksheet = get_worksheet()
    week_data = []

    for date in dates:
        row_num = find_row_by_date(worksheet, date)
        entry = {
            "date": format_date_for_sheet(date),
            "day": get_day_name(date),
            "habits": {},
            "total": 0,
            "percentage": 0.0,
            "is_off_day": False,
        }

        if row_num is None:
            entry["is_off_day"] = True
            week_data.append(entry)
            continue

        row_values = worksheet.row_values(row_num)

        # Check for special entries (SICK, HOLIDAY, etc.)
        if len(row_values) > 2 and row_values[2] in ("SICK", "HOLIDAY", "PONGAL", "Diwali Break"):
            entry["is_off_day"] = True
            entry["note"] = row_values[2]
            week_data.append(entry)
            continue

        for habit in HABITS:
            col_idx = habit["column_index"]
            if col_idx < len(row_values) and row_values[col_idx]:
                try:
                    entry["habits"][habit["name"]] = int(row_values[col_idx])
                except ValueError:
                    pass

        # Get total and percentage if available
        if TOTAL_COLUMN - 1 < len(row_values) and row_values[TOTAL_COLUMN - 1]:
            try:
                entry["total"] = int(row_values[TOTAL_COLUMN - 1])
            except ValueError:
                pass

        if PERCENTAGE_COLUMN - 1 < len(row_values) and row_values[PERCENTAGE_COLUMN - 1]:
            try:
                pct_str = row_values[PERCENTAGE_COLUMN - 1].replace("%", "")
                entry["percentage"] = float(pct_str)
            except ValueError:
                pass

        week_data.append(entry)

    return week_data
