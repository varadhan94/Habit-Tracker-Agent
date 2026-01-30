#!/bin/bash
# Create Cloud Scheduler jobs for daily prompt and weekly report

set -e

PROJECT_ID="habit-tracker-agent-varadha"
REGION="asia-south1"

echo "=== Setting up Cloud Scheduler Jobs ==="
echo ""

# Get the Cloud Function URLs
DAILY_PROMPT_URL=$(gcloud functions describe sendDailyPrompt --region="$REGION" --format='value(serviceConfig.uri)' 2>/dev/null)
WEEKLY_REPORT_URL=$(gcloud functions describe sendWeeklyReport --region="$REGION" --format='value(serviceConfig.uri)' 2>/dev/null)

if [ -z "$DAILY_PROMPT_URL" ] || [ -z "$WEEKLY_REPORT_URL" ]; then
    echo "ERROR: Cloud Functions not deployed yet. Run deploy.sh first."
    exit 1
fi

echo "Daily Prompt URL: $DAILY_PROMPT_URL"
echo "Weekly Report URL: $WEEKLY_REPORT_URL"
echo ""

# Get the service account for authentication
SA_EMAIL="${PROJECT_ID}@appspot.gserviceaccount.com"

# Create App Engine app if it doesn't exist (required for Cloud Scheduler)
gcloud app create --region="$REGION" 2>/dev/null || true

# Job 1: Daily prompt at 9 PM IST
echo "Creating daily prompt scheduler (9 PM IST)..."
gcloud scheduler jobs delete daily-habit-prompt --location="$REGION" --quiet 2>/dev/null || true
gcloud scheduler jobs create http daily-habit-prompt \
    --location="$REGION" \
    --schedule="0 21 * * *" \
    --time-zone="Asia/Kolkata" \
    --uri="$DAILY_PROMPT_URL" \
    --http-method=POST \
    --oidc-service-account-email="$SA_EMAIL"

echo "Daily prompt job created (runs at 9:00 PM IST every day)"

# Job 2: Weekly report on Sunday at 7 PM IST
echo ""
echo "Creating weekly report scheduler (Sunday 7 PM IST)..."
gcloud scheduler jobs delete weekly-habit-report --location="$REGION" --quiet 2>/dev/null || true
gcloud scheduler jobs create http weekly-habit-report \
    --location="$REGION" \
    --schedule="0 19 * * 0" \
    --time-zone="Asia/Kolkata" \
    --uri="$WEEKLY_REPORT_URL" \
    --http-method=POST \
    --oidc-service-account-email="$SA_EMAIL"

echo "Weekly report job created (runs at 7:00 PM IST every Sunday)"

echo ""
echo "=== Scheduler Setup Complete ==="
echo ""
echo "To test manually:"
echo "  gcloud scheduler jobs run daily-habit-prompt --location=$REGION"
echo "  gcloud scheduler jobs run weekly-habit-report --location=$REGION"
