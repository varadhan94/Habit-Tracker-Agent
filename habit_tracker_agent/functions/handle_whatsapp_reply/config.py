import os

# Google Cloud
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "habit-tracker-agent-varadha")

# Google Sheet
SHEET_ID = os.environ.get("SHEET_ID", "")
SHEET_NAME = os.environ.get("SHEET_NAME", "Habits Tracker")

# Meta WhatsApp Cloud API
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
META_PHONE_NUMBER_ID = os.environ.get("META_PHONE_NUMBER_ID", "")
META_APP_SECRET = os.environ.get("META_APP_SECRET", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")

# User's WhatsApp number
USER_PHONE_NUMBER = os.environ.get("USER_PHONE_NUMBER", "")

# Google Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini model
GEMINI_MODEL = "gemini-2.0-flash"

# Graph API version
META_API_VERSION = "v21.0"

# Message template names
DAILY_PROMPT_TEMPLATE = "daily_habit_prompt"
WEEKLY_REPORT_TEMPLATE = "weekly_report"
