import os
import smtplib
import re
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

IMAP_HOST = "imap.gmail.com"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# ------------------------------------------------------
# CLEAN BODY HELPER
# ------------------------------------------------------
def clean_body(raw):
    if not raw:
        return ""

    # strip HTML
    text = re.sub(r"<[^>]+>", " ", raw)

    # strip URLs
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ------------------------------------------------------
# SEND EMAIL
# ------------------------------------------------------
def send_real_email(recipient, subject, body):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise ValueError("Missing EMAIL_ADDRESS or EMAIL_PASSWORD in .env file")

    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"📨 Email successfully sent to {recipient}!")
    except Exception as e:
        print("⚠️ Failed to send email:", e)


# ------------------------------------------------------
# CONNECT IMAP
# ------------------------------------------------------
def connect():
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise ValueError("Missing EMAIL env vars")

    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    return mail


def safe_select(mail, folder):
    """Select folder safely with quotes."""
    try:
        status, _ = mail.select(f'"{folder}"', readonly=True)
        return status == "OK"
    except:
        return False


# ------------------------------------------------------
# SHOW LATEST EMAILS (clean)
# ------------------------------------------------------
def read_latest_emails(n=5):
    try:
        mail = connect()

        if not safe_select(mail, "INBOX"):
            print("❌ Cannot access INBOX")
            return

        result, data = mail.search(None, "ALL")
        mail_ids = data[0].split()

        if not mail_ids:
            print("📭 No emails.")
            return

        print(f"📨 Showing latest {n} emails:\n")

        for i in mail_ids[-n:]:
            _, msg_data = mail.fetch(i, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject_raw = decode_header(msg["Subject"])[0]
            subject = subject_raw[0]
            if isinstance(subject, bytes):
                subject = subject.decode(errors="ignore")

            print(f"📌 {subject}")

        mail.logout()
    except Exception as e:
        print("⚠️ Error:", e)


# ------------------------------------------------------
# FETCH UNSEEN EMAILS (used by calendar agent)
# ------------------------------------------------------
def fetch_unseen_emails(limit=10):
    mail = connect()

    if not safe_select(mail, "INBOX"):
        print("❌ Cannot access INBOX")
        return []

    status, msgs = mail.search(None, "ALL")
    ids = msgs[0].split()

    if not ids:
        return []

    ids = ids[-limit:]
    emails = []

    for uid in reversed(ids):
        _, data = mail.fetch(uid, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        subject_raw = decode_header(msg["Subject"])[0]
        subject = subject_raw[0]
        if isinstance(subject, bytes):
            subject = subject.decode(errors="ignore")

        # extract clean body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ["text/plain", "text/html"]:
                    try:
                        raw_body = part.get_payload(decode=True).decode(errors="ignore")
                    except:
                        raw_body = ""
                    body = clean_body(raw_body)
                    break
        else:
            try:
                raw_body = msg.get_payload(decode=True).decode(errors="ignore")
                body = clean_body(raw_body)
            except:
                body = ""

        emails.append((subject, body))

    mail.logout()
    return emails


# ------------------------------------------------------
# GET RECENT EMAILS (All Mail → inbox fallback)
# ------------------------------------------------------
def get_recent_emails(limit=10):
    mail = connect()

    folders = ["[Gmail]/All Mail", "[Gmail]/Allmail", "INBOX"]
    chosen = None

    for f in folders:
        if safe_select(mail, f):
            chosen = f
            break

    if not chosen:
        print("❌ Cannot access All Mail or INBOX")
        return []

    print(f"📌 Reading emails from: {chosen}")

    status, msgs = mail.search(None, "ALL")
    if status != "OK":
        print("❌ Search failed")
        return []

    ids = msgs[0].split()
    if not ids:
        print("❌ No emails")
        return []

    ids = ids[-limit:]
    emails = []

    for uid in reversed(ids):
        _, data = mail.fetch(uid, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        subject = msg.get("Subject", "")
        body = ""

        # extract clean body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ["text/plain", "text/html"]:
                    try:
                        raw_body = part.get_payload(decode=True).decode(errors="ignore")
                    except:
                        raw_body = ""
                    body = clean_body(raw_body)
                    break
        else:
            try:
                raw_body = msg.get_payload(decode=True).decode(errors="ignore")
                body = clean_body(raw_body)
            except:
                body = ""

        emails.append((subject, body))

    mail.close()
    mail.logout()
    return emails
