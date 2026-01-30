"""
Cloud Function: handleWhatsAppReply
HTTP trigger (Meta webhook). Receives user replies, parses habits,
updates Google Sheet, and sends confirmation.
"""

import functions_framework
import sys
import os

# Add project root to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import USER_PHONE_NUMBER
from shared.date_utils import get_today_ist, get_short_day_date, format_date_for_sheet
from shared.whatsapp_client import (
    verify_webhook,
    validate_webhook_signature,
    extract_message_from_webhook,
    send_text_message,
    format_confirmation_message,
)
from shared.gemini_client import parse_habit_reply
from shared.sheets_client import update_habit_row, get_today_data
from shared.habit_config import get_all_habit_names, HABITS


HELP_MESSAGE = (
    "Available habits and shortcuts:\n\n"
    "Walk/Run, Sandhi (morning/evening/both), Yoga, Brief, "
    "Cook, Utensils, Clothes, Upskill, Read/Audiobook, Jobs\n\n"
    "Tips:\n"
    "- Say times: 'walked 30' or just 'walked' for default\n"
    "- 'sandhi both' = morning + evening\n"
    "- 'household' = cook + utensils + clothes\n\n"
    "Commands: 'skip', 'status', 'help'"
)


@functions_framework.http
def handle_whatsapp_reply(request):
    """Handle incoming WhatsApp messages via Meta webhook."""
    print(f"[WEBHOOK] Received {request.method} request")

    # Handle webhook verification (GET request)
    if request.method == "GET":
        print(f"[WEBHOOK] GET params: {dict(request.args)}")
        challenge = verify_webhook(request.args)
        if challenge:
            print("[WEBHOOK] Verification succeeded")
            return challenge, 200
        print("[WEBHOOK] Verification failed")
        return "Verification failed", 403

    # Handle incoming message (POST request)
    if request.method == "POST":
        print("[WEBHOOK] Processing POST request")

        # Validate webhook signature
        signature = request.headers.get("X-Hub-Signature-256", "")
        raw_body = request.get_data()
        print(f"[WEBHOOK] Signature present: {bool(signature)}")
        print(f"[WEBHOOK] Body length: {len(raw_body)} bytes")

        if not validate_webhook_signature(raw_body, signature):
            print("[WEBHOOK] Signature validation FAILED")
            return "Invalid signature", 403

        print("[WEBHOOK] Signature validation PASSED")

        # Parse the webhook payload
        body = request.get_json(silent=True)
        if not body:
            print("[WEBHOOK] Empty body, returning OK")
            return "OK", 200

        print(f"[WEBHOOK] Body keys: {list(body.keys())}")

        message_data = extract_message_from_webhook(body)
        if not message_data:
            # Not a text message or no message — acknowledge anyway
            print("[WEBHOOK] No message extracted (status update or non-text)")
            return "OK", 200

        from_number = message_data["from_number"]
        message_text = message_data["message_text"].strip()
        print(f"[WEBHOOK] From: {from_number}, Text: {message_text}")
        print(f"[WEBHOOK] Expected user: {USER_PHONE_NUMBER}")

        # Only process messages from the configured user
        if from_number != USER_PHONE_NUMBER:
            print("[WEBHOOK] Number mismatch, ignoring")
            return "OK", 200

        try:
            response_text = process_user_message(message_text)
            send_text_message(to_number=from_number, message_body=response_text)
        except Exception as e:
            print(f"Error processing message: {e}")
            error_msg = (
                "Sorry, something went wrong. Please try again.\n"
                "Type 'help' for usage instructions."
            )
            send_text_message(to_number=from_number, message_body=error_msg)

        return "OK", 200

    return "Method not allowed", 405


def process_user_message(message_text):
    """Process the user's message and return a response string.

    Args:
        message_text: The user's WhatsApp message text

    Returns:
        Response message string to send back
    """
    message_lower = message_text.lower().strip()

    # Handle special commands
    if message_lower in ("skip", "off", "rest", "leave"):
        return handle_skip()

    if message_lower in ("status", "today"):
        return handle_status()

    if message_lower in ("help", "?"):
        return HELP_MESSAGE

    # Parse the habit reply using Gemini
    try:
        habit_data = parse_habit_reply(message_text)
    except ValueError:
        return (
            "I couldn't understand that. Could you rephrase?\n\n"
            "Example: 'walked 45, sandhi both, cooked, utensils, clothes, read 20'\n\n"
            "Type 'help' for all available habits."
        )

    if not habit_data:
        return (
            "No habits detected in your message. "
            "Type 'help' to see available habits and shortcuts."
        )

    # Update the Google Sheet
    today = get_today_ist()
    try:
        result = update_habit_row(today, habit_data)
    except ValueError as e:
        return f"Could not update sheet: {str(e)}"
    except Exception as e:
        # Sheet update failed — still tell user what was parsed
        parsed_summary = ", ".join(f"{k}: {v}min" for k, v in habit_data.items())
        return (
            f"Parsed your habits but failed to update the sheet:\n{parsed_summary}\n\n"
            f"Error: {str(e)}\nPlease try again later."
        )

    # Format and return confirmation
    date_str = get_short_day_date(today)
    return format_confirmation_message(
        habit_data=habit_data,
        total_minutes=result["total_minutes"],
        percentage=result["percentage"],
        date_str=date_str,
    )


def handle_skip():
    """Mark today as a skip/off day."""
    today = get_today_ist()
    date_str = get_short_day_date(today)
    # We don't update the sheet for skip days — they stay blank
    return f"Got it! {date_str} marked as a rest day. See you tomorrow!"


def handle_status():
    """Show today's currently logged habits."""
    today = get_today_ist()
    date_str = get_short_day_date(today)
    data = get_today_data(today)

    if not data:
        return f"No habits logged yet for {date_str}. Reply with what you did today!"

    lines = [f"Today's log ({date_str}):\n"]
    total = 0
    for habit_name, mins in sorted(data.items()):
        if isinstance(mins, int):
            lines.append(f"  {habit_name}: {mins} min")
            total += mins

    from shared.habit_config import DAILY_TARGET_MINUTES
    percentage = (total / DAILY_TARGET_MINUTES) * 100
    lines.append(f"\nTotal: {total} min | {percentage:.1f}%")

    return "\n".join(lines)
