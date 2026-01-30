"""Tests for sheets_client module with mocked gspread."""

import sys
import os
from unittest.mock import patch, MagicMock
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@patch("shared.sheets_client.get_worksheet")
def test_find_row_by_date(mock_get_ws):
    """Should find the correct row for a given date."""
    from shared.sheets_client import find_row_by_date

    mock_ws = MagicMock()
    mock_ws.col_values.return_value = [
        "Date", "", "", "",  # Header rows
        "22-Jan-2026", "23-Jan-2026", "24-Jan-2026", "25-Jan-2026",
    ]

    row = find_row_by_date(mock_ws, date(2026, 1, 24))
    assert row == 7  # 1-indexed, 24-Jan is the 7th row


@patch("shared.sheets_client.get_worksheet")
def test_find_row_by_date_not_found(mock_get_ws):
    """Should return None if date not in sheet."""
    from shared.sheets_client import find_row_by_date

    mock_ws = MagicMock()
    mock_ws.col_values.return_value = ["Date", "", "", "", "22-Jan-2026"]

    row = find_row_by_date(mock_ws, date(2026, 2, 15))
    assert row is None


@patch("shared.sheets_client.get_worksheet")
@patch("shared.sheets_client.find_row_by_date")
def test_update_habit_row(mock_find_row, mock_get_ws):
    """Should update cells with habit data and calculate totals."""
    from shared.sheets_client import update_habit_row

    mock_ws = MagicMock()
    mock_get_ws.return_value = mock_ws
    mock_find_row.return_value = 10

    habit_data = {
        "Walking/Running": 45,
        "Sandhi - Morning": 10,
        "Cook Morning": 30,
    }

    result = update_habit_row(date(2026, 1, 24), habit_data)

    assert result["total_minutes"] == 85
    assert result["percentage"] == round((85 / 215) * 100, 2)
    assert result["row_number"] == 10
    mock_ws.update_cells.assert_called_once()


@patch("shared.sheets_client.get_worksheet")
@patch("shared.sheets_client.find_row_by_date")
def test_update_habit_row_not_found(mock_find_row, mock_get_ws):
    """Should raise ValueError if row not found."""
    from shared.sheets_client import update_habit_row

    mock_ws = MagicMock()
    mock_get_ws.return_value = mock_ws
    mock_find_row.return_value = None

    try:
        update_habit_row(date(2026, 2, 30), {"Walking/Running": 45})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Row not found" in str(e)


@patch("shared.sheets_client.get_worksheet")
@patch("shared.sheets_client.find_row_by_date")
def test_get_week_data(mock_find_row, mock_get_ws):
    """Should read a week of data correctly."""
    from shared.sheets_client import get_week_data

    mock_ws = MagicMock()
    mock_get_ws.return_value = mock_ws

    # Simulate finding rows
    mock_find_row.return_value = 10
    mock_ws.row_values.return_value = [
        "24-Jan-2026", "Saturday",  # Date, Day
        "45", "10", "5", "", "20", "30", "15", "15", "", "20", "",  # Habits
        "160", "74.42%",  # Total, Percentage
    ]

    dates = [date(2026, 1, 24)]
    result = get_week_data(dates)

    assert len(result) == 1
    assert result[0]["habits"]["Walking/Running"] == 45
    assert result[0]["habits"]["Sandhi - Morning"] == 10
    assert result[0]["total"] == 160
    assert result[0]["percentage"] == 74.42
