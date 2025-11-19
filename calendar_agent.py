# calendar_agent.py

from email_tools import get_recent_emails
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from dateutil.tz import gettz
from dateparser.search import search_dates
import dateparser
import re


LOCAL_TZ = gettz("Asia/Kolkata")


# ----------------------------------------------------------------------
# 1. KEYWORDS
# ----------------------------------------------------------------------

MEETING_KEYWORDS = [
    "meeting", "call", "schedule", "appointment", "invite",
    "zoom", "google meet", "gmeet", "connect", "discussion",
    "reminder", "event"
]

IGNORE_KEYWORDS = [
    "newsletter", "placement", "webinar", "mba", "convocation",
    "admission", "admissions", "admission open", "highlights",
    "recap", "promo", "offer", "blog", "tutorial",
    "digest", "update", "results", "sale", "discount",
    "marketing", "announcement", "course", "training",
    "report", "alumni", "summary"
]


def is_trash_email(text: str):
    t = text.lower()
    return any(w in t for w in IGNORE_KEYWORDS)


def is_meeting_email(text: str):
    t = text.lower()
    return any(w in t for w in MEETING_KEYWORDS)


# ----------------------------------------------------------------------
# 2. DATETIME EXTRACTION
# ----------------------------------------------------------------------

def get_first_datetime_from_text(text: str):
    if not text:
        return None

    txt = re.sub(r"\s+", " ", text).strip()
    now_local = datetime.now(tz=LOCAL_TZ)

    settings = {
        "RETURN_AS_TIMEZONE_AWARE": True,
        "TIMEZONE": "Asia/Kolkata",
        "TO_TIMEZONE": "Asia/Kolkata",
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": now_local,
    }

    try:
        found = search_dates(txt, settings=settings)
    except:
        found = None

    if found:
        for _, dt in found:
            if dt >= now_local - timedelta(minutes=3):
                return dt
        return found[0][1]

    # fallback quick patterns
    m = re.search(
        r'\b(today|tomorrow|tonight|next\s+\w+)\b.*?(\d{1,2}(:\d{2})?\s*(am|pm)?)',
        txt, flags=re.I
    )
    if m:
        dt = dateparser.parse(m.group(0), settings=settings)
        if dt:
            return dt

    m2 = re.search(
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4}',
        txt, flags=re.I
    )
    if m2:
        dt = dateparser.parse(m2.group(0), settings=settings)
        if dt:
            return dt

    return None


def extract_datetime(subject, body):
    for t in (subject, body):
        if t:
            dt = get_first_datetime_from_text(t)
            if dt:
                return dt
    return None


# ----------------------------------------------------------------------
# 3. ADD EVENT TO GOOGLE CALENDAR
# ----------------------------------------------------------------------

def add_to_calendar(subject, body, event_datetime):
    creds = Credentials.from_authorized_user_file(
        "token.json",
        ["https://www.googleapis.com/auth/calendar"]
    )
    service = build("calendar", "v3", credentials=creds)

    end_time = event_datetime + timedelta(hours=1)

    event = {
        "summary": subject,
        "description": body,
        "start": {"dateTime": event_datetime.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
    }

    service.events().insert(calendarId="primary", body=event).execute()


# ----------------------------------------------------------------------
# 4. MAIN WORKFLOW
# ----------------------------------------------------------------------

def process_meeting_emails():
    """
    Fetch last 10 cleaned emails (from All Mail if available),
    filter only real meetings, extract datetime, and add to calendar.
    """
    emails = get_recent_emails(limit=10)

    for subject, body in emails:

        if not subject:
            continue

        combined = f"{subject} {body}".lower()

        # ignore trash
        if is_trash_email(combined):
            print("⏭ Ignored:", subject)
            continue

        # must be meeting-related
        if not is_meeting_email(combined):
            print("⏭ Not a meeting:", subject)
            continue

        dt = extract_datetime(subject, body)

        if not dt:
            print("❌ No date found:", subject)
            continue

        add_to_calendar(subject, body, dt)
        print("✔ Added:", subject)
