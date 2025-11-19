# Email Assistant Automation System

A fully automated Gmail–Calendar assistant built in Python that can:

- Send emails using Gmail SMTP
- Understand natural language commands ("send mail to X with subject Y saying Z")
- Read and clean incoming emails
- Detect meeting-related emails
- Extract dates/times intelligently
- Automatically add events to Google Calendar
- Safely delete emails with exact subject match
- Search Inbox / Sent / All Mail efficiently

------------------------------------------------------------

## Project Structure

    Email Assistant/
    │
    ├── main.py                   # Runs the meeting → calendar workflow
    ├── calendar_agent.py         # Extracts meetings and creates calendar events
    ├── email_tools.py            # Send, read, clean, parse emails
    ├── delete_mail.py            # Safe, exact-match deletion logic
    ├── token.json                # Auto-created after OAuth login
    ├── credentials.json          # Google OAuth client credentials
    ├── .env                      # Secret credentials for Gmail login
    └── README.md                 # Documentation

------------------------------------------------------------

## Environment Setup

Create a `.env` file with:

    EMAIL_ADDRESS=your_email@gmail.com
    EMAIL_PASSWORD=your_app_password
    IMAP_HOST=imap.gmail.com

Use a Gmail App Password  
Enable IMAP in Gmail settings

------------------------------------------------------------

## Installation

Run:

    pip install python-dotenv google-api-python-client google-auth-oauthlib google-auth-httplib2 dateparser python-dateutil

------------------------------------------------------------

## Google Calendar Setup

1. Enable Google Calendar API in Google Cloud  
2. Create OAuth Client ID → Desktop App  
3. Save `credentials.json` into project folder  
4. Authenticate:

       python main.py

This creates `token.json` automatically.

------------------------------------------------------------

## Run the Meeting-to-Calendar Agent

    python main.py

This executes:

    from calendar_agent import process_meeting_emails
    process_meeting_emails()

The agent will:

- Read latest 10 emails  
- Skip newsletters/promotions/MBA trash  
- Detect meeting-related mails  
- Extract datetime  
- Add event to Google Calendar  

------------------------------------------------------------

## Send Email Using Natural Language

    from email_tools import handle_email_command
    handle_email_command("Send mail to test@example.com with subject dinner saying let's meet tomorrow at 7 pm")

------------------------------------------------------------

## Delete Email by Exact Subject (Safe)

    from delete_mail import delete_email_exact
    delete_email_exact("Lunch")

- Searches Inbox / Sent / All Mail  
- Exact subject match only  
- Moves to Trash (never permanently deletes)  

------------------------------------------------------------

## Core Features

### Smart Email Cleaning
Removes:
- HTML
- URLs
- Extra whitespace

### Smart Meeting Detection
Ignore keywords:
newsletter, mba, convocation, highlights, recap, promo, digest, update, tutorial, offer, placement, alumni…

Meeting keywords:
meeting, schedule, call, appointment, invite, zoom, google meet, discussion, reminder, event…

### Smart Date Extraction
Understands:
- "tomorrow at 6:30 pm"
- "next Monday 10am"
- "today at 4pm"
- "12 Feb 2025"
- "15/02/2025"
- "tonight 8pm"

Converted to Asia/Kolkata timezone.

### Safe Folder Handling
- Prefers All Mail  
- Falls back to INBOX  
- Delete script identifies Trash/Bin safely  

------------------------------------------------------------

