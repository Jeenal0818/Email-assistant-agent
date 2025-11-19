# delete_mail.py
import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import traceback

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_ADDRESS")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")  # must match your .env

# Adjust per-folder read limit (newest messages only)
PER_FOLDER_LIMIT = 100


def connect_to_gmail():
    if not EMAIL_USER or not EMAIL_PASS:
        raise ValueError("Missing EMAIL_USER or EMAIL_APP_PASSWORD in .env")
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    return mail


def _decode_subject(raw):
    if not raw:
        return ""
    parts = decode_header(raw)
    text_parts = []
    for p, enc in parts:
        try:
            if isinstance(p, bytes):
                text_parts.append(p.decode(enc or "utf-8", errors="ignore"))
            else:
                text_parts.append(str(p))
        except Exception:
            try:
                text_parts.append(p.decode("utf-8", errors="ignore"))
            except:
                text_parts.append(str(p))
    return "".join(text_parts)


def _list_mailboxes(mail):
    """Return decoded list of mailbox names available on the server."""
    status, boxes = mail.list()
    if status != "OK":
        return []
    names = []
    for b in boxes:
        if isinstance(b, bytes):
            b = b.decode()
        # mailbox response format varies; try to extract name after the last space or quoted part
        # Examples: '(\\HasNoChildren) "/" "INBOX"'  or '("*" "/" "[Gmail]/Sent Mail")'
        try:
            # try to find quoted name
            if '"' in b:
                parts = b.split('"')
                # last quoted token often the mailbox name
                name = parts[-2]
            else:
                parts = b.split()
                name = parts[-1]
            names.append(name)
        except Exception:
            continue
    # unique
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen


def _find_trash_folder(mailboxes):
    # common variants
    candidates = ["[Gmail]/Trash", "[Gmail]/Bin", "Trash", "Bin", "[Gmail]/Deleted Messages", "Deleted"]
    for c in candidates:
        if c in mailboxes:
            return c
    # fallback: any mailbox containing 'trash' or 'bin' (case-insensitive)
    for m in mailboxes:
        if "trash" in m.lower() or "bin" in m.lower() or "deleted" in m.lower():
            return m
    return None


def delete_email_exact(subject_keyword, per_folder_limit=PER_FOLDER_LIMIT, verbose=True):
    """
    Exact subject match only (case-insensitive).
    Tries to apply Gmail label \Trash (fast). If not available, copies to Trash folder and deletes original.
    Returns number of messages moved to trash.
    """
    if not subject_keyword or not subject_keyword.strip():
        print("❌ Subject cannot be empty.")
        return 0

    subject_keyword = subject_keyword.strip().lower()

    mail = connect_to_gmail()
    try:
        mailboxes = _list_mailboxes(mail)
        if verbose:
            print("Mailboxes found:", ", ".join(mailboxes))
    except Exception:
        mailboxes = []
    # Preferred folders to check; will be filtered to what actually exists
    preferred = ["INBOX", "[Gmail]/Sent Mail", "[Gmail]/All Mail", "Sent", "Sent Mail"]
    folders = [f for f in preferred if f in mailboxes]
    # If none of preferred found, fall back to some mailboxes returned
    if not folders:
        # choose up to three meaningful folders (INBOX first)
        if "INBOX" in mailboxes:
            folders = ["INBOX"]
        else:
            folders = mailboxes[:3]

    trash_folder = _find_trash_folder(mailboxes)  # may be None

    total_moved = 0
    if verbose:
        print(f"\n🔍 Searching exact subject: '{subject_keyword}' in {len(folders)} folder(s): {folders}\n")

    for folder in folders:
        if verbose:
            print(f"→ Checking: {folder}")
        # attempt to select with and without quotes if necessary
        selected = False
        for attempt_name in (folder, f'"{folder}"'):
            try:
                status, _ = mail.select(attempt_name)
                if status == "OK":
                    selected = True
                    break
            except Exception:
                continue
        if not selected:
            if verbose:
                print(f"   ⚠ Cannot open folder: {folder}")
            continue

        status, data = mail.search(None, "ALL")
        if status != "OK":
            if verbose:
                print("   ⚠ Search failed in folder.")
            continue

        ids = data[0].split()
        if not ids:
            if verbose:
                print("   • No messages found.")
            continue

        # limit to most recent per_folder_limit
        ids_to_check = ids[-per_folder_limit:]

        folder_moved = 0
        for msg_id in reversed(ids_to_check):  # newest first
            try:
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subj = _decode_subject(msg.get("Subject", "")).strip()
                if subj.lower() != subject_keyword:
                    continue  # exact match only

                # Try Gmail label approach first (fast, does not require explicit trash folder)
                moved = False
                try:
                    # set label \Trash via X-GM-LABELS (Gmail extension)
                    status_store, resp = mail.store(msg_id, '+X-GM-LABELS', '\\Trash')
                    if status_store == 'OK':
                        moved = True
                        if verbose:
                            print(f"   🗑 Moved to Trash (label) → {subj}")
                    else:
                        moved = False
                except Exception:
                    moved = False

                # Fallback: if label not supported, try to copy to actual trash folder then mark deleted
                if not moved:
                    if trash_folder:
                        try:
                            # copy to trash folder
                            # use quoted folder name if contains space/special chars
                            copy_folder = trash_folder
                            status_copy, _ = mail.copy(msg_id, copy_folder)
                            if status_copy == 'OK':
                                # mark original deleted (so inbox copy will be removed upon expunge)
                                mail.store(msg_id, '+FLAGS', '\\Deleted')
                                mail.expunge()
                                moved = True
                                if verbose:
                                    print(f"   🗑 Copied to {copy_folder} and removed original → {subj}")
                            else:
                                moved = False
                        except Exception:
                            moved = False

                # Last resort: mark \Deleted (this may not move to Trash in Gmail; use with caution)
                if not moved:
                    try:
                        mail.store(msg_id, '+FLAGS', '\\Deleted')
                        mail.expunge()
                        moved = True
                        if verbose:
                            print(f"   🗑 Marked Deleted (fallback) → {subj}")
                    except Exception:
                        moved = False

                if moved:
                    folder_moved += 1
                    total_moved += 1

            except Exception as e:
                if verbose:
                    print("   ⚠ Error reading message:", e)
                    traceback.print_exc()
                continue

        if folder_moved == 0 and verbose:
            print("   • No exact matches in this folder.")
        elif verbose:
            print(f"   ✔ Moved {folder_moved} message(s) from {folder}.")

    try:
        mail.close()
    except:
        pass
    try:
        mail.logout()
    except:
        pass

    if verbose:
        print(f"\n✔ Completed. Total messages moved to Trash (or marked deleted): {total_moved}\n")
    return total_moved
