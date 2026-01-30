"""
Cloud Function: sendDailyPrompt
Triggered by Cloud Scheduler at 9 PM IST daily.
Sends a WhatsApp message asking the user what habits they completed today.
"""

import functions_framework
import sys
import os

# Add project root to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import USER_PHONE_NUMBER, DAILY_PROMPT_TEMPLATE
from shared.date_utils import get_today_ist, get_short_day_date
from shared.whatsapp_client import send_template_message


@functions_framework.http
def send_daily_prompt(request):
    """Send the daily habit check-in prompt via WhatsApp."""
    try:
        today = get_today_ist()
        day_date_str = get_short_day_date(today)

        # Send template message with parameters:
        # {{1}} = User's name, {{2}} = Day and date
        parameters = ["Varadha", day_date_str]

        send_template_message(
            to_number=USER_PHONE_NUMBER,
            template_name=DAILY_PROMPT_TEMPLATE,
            parameters=parameters,
        )

        return {"status": "success", "message": f"Daily prompt sent for {day_date_str}"}, 200

    except Exception as e:
        print(f"Error sending daily prompt: {e}")
        return {"status": "error", "message": str(e)}, 500
