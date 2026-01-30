"""Tests for habit_config module."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.habit_config import (
    HABITS,
    COMPOUND_ALIASES,
    DAILY_TARGET_MINUTES,
    get_habit_by_name,
    get_all_habit_names,
)


def test_habit_count():
    """Should have exactly 11 habits defined."""
    assert len(HABITS) == 11


def test_habit_columns_are_sequential():
    """Habit columns should be C(2) through M(12)."""
    columns = [h["column_index"] for h in HABITS]
    assert columns == list(range(2, 13))


def test_daily_target():
    """Daily target should equal sum of all habit targets minus Job Applications."""
    total = sum(h["target_mins"] for h in HABITS if h["name"] != "Job Applications")
    assert DAILY_TARGET_MINUTES == total


def test_get_habit_by_name():
    """Should find habits by exact name."""
    habit = get_habit_by_name("Walking/Running")
    assert habit is not None
    assert habit["target_mins"] == 45
    assert habit["column_index"] == 2


def test_get_habit_by_name_not_found():
    """Should return None for unknown habits."""
    assert get_habit_by_name("Meditation") is None


def test_get_all_habit_names():
    """Should return all 11 habit names."""
    names = get_all_habit_names()
    assert len(names) == 11
    assert "Walking/Running" in names
    assert "Yoga" in names
    assert "Job Applications" in names


def test_compound_aliases():
    """Compound aliases should map to correct habits."""
    assert "Sandhi - Morning" in COMPOUND_ALIASES["sandhi both"]
    assert "Sandhi - Evening" in COMPOUND_ALIASES["sandhi both"]
    assert "Cook Morning" in COMPOUND_ALIASES["household"]
    assert "Utensils" in COMPOUND_ALIASES["household"]
    assert "Clothes" in COMPOUND_ALIASES["household"]


def test_all_habits_have_aliases():
    """Every habit should have at least one alias."""
    for habit in HABITS:
        assert len(habit["aliases"]) >= 1, f"{habit['name']} has no aliases"


def test_all_habits_have_target():
    """Every habit should have a positive target_mins."""
    for habit in HABITS:
        assert habit["target_mins"] > 0, f"{habit['name']} has no target"
