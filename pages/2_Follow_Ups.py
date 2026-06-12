import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.sheets import (
    get_followups_df, add_followup, update_followup_status,
    get_due_followups, get_due_count, get_pipeline_df,
)
from utils.constants import USERS, EXHIBITIONS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

inject_css()
require_login()
show_logo()
show_user_bar()

st.title("📅 Follow-ups")
st.markdown("All scheduled follow-ups — they appear in Tasks automatically when due.")

# ── Add Follow-up ─────────────────────────────────────────────────────────────
with st.expander("➕ Add Follow-up"):
    pipeline_df = get_pipeline_df()
    companies = (
        sorted(pipeline_df["Company Name"].dropna().astype(str).unique().tolist())
        if not pipeline_df.empty and "Company Name" in pipeline_df.columns
        else []
    )
    pick = st.selectbox(
        "Company / Client",
        ["✏️ Type a new name"] + companies,
        help="Pick an existing lead, or type any client name (e.g. a cold call).",
    )
    with st.form("add_followup_form"):
        if pick == "✏️ Type a new name":
            company_in = st.text_input("Client / Company Name *",
                                       placeholder="e.g. Al Futtaim Group")
        else:
            company_in = pick
            st.caption(f"Company: **{pick}**")
        a1, a2, a3 = st.columns(3)
        with a1:
            fu_date = st.date_input("Follow-up Date *", value=date.today())
        with a2:
            fu_user = st.selectbox("Assign To", USERS)
        with a3:
            fu_exh = st.selectbox("Exhibition", ["—"] + EXHIBITIONS)
        fu_notes = st.text_input(
            "Notes",
            placeholder="e.g. Cold call — client asked to call back after a week",
        )
        if st.form_submit_button("📅 Save Follow-up", type="primary"):
            if not str(company_in).strip():
                st.error("Client / company name is required.")
            else:
                ok = add_followup({
                    "company_name":  str(company_in).strip(),
                    "exhibition":    "" if fu_exh == "—" else fu_exh,
                    "stage_at_time": "",
                    "followup_date": fu_date.strftime("%d-%b-%Y"),
                    "assigned_to":   fu_user,
                    "notes":         fu_notes,
                    "created_by":    fu_user,
                })
                if ok:
                    get_due_followups.clear()
                    get_due_count.clear()
                    st.success(f"✅ Follow-up saved — it will show in Tasks on {fu_date.strftime('%d %b %Y')}.")
                    st.rerun()
                else:
                    st.error("Could not save. Check Google Sheets connection.")

st.markdown("---")

# ── Filters ───────────────────────────────────────────────────────────────────
fc1, fc2 = st.columns(2)
with fc1:
    filter_person = st.selectbox("Filter by person", ["All"] + USERS)
with fc2:
    filter_status = st.selectbox("Filter by status", ["Pending", "All", "Done"])

# ── Load data ─────────────────────────────────────────────────────────────────
df = get_followups_df()

if df.empty:
    st.info("No follow-ups yet. Add them from a lead card on the Leads page.")
    st.stop()

if filter_person != "All" and "Assigned To" in df.columns:
    df = df[df["Assigned To"] == filter_person]
if filter_status != "All" and "Status" in df.columns:
    df = df[df["Status"] == filter_status]

if df.empty:
    st.info("No follow-ups match the current filter.")
    st.stop()

# Sort by follow-up date ascending
try:
    df = df.copy()
    df["_date_sort"] = pd.to_datetime(df["Follow-up Date"], dayfirst=True, errors="coerce")
    df = df.sort_values("_date_sort").drop(columns=["_date_sort"])
except Exception:
    pass

today = datetime.now().date()

# Counts
total   = len(df)
pending = int((df["Status"] == "Pending").sum()) if "Status" in df.columns else 0
overdue = 0
try:
    overdue = int((
        (df["Status"] == "Pending") &
        (pd.to_datetime(df["Follow-up Date"], dayfirst=True, errors="coerce").dt.date <= today)
    ).sum())
except Exception:
    pass

m1, m2, m3 = st.columns(3)
m1.metric("Total",   total)
m2.metric("Pending", pending)
if overdue:
    m3.metric("Overdue 🔴", overdue)
else:
    m3.metric("Overdue", overdue)

st.markdown("---")

# ── Follow-up list ────────────────────────────────────────────────────────────
for idx, row in df.iterrows():
    company  = row.get("Company Name", "—")
    exh      = row.get("Exhibition",   "")
    fu_date  = row.get("Follow-up Date", "—")
    assigned = row.get("Assigned To",  "—")
    stage    = row.get("Stage at Time", "")
    notes    = row.get("Notes",         "")
    status   = row.get("Status",        "Pending")

    # Determine if overdue
    is_overdue = False
    try:
        is_overdue = (status == "Pending" and
                      pd.to_datetime(fu_date, dayfirst=True).date() <= today)
    except Exception:
        pass

    icon = "🔴" if is_overdue else ("✅" if status == "Done" else "📅")
    label = f"{icon}  {company}  —  {exh}  ·  {fu_date}  ·  👤 {assigned}"

    with st.expander(label):
        lc, rc = st.columns([3, 1])
        with lc:
            if stage:
                st.caption(f"Stage when added: {stage}")
            if notes:
                st.markdown(f"_{notes}_")
            st.caption(f"Status: **{status}**")
        with rc:
            if status != "Done":
                if st.button("✓ Mark Done", key=f"done_{idx}", type="primary", use_container_width=True):
                    update_followup_status(idx, "Done")
                    get_due_followups.clear()
                    st.rerun()
            else:
                if st.button("↩ Reopen", key=f"reopen_{idx}", use_container_width=True):
                    update_followup_status(idx, "Pending")
                    get_due_followups.clear()
                    st.rerun()
