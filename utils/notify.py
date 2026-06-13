"""
Instant email notifications sent from the Streamlit app.
Reads Gmail credentials from st.secrets. Silently does nothing if creds are
missing, so the app never breaks because email isn't configured yet.
"""
import streamlit as st
from utils.email_util import send_email, task_assigned_html, followup_assigned_html
from utils.constants import USER_EMAILS


def _creds():
    addr = str(st.secrets.get("GMAIL_ADDRESS", "")).strip()
    pwd  = str(st.secrets.get("GMAIL_APP_PASSWORD", "")).strip()
    return addr, pwd


def _link():
    return str(st.secrets.get("DASHBOARD_URL", "")).strip()


def notify_task_assigned(title, assigned_to, assigned_by, priority, due, notes):
    """Email the assignee that a new task was assigned to them."""
    if assigned_to == assigned_by:
        return
    to_addr = USER_EMAILS.get(assigned_to)
    addr, pwd = _creds()
    if not (to_addr and addr and pwd):
        return
    html = task_assigned_html(title, assigned_by, priority, due, notes, link=_link())
    send_email(to_addr, f"📋 New task for you: {title}", html, addr, pwd)


def notify_followup_assigned(assigned_to, assigned_by, company, exhibition, fu_date,
                             notes, contact_name="", contact_phone="", contact_email=""):
    """Email the assignee that a follow-up was assigned to them, with contact details."""
    if assigned_to == assigned_by:
        return
    to_addr = USER_EMAILS.get(assigned_to)
    addr, pwd = _creds()
    if not (to_addr and addr and pwd):
        return
    html = followup_assigned_html(
        assigned_by, company, exhibition, fu_date, notes,
        contact_name, contact_phone, contact_email, link=_link(),
    )
    send_email(to_addr, f"📅 New follow-up for you: {company} ({fu_date})", html, addr, pwd)
