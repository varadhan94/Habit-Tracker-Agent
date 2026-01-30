"""
Habit definitions, column mappings, aliases, and target configuration.
Derived from the Google Sheet structure.
"""

# Each habit with its sheet column (0-indexed from C), target time, and aliases
HABITS = [
    {
        "name": "Walking/Running",
        "column_index": 2,  # Column C
        "target_mins": 45,
        "aliases": ["walk", "walked", "walking", "run", "running", "ran", "jog", "jogged"],
    },
    {
        "name": "Sandhi - Morning",
        "column_index": 3,  # Column D
        "target_mins": 10,
        "aliases": ["sandhi morning", "sandhi am", "sandhi m"],
    },
    {
        "name": "Sandhi - Evening",
        "column_index": 4,  # Column E
        "target_mins": 5,
        "aliases": ["sandhi evening", "sandhi pm", "sandhi e", "sandhi ev"],
    },
    {
        "name": "Yoga",
        "column_index": 5,  # Column F
        "target_mins": 15,
        "aliases": ["yoga"],
    },
    {
        "name": "Daily Brief",
        "column_index": 6,  # Column G
        "target_mins": 20,
        "aliases": ["brief", "daily brief", "db"],
    },
    {
        "name": "Cook Morning",
        "column_index": 7,  # Column H
        "target_mins": 30,
        "aliases": ["cook", "cooked", "cooking", "cook morning", "breakfast"],
    },
    {
        "name": "Utensils",
        "column_index": 8,  # Column I
        "target_mins": 15,
        "aliases": ["utensils", "dishes", "vessels", "wash dishes"],
    },
    {
        "name": "Clothes",
        "column_index": 9,  # Column J
        "target_mins": 15,
        "aliases": ["clothes", "laundry", "washing", "wash clothes"],
    },
    {
        "name": "Upskilling/Professional",
        "column_index": 10,  # Column K
        "target_mins": 30,
        "aliases": ["upskilling", "professional", "upskill", "networking", "study"],
    },
    {
        "name": "Audiobooks/Reading",
        "column_index": 11,  # Column L
        "target_mins": 30,
        "aliases": ["read", "reading", "audiobook", "audiobooks", "book", "podcast"],
    },
    {
        "name": "Job Applications",
        "column_index": 12,  # Column M
        "target_mins": 15,
        "aliases": ["job", "jobs", "applications", "apply", "applied"],
    },
]

# Compound aliases that map to multiple habits
COMPOUND_ALIASES = {
    "sandhi both": ["Sandhi - Morning", "Sandhi - Evening"],
    "sandhi": ["Sandhi - Morning"],  # Default to morning if just "sandhi"
    "household": ["Cook Morning", "Utensils", "Clothes"],
    "all household": ["Cook Morning", "Utensils", "Clothes"],
}

# Sheet structure
DATA_START_ROW = 5  # Row where data begins (1-indexed in gspread)
DATE_COLUMN = 1     # Column A (1-indexed in gspread)
DAY_COLUMN = 2      # Column B
TOTAL_COLUMN = 14   # Column N
PERCENTAGE_COLUMN = 15  # Column O

# Daily target in minutes (sum of all habit targets excluding Job Applications)
# 45+10+5+15+20+30+15+15+30+30 = 215
DAILY_TARGET_MINUTES = 215

# Number of habit columns (C through M)
NUM_HABIT_COLUMNS = 11


def get_habit_by_name(name):
    """Get habit config by exact name."""
    for habit in HABITS:
        if habit["name"] == name:
            return habit
    return None


def get_all_habit_names():
    """Get list of all habit names."""
    return [h["name"] for h in HABITS]
