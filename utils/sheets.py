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


# ── EXHIBITOR DATABASE — SEPARATE SPREADSHEETS PER EVENT ────────────────────
#
# Architecture:
#   • Each uploaded list creates its own standalone Google Spreadsheet named
#     "ATK — {event_name} Exhibitors", shared with anyone who has the link.
#   • A "DB Registry" tab in the main ATK Dashboard spreadsheet stores:
#       Event Name | Spreadsheet ID | Event Date | Total | Called | Uploaded By | Created Date
#   • "Open in Google Sheets" opens https://docs.google.com/spreadsheets/d/{event_ss_id}/edit
#     — ONLY that event's data, completely separate from Pipeline/Calendar/etc.

_REGISTRY_HEADERS = [
    "Event Name", "Spreadsheet ID", "Event Date",
    "Total", "Called", "Uploaded By", "Created Date",
]


# ── Registry helpers ─────────────────────────────────────────────────────────

def _get_db_registry_ws():
    """Return the DB Registry worksheet in the main spreadsheet, creating it if needed."""
    sheet = get_sheet()
    if not sheet:
        return None
    try:
        return sheet.worksheet("DB Registry")
    except gspread.exceptions.WorksheetNotFound:
        try:
            ws = sheet.add_worksheet(title="DB Registry", rows=500, cols=len(_REGISTRY_HEADERS))
            ws.append_row(_REGISTRY_HEADERS)
            return ws
        except Exception:
            return None


def _get_registry_records() -> list:
    """Read all DB Registry rows — fast (small table, no caching needed here)."""
    ws = _get_db_registry_ws()
    if not ws:
        return []
    try:
        return ws.get_all_records()
    except Exception:
        return []


def _get_registry_map() -> dict:
    """Return {event_name: record_dict} from the registry."""
    return {r["Event Name"]: r for r in _get_registry_records() if r.get("Event Name")}


def _register_event(event_name: str, ss_id: str, event_date: str,
                    total: int, uploaded_by: str):
    """Add a new row to the DB Registry and clear public caches."""
    ws = _get_db_registry_ws()
    if not ws:
        return
    try:
        ws.append_row([
            event_name, ss_id, event_date, total, 0,
            uploaded_by, datetime.now().strftime("%d-%b-%Y"),
        ])
        get_all_exhibitor_events.clear()
        get_exhibitor_df.clear()
    except Exception:
        pass


def _update_registry_counts(event_name: str, total: int, called: int):
    """Overwrite Total and Called for an event in the registry."""
    sheet = get_sheet()
    if not sheet:
        return
    try:
        ws = sheet.worksheet("DB Registry")
        data = ws.get_all_values()
        if not data:
            return
        headers = data[0]
        name_col   = headers.index("Event Name")
        total_col  = headers.index("Total")
        called_col = headers.index("Called")
        for i, row in enumerate(data[1:], start=2):
            if len(row) > name_col and row[name_col] == event_name:
                ws.update_cell(i, total_col  + 1, total)
                ws.update_cell(i, called_col + 1, called)
                get_all_exhibitor_events.clear()
                return
    except Exception:
        pass


# ── Per-event spreadsheet helpers ────────────────────────────────────────────

def _get_or_create_event_spreadsheet(event_name: str, event_date: str = "",
                                      uploaded_by: str = ""):
    """
    Get (or create) the dedicated standalone Google Spreadsheet for an event.
    New spreadsheets are shared with anyone who has the link (writer access).
    Returns the gspread.Spreadsheet object, or None on failure.
    """
    client = get_client()
    if not client:
        return None

    reg = _get_registry_map()
    if event_name in reg:
        ss_id = reg[event_name].get("Spreadsheet ID", "")
        if ss_id:
            try:
                return client.open_by_key(ss_id)
            except Exception:
                pass  # Fall through — recreate if missing

    # Create a fresh spreadsheet
    try:
        title = f"ATK — {event_name} Exhibitors"
        ss = client.create(title)
        # Share: anyone with the link can edit
        ss.share(None, perm_type="anyone", role="writer", notify=False)
        # Add headers to sheet1
        ws = ss.sheet1
        ws.update_title("Exhibitors")
        ws.append_row(EXHIBITOR_HEADERS)
        # Record in registry (count starts at 0; add_exhibitor_rows updates it)
        _register_event(event_name, ss.id, event_date, 0, uploaded_by)
        return ss
    except Exception:
        return None


def _get_event_ws(event_name: str):
    """Return sheet1 of the event's spreadsheet, or None."""
    reg = _get_registry_map()
    ss_id = reg.get(event_name, {}).get("Spreadsheet ID", "")
    if not ss_id:
        return None
    client = get_client()
    if not client:
        return None
    try:
        return client.open_by_key(ss_id).sheet1
    except Exception:
        return None


# ── Public API ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_all_exhibitor_events() -> list:
    """
    Return summary list for all registered events — cached 60s.
    Each dict: {name, spreadsheet_id, url, event_date, total, called, uploaded_by}
    """
    result = []
    for r in _get_registry_records():
        if not r.get("Event Name"):
            continue
        ss_id = r.get("Spreadsheet ID", "")
        result.append({
            "name":           r["Event Name"],
            "spreadsheet_id": ss_id,
            "url":            f"https://docs.google.com/spreadsheets/d/{ss_id}/edit" if ss_id else "",
            "event_date":     r.get("Event Date") or "—",
            "total":          int(r.get("Total", 0) or 0),
            "called":         int(r.get("Called", 0) or 0),
            "uploaded_by":    r.get("Uploaded By") or "—",
        })
    return result


