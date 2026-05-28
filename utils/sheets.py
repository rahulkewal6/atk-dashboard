import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from datetime import datetime
from utils.constants import EXHIBITOR_HEADERS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "ATK Dashboard"


@st.cache_resource
def get_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        return None


def get_sheet():
    client = get_client()
    if not client:
        return None
    try:
        return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
    except Exception:
        return None


def get_pipeline_df():
    sheet = get_sheet()
    if not sheet:
        return pd.DataFrame()
    try:
        ws = sheet.worksheet("Pipeline")
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def add_lead(data: dict):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        ws = sheet.worksheet("Pipeline")
        row = [
            data.get("company_name", ""),
            data.get("exhibition", ""),
            data.get("source", ""),
            data.get("contact_email", ""),
            data.get("contact_name", ""),
            data.get("contact_phone", ""),
            data.get("current_stage", "Hot Lead (Apollo)"),
            data.get("brief_version", 1),
            data.get("design_options_sent", 0),
            data.get("vendor_quote", ""),
            data.get("margin", ""),
            data.get("client_quote", ""),
            data.get("discount_given", "No"),
            data.get("notes", ""),
            data.get("updated_by", ""),
            datetime.now().strftime("%d-%b-%Y"),
        ]
        ws.append_row(row)
        return True
    except Exception:
        return False


def update_lead_field(row_number: int, field: str, value, updated_by: str):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        ws = sheet.worksheet("Pipeline")
        headers = ws.row_values(1)
        if field not in headers:
            return False
        col_index = headers.index(field) + 1
        ws.update_cell(row_number + 1, col_index, value)
        if "Last Updated By" in headers:
            upd_col = headers.index("Last Updated By") + 1
            ws.update_cell(row_number + 1, upd_col, updated_by)
        return True
    except Exception:
        return False


def log_stage_change(company_name: str, new_stage: str, updated_by: str, notes: str = ""):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        ws = sheet.worksheet("Stage History")
        ws.append_row([
            company_name,
            new_stage,
            updated_by,
            datetime.now().strftime("%d-%b-%Y %H:%M"),
            notes,
        ])
        return True
    except Exception:
        return False


def get_stage_history(company_name: str):
    sheet = get_sheet()
    if not sheet:
        return pd.DataFrame()
    try:
        ws = sheet.worksheet("Stage History")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        return df[df["Company Name"] == company_name]
    except Exception:
        return pd.DataFrame()


def get_calendar_df():
    sheet = get_sheet()
    if not sheet:
        return pd.DataFrame()
    try:
        ws = sheet.worksheet("Event Calendar")
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def add_calendar_event(data: dict):
    sheet = get_sheet()
    if not sheet:
        return False
    try:
        ws = sheet.worksheet("Event Calendar")
        ws.append_row([
            data.get("event_name", ""),
            data.get("venue", ""),
            data.get("city", ""),
            data.get("start_date", ""),
            data.get("end_date", ""),
            data.get("exhibitor_count", 0),
            data.get("official_url", ""),
            data.get("verification_status", "UNVERIFIED"),
            data.get("last_verified", ""),
            data.get("date_priority", ""),
            data.get("exhibitor_priority", ""),
            data.get("notes", ""),
        ])
        return True
    except Exception:
        return False


# ── EXHIBITOR DATABASE ──────────────────────────────────────────────────────

def _get_exhibitor_ws():
    """Return the Exhibitor Lists worksheet, creating it if it doesn't exist."""
    sheet = get_sheet()
    if not sheet:
        return None
    try:
        return sheet.worksheet("Exhibitor Lists")
    except gspread.exceptions.WorksheetNotFound:
        try:
            ws = sheet.add_worksheet(title="Exhibitor Lists", rows=5000, cols=len(EXHIBITOR_HEADERS))
            ws.append_row(EXHIBITOR_HEADERS)
            return ws
        except Exception:
            return None


@st.cache_data(ttl=60)
def get_exhibitor_df() -> pd.DataFrame:
    ws = _get_exhibitor_ws()
    if not ws:
        return pd.DataFrame()
    try:
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def add_exhibitor_rows(rows: list) -> bool:
    """Append a list of exhibitor dicts to the Exhibitor Lists sheet."""
    ws = _get_exhibitor_ws()
    if not ws:
        return False
    try:
        today = datetime.now().strftime("%d-%b-%Y")
        batch = []
        for r in rows:
            batch.append([
                r.get("Event Name", ""),
                r.get("Event Date", ""),
                r.get("Company Name", ""),
                r.get("Stand Number", ""),
                r.get("Hall / Pavilion", ""),
                r.get("Country", ""),
                r.get("Website", ""),
                r.get("Email", ""),
                r.get("Phone", ""),
                r.get("Contact Name", ""),
                r.get("Call Status", "Not Called"),
                r.get("Called By", ""),
                r.get("Call Notes", ""),
                r.get("Uploaded By", ""),
                today,
            ])
        ws.append_rows(batch, value_input_option="RAW")
        get_exhibitor_df.clear()
        return True
    except Exception:
        return False


def update_call_status(event_name: str, company_name: str, status: str, called_by: str, notes: str) -> bool:
    """Update call status for a specific company in the Exhibitor Lists sheet."""
    ws = _get_exhibitor_ws()
    if not ws:
        return False
    try:
        data = ws.get_all_values()
        if not data:
            return False
        headers = data[0]
        try:
            event_col   = headers.index("Event Name")
            company_col = headers.index("Company Name")
            status_col  = headers.index("Call Status")
            by_col      = headers.index("Called By")
            notes_col   = headers.index("Call Notes")
        except ValueError:
            return False
        for i, row in enumerate(data[1:], start=2):  # 1-indexed, skip header
            if (len(row) > max(event_col, company_col) and
                    row[event_col] == event_name and
                    row[company_col] == company_name):
                ws.update_cell(i, status_col + 1, status)
                ws.update_cell(i, by_col + 1, called_by)
                ws.update_cell(i, notes_col + 1, notes)
                get_exhibitor_df.clear()
                return True
        return False
    except Exception:
        return False


def delete_event_exhibitors(event_name: str) -> bool:
    """Delete all rows for a given event from the Exhibitor Lists sheet."""
    ws = _get_exhibitor_ws()
    if not ws:
        return False
    try:
        data = ws.get_all_values()
        if not data:
            return True
        headers = data[0]
        try:
            event_col = headers.index("Event Name")
        except ValueError:
            return False
        rows_to_delete = [
            i + 1
            for i, row in enumerate(data[1:], start=1)
            if len(row) > event_col and row[event_col] == event_name
        ]
        for row_idx in reversed(rows_to_delete):
            ws.delete_rows(row_idx + 1)
        get_exhibitor_df.clear()
        return True
    except Exception:
        return False
