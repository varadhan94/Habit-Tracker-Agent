"""
Cloud Function: sendWeeklyReport
Triggered by Cloud Scheduler every Sunday at 7 PM IST.
Reads the past week's data, generates recommendations, and sends a WhatsApp report.
"""

import functions_framework
import sys
import os

# Add project root to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import USER_PHONE_NUMBER, WEEKLY_REPORT_TEMPLATE
from shared.date_utils import get_past_n_days
from shared.sheets_client import get_week_data
from shared.gemini_client import generate_weekly_recommendations
from shared.whatsapp_client import (
    send_template_message,
    send_text_message,
    format_weekly_report,
)


@functions_framework.http
def send_weekly_report(request):
    """Generate and send the weekly habit report via WhatsApp."""
    try:
        # Get past 7 days of data
        dates = get_past_n_days(7)
        week_data = get_week_data(dates)

        # Generate recommendations using Gemini
        try:
            recommendations = generate_weekly_recommendations(week_data)
        except Exception as e:
            print(f"Gemini recommendation generation failed: {e}")
            recommendations = (
                "1. Keep up with your most consistent habits\n"
                "2. Try to add one more habit each day\n"
                "3. Don't break the streak on your top habits"
            )

        # Format the full report
        report_message = format_weekly_report(week_data, recommendations)

        # Try sending as template first (business-initiated, outside 24h window)
        try:
            send_template_message(
                to_number=USER_PHONE_NUMBER,
                template_name=WEEKLY_REPORT_TEMPLATE,
                parameters=[report_message],
            )
        except Exception:
            # Fallback: try as text message (works if within 24h session window)
            send_text_message(
                to_number=USER_PHONE_NUMBER,
                message_body=report_message,
            )

        return {
            "status": "success",
            "message": "Weekly report sent",
            "dates": [d.isoformat() for d in dates],
        }, 200

    except Exception as e:
        print(f"Error sending weekly report: {e}")
        return {"status": "error", "message": str(e)}, 500