def get_event_sheet_url(event_name: str) -> str:
    """Return the direct URL for the event's standalone spreadsheet."""
    reg = _get_registry_map()
    ss_id = reg.get(event_name, {}).get("Spreadsheet ID", "")
    return f"https://docs.google.com/spreadsheets/d/{ss_id}/edit" if ss_id else ""


@st.cache_data(ttl=60)
def get_exhibitor_df(event_name: str = None) -> pd.DataFrame:
    """
    Load exhibitor data from the event's dedicated spreadsheet.
    Pass event_name for a single event; omit to load all (slower).
    """
    reg = _get_registry_map()
    if not reg:
        return pd.DataFrame()
    client = get_client()
    if not client:
        return pd.DataFrame()

    targets = [event_name] if event_name else list(reg.keys())
    frames = []
    for ev in targets:
        ss_id = reg.get(ev, {}).get("Spreadsheet ID", "")
        if not ss_id:
            continue
        try:
            ws = client.open_by_key(ss_id).sheet1
            data = ws.get_all_records()
            if data:
                df = pd.DataFrame(data)
                if "Event Name" not in df.columns:
                    df.insert(0, "Event Name", ev)
                frames.append(df)
        except Exception:
            continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def add_exhibitor_rows(rows: list, event_name: str) -> bool:
    """Upload rows to the event's own spreadsheet; create it if it doesn't exist."""
    event_date  = rows[0].get("Event Date", "")  if rows else ""
    uploaded_by = rows[0].get("Uploaded By", "") if rows else ""

    ss = _get_or_create_event_spreadsheet(event_name, event_date, uploaded_by)
    if not ss:
        return False
    try:
        ws = ss.sheet1
        today = datetime.now().strftime("%d-%b-%Y")
        batch = [[
            r.get("Event Name",    event_name),
            r.get("Event Date",    ""),
            r.get("Company Name",  ""),
            r.get("Stand Number",  ""),
            r.get("Hall / Pavilion",""),
            r.get("Country",       ""),
            r.get("Website",       ""),
            r.get("Email",         ""),
            r.get("Phone",         ""),
            r.get("Contact Name",  ""),
            r.get("Call Status",   "Not Called"),
            r.get("Called By",     ""),
            r.get("Call Notes",    ""),
            r.get("Uploaded By",   ""),
            today,
        ] for r in rows]
        ws.append_rows(batch, value_input_option="RAW")
        # Update registry counts
        all_data = ws.get_all_records()
        total  = len(all_data)
        called = sum(1 for d in all_data if str(d.get("Call Status", "")) != "Not Called")
        _update_registry_counts(event_name, total, called)
        get_exhibitor_df.clear()
        return True
    except Exception:
        return False


def update_call_status(event_name: str, company_name: str, status: str,
                       called_by: str, notes: str) -> bool:
    """Update call status, called-by, and notes for a company in its event spreadsheet."""
    ws = _get_event_ws(event_name)
    if not ws:
        return False
    try:
        data = ws.get_all_values()
        if not data:
            return False
        headers = data[0]
        company_col = headers.index("Company Name")
        status_col  = headers.index("Call Status")
        by_col      = headers.index("Called By")
        notes_col   = headers.index("Call Notes")
        for i, row in enumerate(data[1:], start=2):
            if len(row) > company_col and row[company_col] == company_name:
                ws.update_cell(i, status_col + 1, status)
                ws.update_cell(i, by_col     + 1, called_by)
                ws.update_cell(i, notes_col  + 1, notes)
                # Refresh registry counts
                all_records = ws.get_all_records()
                total   = len(all_records)
                called_n = sum(1 for d in all_records
                               if str(d.get("Call Status", "")) != "Not Called")
                _update_registry_counts(event_name, total, called_n)
                get_exhibitor_df.clear()
                return True
        return False
    except Exception:
        return False


def delete_event_exhibitors(event_name: str) -> bool:
    """
    Delete the event's standalone spreadsheet and remove it from the registry.
    """
    reg = _get_registry_map()
    ss_id = reg.get(event_name, {}).get("Spreadsheet ID", "")

    # 1. Delete the spreadsheet itself (gspread client.del_spreadsheet)
    if ss_id:
        client = get_client()
        if client:
            try:
                client.del_spreadsheet(ss_id)
            except Exception:
                pass  # Continue regardless — still remove from registry

    # 2. Remove from DB Registry
    sheet = get_sheet()
    if sheet:
        try:
            ws = sheet.worksheet("DB Registry")
            data = ws.get_all_values()
            if data:
                name_col = data[0].index("Event Name")
                for i, row in enumerate(data[1:], start=2):
                    if len(row) > name_col and row[name_col] == event_name:
                        ws.delete_rows(i)
                        break
        except Exception:
            pass

    get_all_exhibitor_events.clear()
    get_exhibitor_df.clear()
    return True
