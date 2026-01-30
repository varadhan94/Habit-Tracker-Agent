"""
Meta Cloud API (WhatsApp Business Platform) client for sending and receiving messages.
"""

import hashlib
import hmac
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    META_ACCESS_TOKEN,
    META_PHONE_NUMBER_ID,
    META_APP_SECRET,
    META_API_VERSION,
    WHATSAPP_VERIFY_TOKEN,
    DAILY_PROMPT_TEMPLATE,
    WEEKLY_REPORT_TEMPLATE,
)

GRAPH_API_URL = f"https://graph.facebook.com/{META_API_VERSION}/{META_PHONE_NUMBER_ID}/messages"


def send_text_message(to_number, message_body):
    """Send a free-form text message (only works within 24h session window).

    Args:
        to_number: Recipient's WhatsApp number (e.g., "91XXXXXXXXXX")
        message_body: The text message to send

    Returns:
        dict with API response

    Raises:
        requests.HTTPError: If the API call fails
    """
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"body": message_body},
    }

    response = requests.post(GRAPH_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def send_template_message(to_number, template_name, parameters):
    """Send a template message (for business-initiated conversations).

    Args:
        to_number: Recipient's WhatsApp number
        template_name: The approved template name
        parameters: list of parameter values for the template

    Returns:
        dict with API response
    """
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Build template components with parameters
    components = []
    if parameters:
        body_params = [{"type": "text", "text": str(p)} for p in parameters]
        components.append({"type": "body", "parameters": body_params})

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": components,
        },
    }

    response = requests.post(GRAPH_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def verify_webhook(request_args):
    """Handle the webhook verification challenge from Meta.

    Args:
        request_args: dict of query parameters from the GET request

    Returns:
        The challenge string if verification succeeds, None otherwise
    """
    mode = request_args.get("hub.mode")
    token = request_args.get("hub.verify_token")
    challenge = request_args.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return challenge
    return None


def validate_webhook_signature(request_body, signature_header):
    """Validate the X-Hub-Signature-256 header from incoming webhooks.

    Args:
        request_body: Raw request body bytes
        signature_header: Value of the X-Hub-Signature-256 header

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header:
        return False

    expected_signature = hmac.new(
        META_APP_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha256,
    ).hexdigest()

    received_signature = signature_header.replace("sha256=", "")
    return hmac.compare_digest(expected_signature, received_signature)


def extract_message_from_webhook(webhook_body):
    """Extract the message text and sender info from a webhook payload.

    Args:
        webhook_body: Parsed JSON body of the webhook POST request

    Returns:
        dict with 'from_number', 'message_text', 'message_id' or None if not a text message
    """
    try:
        entry = webhook_body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None

        message = messages[0]
        if message.get("type") != "text":
            return None

        return {
            "from_number": message["from"],
            "message_text": message["text"]["body"],
            "message_id": message["id"],
        }
    except (IndexError, KeyError, TypeError):
        return None


def format_confirmation_message(habit_data, total_minutes, percentage, date_str):
    """Format a confirmation message after successfully logging habits.

    Args:
        habit_data: dict of {habit_name: minutes}
        total_minutes: Total minutes logged
        percentage: Completion percentage
        date_str: Formatted date string

    Returns:
        Formatted confirmation message string
    """
    lines = [f"Logged for {date_str}:\n"]

    for habit_name, mins in sorted(habit_data.items()):
        lines.append(f"  {habit_name}: {mins} min")

    lines.append(f"\nTotal: {total_minutes} min | {percentage:.1f}%")

    # Show habits not logged
    from shared.habit_config import get_all_habit_names
    all_habits = set(get_all_habit_names())
    done_habits = set(habit_data.keys())
    missed = all_habits - done_habits
    if missed:
        lines.append(f"\nNot logged: {', '.join(sorted(missed))}")

    return "\n".join(lines)


def format_weekly_report(week_data, recommendations):
    """Format the weekly report message.

    Args:
        week_data: list of daily data dicts
        recommendations: str with 3 numbered recommendations

    Returns:
        Formatted weekly report message string
    """
    active_days = [d for d in week_data if not d["is_off_day"] and d["habits"]]

    if not active_days:
        return "No habits logged this week. Let's start fresh next week!"

    avg_pct = sum(d["percentage"] for d in active_days) / len(active_days)
    total_mins = sum(d["total"] for d in active_days)
    best_day = max(active_days, key=lambda d: d["percentage"])

    # Habit frequency across the week
    habit_counts = {}
    for day in active_days:
        for habit_name in day["habits"]:
            habit_counts[habit_name] = habit_counts.get(habit_name, 0) + 1

    most_consistent = max(habit_counts, key=habit_counts.get) if habit_counts else "None"
    most_missed_habits = [
        name for name, count in habit_counts.items() if count <= 1
    ]

    # Date range
    start_date = week_data[0]["date"]
    end_date = week_data[-1]["date"]

    report = (
        f"Weekly Report ({start_date} to {end_date}):\n\n"
        f"Active days: {len(active_days)}/7 | Avg: {avg_pct:.1f}% | Total: {total_mins} min\n"
        f"Best: {best_day['day']} ({best_day['percentage']:.1f}%)\n"
        f"Most consistent: {most_consistent} ({habit_counts[most_consistent]}/{len(active_days)} days)\n"
    )

    if most_missed_habits:
        report += f"Needs work: {', '.join(most_missed_habits[:3])}\n"

    report += f"\nRecommendations:\n{recommendations}"

    return report
