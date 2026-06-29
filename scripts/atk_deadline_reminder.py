"""
"Task due in ~1 hour" email reminder — runs every 15 min from GitHub Actions.

For each task that is NOT done, has a due date + time, falls due within the
next ~75 minutes, and hasn't already been reminded, it emails the assignee and
marks "Reminder Sent" = yes so it only sends once.

All times are UAE (UTC+4). Reads from env (GitHub repo Secrets):
  GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GOOGLE_SHEET_ID, GCP_SERVICE_ACCOUNT
  DASHBOARD_URL (optional)
"""
import os
import sys
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from utils.constants import USER_EMAILS
from utils.email_util import send_email, task_due_html, followup_due_html
from utils.timeutil import time_with_ist

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

WINDOW_MIN = 75  # send when the task is due within this many minutes


def _due_datetime(date_str, time_str):
    """Combine '16-Jun-2026' + '06:00 PM' into a datetime, or None."""
    date_str = str(date_str).strip()
    time_str = str(time_str).strip()
    if not (date_str and time_str):
        return None
    for tfmt in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(f"{date_str} {time_str}", f"%d-%b-%Y {tfmt}")
        except Exception:
            continue
    return None


def main():
    gmail = os.environ.get("GMAIL_ADDRESS", "").strip()
    pwd = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "").strip()
    link = os.environ.get("DASHBOARD_URL", "").strip()
    sa_json = os.environ.get("GCP_SERVICE_ACCOUNT", "")

    if not (gmail and pwd and sheet_id and sa_json):
        print("Missing required environment variables; aborting.")
        return

    client = gspread.service_account_from_dict(json.loads(sa_json), scopes=SCOPES)
    book = client.open_by_key(sheet_id)
    now_uae = datetime.utcnow() + timedelta(hours=4)
    cutoff = now_uae + timedelta(minutes=WINDOW_MIN)

    # ── Tasks due within ~1 hour ──────────────────────────────────────────────
    try:
        ws = book.worksheet("ATK Tasks")
        headers = ws.row_values(1)
        if "Reminder Sent" in headers and "Due Time" in headers:
            reminder_col = headers.index("Reminder Sent") + 1
            for i, rec in enumerate(ws.get_all_records()):
                if str(rec.get("Status", "")) == "Done":
                    continue
                if str(rec.get("Reminder Sent", "")).strip().lower() == "yes":
                    continue
                due_dt = _due_datetime(rec.get("Due Date", ""), rec.get("Due Time", ""))
                if not due_dt or not (now_uae <= due_dt <= cutoff):
                    continue
                to_addr = USER_EMAILS.get(str(rec.get("Assigned To", "")))
                if not to_addr:
                    continue
                when = f"{rec.get('Due Date','')} · {time_with_ist(rec.get('Due Time',''))}".strip(" ·")
                html = task_due_html(rec.get("Title", ""), when, rec.get("Priority", ""),
                                     rec.get("Notes", ""), link=link)
                if send_email(to_addr, f"⏰ Task due soon: {rec.get('Title','')}", html, gmail, pwd):
                    ws.update_cell(i + 2, reminder_col, "yes")
                    print(f"task reminded: {to_addr} — {rec.get('Title','')}")
    except Exception as e:
        print("Tasks reminder skipped:", e)

    # ── Follow-ups due within ~1 hour ─────────────────────────────────────────
    try:
        ws = book.worksheet("ATK Followups")
        headers = ws.row_values(1)
        if "Reminder Sent" in headers and "Follow-up Time" in headers:
            reminder_col = headers.index("Reminder Sent") + 1
            for i, rec in enumerate(ws.get_all_records()):
                if str(rec.get("Status", "")) == "Done":
                    continue
                if str(rec.get("Reminder Sent", "")).strip().lower() == "yes":
                    continue
                due_dt = _due_datetime(rec.get("Follow-up Date", ""), rec.get("Follow-up Time", ""))
                if not due_dt or not (now_uae <= due_dt <= cutoff):
                    continue
                to_addr = USER_EMAILS.get(str(rec.get("Assigned To", "")))
                if not to_addr:
                    continue
                when = f"{rec.get('Follow-up Date','')} · {time_with_ist(rec.get('Follow-up Time',''))}".strip(" ·")
                html = followup_due_html(rec.get("Company Name", ""), when,
                                         rec.get("Exhibition", ""), rec.get("Notes", ""), link=link)
                if send_email(to_addr, f"⏰ Follow-up due soon: {rec.get('Company Name','')}", html, gmail, pwd):
                    ws.update_cell(i + 2, reminder_col, "yes")
                    print(f"followup reminded: {to_addr} — {rec.get('Company Name','')}")
    except Exception as e:
        print("Follow-ups reminder skipped:", e)


if __name__ == "__main__":
    try:
        main()
        print("Deadline reminder run complete.")
    except Exception:
        import traceback
        traceback.print_exc()
        print("Deadline reminder hit a transient error — skipping this run.")
        # Exit cleanly so a one-off hiccup doesn't spam failure emails
        sys.exit(0)
