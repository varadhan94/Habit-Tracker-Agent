#!/bin/bash
# Meta WhatsApp Business Platform Setup Guide
# This script provides step-by-step instructions (not automated)

cat << 'GUIDE'
=== Meta WhatsApp Cloud API Setup Guide ===

Follow these steps to set up WhatsApp Business API (free tier):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: Create a Meta Business Account
  - Go to: https://business.facebook.com/
  - Sign up or log in with your Facebook account
  - Complete business verification if prompted

STEP 2: Create a Meta App
  - Go to: https://developers.facebook.com/apps/
  - Click "Create App"
  - Select "Business" as the app type
  - Fill in app name: "Personal Habits Agent"
  - Select your Business Account
  - Click "Create App"

STEP 3: Add WhatsApp Product
  - In your app dashboard, find "Add Products"
  - Click "Set Up" on the WhatsApp card
  - This will create a WhatsApp Business Account for you

STEP 4: Set Up a Phone Number
  - Go to WhatsApp > Getting Started
  - You'll see a test phone number provided by Meta
  - To use your own number: Go to WhatsApp > Phone Numbers > Add Phone Number
  - Verify the number via SMS or voice call

STEP 5: Configure Business Profile
  - Go to WhatsApp > Phone Numbers
  - Click on your number
  - Set Display Name: "Personal Habits Agent"
  - Upload a Profile Picture
  - Add Description: "Your daily habit tracking companion"

STEP 6: Create Message Templates
  - Go to WhatsApp > Message Templates
  - Click "Create Template"

  Template 1 - Daily Prompt:
    - Name: daily_habit_prompt
    - Category: UTILITY
    - Language: English
    - Body: "Hey {{1}}! What habits did you complete today ({{2}})? Reply naturally.

             Habits: Walk, Sandhi, Yoga, Brief, Cook, Utensils, Clothes, Upskill, Read"
    - Submit for approval

  Template 2 - Weekly Report:
    - Name: weekly_report
    - Category: UTILITY
    - Language: English
    - Body: "{{1}}"
    - Submit for approval

  Note: Templates usually get approved within 24-48 hours.

STEP 7: Configure Webhook
  - Go to WhatsApp > Configuration
  - Under "Webhook", click "Edit"
  - Callback URL: [Your Cloud Function URL for handleWhatsAppReply]
    (Deploy the function first, then come back to set this)
  - Verify Token: [The custom token you set during GCP setup]
  - Click "Verify and Save"
  - Subscribe to the "messages" webhook field

STEP 8: Generate Access Token
  - Go to WhatsApp > Getting Started
  - Option A (Temporary - 24h): Click "Generate" next to the temporary token
  - Option B (Permanent - Recommended):
    1. Go to Business Settings > System Users
    2. Create a System User (Admin role)
    3. Generate a token with these permissions:
       - whatsapp_business_messaging
       - whatsapp_business_management
    4. This token never expires

STEP 9: Note Your Credentials
  Save these values (you'll need them for GCP Secret Manager):
  - Access Token: (from Step 8)
  - Phone Number ID: (visible in WhatsApp > Getting Started)
  - App Secret: (from App Settings > Basic)
  - Verify Token: (the custom string you chose)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FREE TIER DETAILS:
  - 1,000 service conversations/month (business-initiated)
  - Unlimited user-initiated conversations (when user messages first)
  - Your usage: ~30 daily prompts + 4 weekly reports = ~34 conversations/month
  - Well within the free tier!

VERIFIED BADGE (Green Tick):
  - Requires Meta Business Verification
  - Go to: Business Settings > Security Center > Start Verification
  - Needs: Business documents, website, etc.
  - Processing time: 2-4 weeks
  - Optional: The agent works fully without it

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GUIDE
