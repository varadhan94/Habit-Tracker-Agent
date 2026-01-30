# Habit Tracker Agent 🎯

A conversational AI agent that tracks daily habits through WhatsApp messages and stores data in Google Sheets for visualization.

## Overview

Building consistent habits is challenging—most tracking apps require manual input and lack the conversational nudges that drive accountability. This agent lives where you already are—WhatsApp. Simply message your habits as you complete them, and the agent tracks, encourages, and visualizes your progress automatically.

## Features

- **Natural Language Tracking** — Just text "completed my morning run" or "did 30 mins meditation" and the agent understands and logs it
- **Smart Reminders** — Contextual nudges based on your patterns and optimal timing
- **Streak Tracking** — Motivational streak counters with celebration messages
- **Weekly Summaries** — Automated insights on your habit consistency delivered every Sunday
- **Google Sheets Dashboard** — All data synced to a spreadsheet for custom visualization

## Tech Stack

| Component | Technology |
|-----------|------------|
| Messaging Platform | WhatsApp Business API |
| AI/NLU | Google Gemini |
| Data Storage | Google Sheets |
| Integration Layer | Twilio |
| Hosting | Google Cloud Functions |

## Project Structure

```
habit_tracker_agent/
├── functions/
│   ├── handle_whatsapp_reply/   # Processes incoming WhatsApp messages
│   ├── send_daily_prompt/       # Sends daily habit reminders
│   └── send_weekly_report/      # Generates weekly summary reports
├── shared/                      # Shared utilities
│   ├── gemini_client.py         # Gemini AI integration
│   ├── sheets_client.py         # Google Sheets operations
│   ├── whatsapp_client.py       # WhatsApp messaging
│   ├── habit_config.py          # Habit definitions
│   └── date_utils.py            # Date/time utilities
├── scripts/                     # Setup scripts
├── tests/                       # Unit tests
└── deploy.sh                    # Deployment script
```

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Set up Google Cloud project and enable required APIs
4. Configure WhatsApp Business API via Meta
5. Deploy using `./deploy.sh`

## License

MIT
