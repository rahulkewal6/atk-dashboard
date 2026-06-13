"""
ATK digest email — runs on a schedule from GitHub Actions (NOT inside Streamlit).

Sends each team member a summary of their pending tasks, follow-ups due, and
leads needing action.

Modes (env MODE):
  weekahead  → Sunday night: everything pending for the coming week
  checkin    → Mon/Wed/Fri morning: what's due now / overdue

Reads everything from env (set as GitHub repo Secrets):
  GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GOOGLE_SHEET_ID, GCP_SERVICE_ACCOUNT
  DASHBOARD_URL (optional)
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Make utils/ importable when run as `python scripts/atk_digest.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from utils.constants import USER_EMAILS, STAGE_TIERS
from utils.email_util import send_email, wrap_html

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _parse_date(value):
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except Exception:
            continue
    return None


def _records(ws_lookup, tab):
    try:
        return ws_lookup.worksheet(tab).get_all_records()
    except Exception:
        return []


def _list_block(title, items):
    if not items:
        return ""
    lis = "".join(
        f'<li style="margin:4px 0;">{it}</li>' for it in items
    )
    return (
        f'<p style="margin:16px 0 4px;font-weight:700;color:#FF6600;">{title}</p>'
        f'<ul style="margin:0;padding-left:20px;color:#222;">{lis}</ul>'
    )


def main():
    mode = os.environ.get("MODE", "checkin").strip()
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

    tasks = _records(book, "ATK Tasks")
    followups = _records(book, "ATK Followups")
    pipeline = _records(book, "Pipeline")

    today = datetime.now().date()
    horizon = today + timedelta(days=7) if mode == "weekahead" else today

    # Leads needing action (team-wide)
    red_leads = [
        str(r.get("Company Name", ""))
        for r in pipeline
        if STAGE_TIERS.get(str(r.get("Current Stage", "")), "") == "red"
    ]
    red_leads = [c for c in red_leads if c]

    label = "Week ahead" if mode == "weekahead" else "Today"
    subject_date = today.strftime("%a %d %b")

    for user, email in USER_EMAILS.items():
        # Their pending tasks within the horizon
        my_tasks = []
        for t in tasks:
            if str(t.get("Assigned To", "")) != user:
                continue
            if str(t.get("Status", "")) == "Done":
                continue
            d = _parse_date(t.get("Due Date", ""))
            if d is None or d <= horizon:
                due_txt = t.get("Due Date", "")
                flag = " ⚠️ overdue" if (d and d < today) else ""
                my_tasks.append(f"[{t.get('Priority','')}] {t.get('Title','')} — due {due_txt}{flag}")

        # Their follow-ups within the horizon
        my_fus = []
        for f in followups:
            if str(f.get("Assigned To", "")) != user:
                continue
            if str(f.get("Status", "")) == "Done":
                continue
            d = _parse_date(f.get("Follow-up Date", ""))
            if d is None or d <= horizon:
                flag = " ⚠️ overdue" if (d and d < today) else ""
                my_fus.append(f"{f.get('Company Name','')} — {f.get('Follow-up Date','')}{flag}")

        # Skip empty check-ins; always send the Sunday week-ahead
        if mode != "weekahead" and not (my_tasks or my_fus):
            continue

        inner = f'<p style="margin:0 0 4px;">Hi {user},</p>'
        if mode == "weekahead":
            inner += '<p style="margin:0;color:#666;">Here\'s what\'s on your plate for the week.</p>'
        inner += _list_block(f"📋 Your tasks ({len(my_tasks)})", my_tasks or ["Nothing pending 🎉"])
        inner += _list_block(f"📅 Follow-ups due ({len(my_fus)})", my_fus or ["None due"])
        if red_leads:
            shown = red_leads[:6]
            extra = f" …and {len(red_leads) - 6} more" if len(red_leads) > 6 else ""
            inner += _list_block(f"🔴 Leads needing action ({len(red_leads)})", shown + ([extra] if extra else []))

        html = wrap_html(f"☀️ Your ATK {label} — {subject_date}", inner, link=link)
        subject = f"☀️ ATK {label} — {subject_date}"
        ok = send_email(email, subject, html, gmail, pwd)
        print(f"{'sent' if ok else 'FAILED'}: {user} <{email}>")


if __name__ == "__main__":
    main()
