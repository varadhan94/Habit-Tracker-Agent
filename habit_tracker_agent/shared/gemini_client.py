"""
Google Gemini client for natural language parsing and weekly recommendations.
"""

import json
import os
import sys

import google.generativeai as genai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GEMINI_API_KEY, GEMINI_MODEL
from shared.habit_config import HABITS, COMPOUND_ALIASES, DAILY_TARGET_MINUTES

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

PARSE_SYSTEM_INSTRUCTION = """You are a habit tracking assistant. Parse the user's natural language
message into a structured JSON object mapping habit names to minutes spent.

Available habits and their default durations:
- Walking/Running: 45 min (aliases: walk, walked, running, ran, jog)
- Sandhi - Morning: 10 min (aliases: sandhi morning, sandhi am)
- Sandhi - Evening: 5 min (aliases: sandhi evening, sandhi pm)
- Yoga: 15 min
- Daily Brief: 20 min (aliases: brief, db)
- Cook Morning: 30 min (aliases: cook, cooked, cooking, breakfast)
- Utensils: 15 min (aliases: dishes, vessels)
- Clothes: 15 min (aliases: laundry, washing)
- Upskilling/Professional: 30 min (aliases: upskill, professional, study, networking)
- Audiobooks/Reading: 30 min (aliases: read, reading, audiobook, book, podcast)
- Job Applications: 15 min (aliases: job, jobs, applied)

Rules:
1. If a habit is mentioned WITHOUT a specific time, use its default duration
2. "sandhi both" means BOTH Sandhi - Morning (10) AND Sandhi - Evening (5)
3. "sandhi" alone means Sandhi - Morning (10)
4. "household" or "all household" means Cook Morning (30) + Utensils (15) + Clothes (15)
5. Return ONLY valid JSON in this exact format: {"habits": {"Habit Name": minutes, ...}}
6. Only include habits that were explicitly mentioned or implied
7. Times should be integers (minutes)
8. If user says a time like "1 hour" or "1.5 hrs", convert to minutes
9. If user mentions "everything" or "all", include all habits at default durations
10. Do NOT include any explanation, just the JSON object
"""

WEEKLY_REPORT_INSTRUCTION = """You are a concise personal habit coach. Given 7 days of habit tracking data,
provide exactly 3 crisp, actionable recommendations for the next week.

Rules:
1. Each recommendation must be under 100 characters
2. Be specific and reference actual habits from the data
3. Focus on: consistency gaps, building streaks, and linking habits together
4. Don't be generic - use the actual numbers and patterns you see
5. Return ONLY the 3 recommendations as a numbered list, nothing else
"""


def parse_habit_reply(user_message):
    """Parse a natural language habit reply into structured data.

    Args:
        user_message: The user's WhatsApp reply (e.g., "walked 45, sandhi both, cooked")

    Returns:
        dict mapping habit names to minutes (e.g., {"Walking/Running": 45, ...})

    Raises:
        ValueError: If parsing fails after retry
    """
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=PARSE_SYSTEM_INSTRUCTION,
    )

    # Try parsing up to 2 times
    for attempt in range(2):
        response = model.generate_content(user_message)
        response_text = response.text.strip()

        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

        try:
            parsed = json.loads(response_text)
            habits = parsed.get("habits", parsed)

            # Validate: ensure all keys are valid habit names
            valid_names = {h["name"] for h in HABITS}
            validated = {}
            for name, mins in habits.items():
                if name in valid_names and isinstance(mins, (int, float)):
                    validated[name] = int(mins)

            if validated:
                return validated
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    raise ValueError(f"Could not parse habit reply: {user_message}")


def generate_weekly_recommendations(week_data):
    """Generate 3 coaching recommendations based on the week's data.

    Args:
        week_data: list of dicts with daily habit data (from sheets_client.get_week_data)

    Returns:
        str with 3 numbered recommendations
    """
    # Format the week data as a readable summary for Gemini
    summary_lines = []
    for day in week_data:
        if day["is_off_day"]:
            note = day.get("note", "No data")
            summary_lines.append(f"{day['day']} ({day['date']}): OFF - {note}")
        elif day["habits"]:
            habits_str = ", ".join(
                f"{name}: {mins}min" for name, mins in day["habits"].items()
            )
            summary_lines.append(
                f"{day['day']} ({day['date']}): {habits_str} | "
                f"Total: {day['total']}min ({day['percentage']:.1f}%)"
            )
        else:
            summary_lines.append(f"{day['day']} ({day['date']}): No habits logged")

    # Calculate summary stats
    active_days = [d for d in week_data if not d["is_off_day"] and d["habits"]]
    if active_days:
        avg_pct = sum(d["percentage"] for d in active_days) / len(active_days)
        best_day = max(active_days, key=lambda d: d["percentage"])
        worst_day = min(active_days, key=lambda d: d["percentage"])

        # Habit frequency
        habit_counts = {}
        for day in active_days:
            for habit_name in day["habits"]:
                habit_counts[habit_name] = habit_counts.get(habit_name, 0) + 1

        most_consistent = max(habit_counts, key=habit_counts.get) if habit_counts else "None"
        least_done = min(habit_counts, key=habit_counts.get) if habit_counts else "None"

        stats = (
            f"\nWeek Stats: {len(active_days)} active days, "
            f"Avg: {avg_pct:.1f}%, "
            f"Best: {best_day['day']} ({best_day['percentage']:.1f}%), "
            f"Worst: {worst_day['day']} ({worst_day['percentage']:.1f}%)\n"
            f"Most consistent: {most_consistent} ({habit_counts.get(most_consistent, 0)}/{len(active_days)} days)\n"
            f"Least done: {least_done} ({habit_counts.get(least_done, 0)}/{len(active_days)} days)"
        )
    else:
        stats = "\nNo active days this week."

    prompt = "\n".join(summary_lines) + stats + f"\nDaily target: {DAILY_TARGET_MINUTES} mins"

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=WEEKLY_REPORT_INSTRUCTION,
    )

    response = model.generate_content(prompt)
    return response.text.strip()
