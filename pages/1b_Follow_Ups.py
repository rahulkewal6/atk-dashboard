import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.sheets import get_followups_df, update_followup_status, get_due_followups
from utils.constants import USERS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

st.set_page_config(page_title="Follow-ups", page_icon="📅", layout="wide")
inject_css()
require_login()
show_logo()
show_user_bar()

st.title("📅 Follow-ups")
st.markdown("All follow-ups scheduled from your leads.")

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
