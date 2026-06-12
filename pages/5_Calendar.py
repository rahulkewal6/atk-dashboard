import streamlit as st
import pandas as pd
from datetime import date, datetime
from utils.sheets import get_calendar_df, add_calendar_event
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

inject_css()
require_login()
show_logo()
show_user_bar()

st.title("📅 Event Calendar")
st.markdown("Upcoming exhibitions — re-verify any event within 30 days of its start date.")

# --- ADD EVENT ---
with st.expander("➕ Add Event"):
    with st.form("add_event_form"):
        col1, col2 = st.columns(2)
        with col1:
            event_name = st.text_input("Event Name *")
            venue = st.text_input("Venue")
            city = st.text_input("City")
            country = st.text_input("Country")
        with col2:
            start_date = st.date_input("Start Date", value=date.today())
            end_date = st.date_input("End Date", value=date.today())
            exhibitor_count = st.number_input("Est. Exhibitor Count", min_value=0, value=0)
            official_url = st.text_input("Official Website URL")

        col1, col2 = st.columns(2)
        with col1:
            verified = st.selectbox("Verification Status", ["VERIFIED", "UNVERIFIED", "CONFLICTING"])
        with col2:
            last_verified = st.date_input("Last Verified Date", value=date.today())

        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Event")

        if submitted:
            if not event_name:
                st.error("Event name is required.")
            else:
                days_away = (start_date - date.today()).days
                date_priority = "High" if days_away <= 90 else "Medium" if days_away <= 180 else "Low"
                exhibitor_priority = "High" if exhibitor_count >= 500 else "Medium" if exhibitor_count >= 200 else "Low"

                ok = add_calendar_event({
                    "event_name": event_name,
                    "venue": venue,
                    "city": city,
                    "start_date": start_date.strftime("%d-%b-%Y"),
                    "end_date": end_date.strftime("%d-%b-%Y"),
                    "exhibitor_count": exhibitor_count,
                    "official_url": official_url,
                    "verification_status": verified,
                    "last_verified": last_verified.strftime("%d-%b-%Y"),
                    "date_priority": date_priority,
                    "exhibitor_priority": exhibitor_priority,
                    "notes": notes,
                })
                if ok:
                    st.success(f"Event added: {event_name}")
                    st.rerun()
                else:
                    st.error("Could not save. Check Google Sheets connection.")

st.markdown("---")

# --- LOAD CALENDAR ---
df = get_calendar_df()

if df.empty:
    st.info("No events yet. Add your first event above.")
    st.stop()

# --- FLAG EVENTS NEEDING RE-VERIFICATION ---
today = date.today()
needs_reverify = []

if "Start Date" in df.columns and "Last Verified" in df.columns:
    for _, row in df.iterrows():
        try:
            start = datetime.strptime(str(row["Start Date"]), "%d-%b-%Y").date()
            last_v = datetime.strptime(str(row["Last Verified"]), "%d-%b-%Y").date()
            days_to_event = (start - today).days
            days_since_verify = (today - last_v).days
            if days_to_event <= 30 or days_since_verify >= 30:
                needs_reverify.append(row.get("Event Name", ""))
        except Exception:
            pass

if needs_reverify:
    st.warning(f"⚠️ **{len(needs_reverify)} event(s) need re-verification:** {', '.join(needs_reverify)}")

# --- PRIORITY TABLE ---
st.subheader("Events by Priority")

priority_order = {"High": 0, "Medium": 1, "Low": 2}

if "Date Priority" in df.columns:
    df["_priority_sort"] = df["Date Priority"].map(priority_order).fillna(3)
    df = df.sort_values("_priority_sort").drop(columns=["_priority_sort"])

display_cols = [c for c in [
    "Event Name", "City", "Start Date", "End Date",
    "Exhibitor Count", "Date Priority", "Exhibitor Priority",
    "Verification Status", "Last Verified", "Official URL"
] if c in df.columns]

# Highlight rows needing re-verification
def highlight_reverify(row):
    if row.get("Event Name", "") in needs_reverify:
        return ["background-color: #fff3cd"] * len(row)
    return [""] * len(row)

styled = df[display_cols].style.apply(highlight_reverify, axis=1)
st.dataframe(styled, use_container_width=True)
st.caption("🟡 Yellow rows need re-verification before scraping.")
