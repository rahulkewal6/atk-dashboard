import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from utils.sheets import (
    get_followups_df, add_followup, update_followup_status,
    update_followup_fields, delete_followup,
    get_due_followups, get_due_count, get_pipeline_df,
)
from utils.constants import USERS, EXHIBITIONS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, can_modify, get_display_name
from utils.notify import notify_followup_assigned

inject_css()
require_login()
show_logo()
show_user_bar()

st.title("📅 Follow-ups")
st.markdown("All scheduled follow-ups — they appear in Tasks automatically when due.")

if st.session_state.pop("_fu_added_msg", None):
    st.success("✅ Follow-up saved successfully.")

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
    with st.form("add_followup_form", clear_on_submit=True):
        if pick == "✏️ Type a new name":
            company_in = st.text_input("Client / Company Name *",
                                       placeholder="e.g. Al Futtaim Group")
        else:
            company_in = pick
            st.caption(f"Company: **{pick}**")
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            fu_date = st.date_input("Follow-up Date *", value=date.today())
        with a2:
            fu_time = st.time_input("Time (UAE)", value=time(10, 0), step=900)
        with a3:
            fu_user = st.selectbox("Assign To", USERS)
        with a4:
            fu_exh = st.selectbox("Exhibition", ["—"] + EXHIBITIONS)
        fu_notes = st.text_input(
            "Notes",
            placeholder="e.g. Cold call — client asked to call back after a week",
        )
        if st.form_submit_button("📅 Save Follow-up", type="primary"):
            if not str(company_in).strip():
                st.error("Client / company name is required.")
            else:
                company_clean = str(company_in).strip()
                fu_date_str = fu_date.strftime("%d-%b-%Y")
                fu_time_str = fu_time.strftime("%I:%M %p")
                # Pull contact details from the matching lead, if there is one
                c_name = c_phone = c_email = ""
                if not pipeline_df.empty and "Company Name" in pipeline_df.columns:
                    match = pipeline_df[pipeline_df["Company Name"].astype(str) == company_clean]
                    if not match.empty:
                        lead = match.iloc[0]
                        c_name  = str(lead.get("Contact Name", "") or "")
                        c_phone = str(lead.get("Contact Phone", "") or "")
                        c_email = str(lead.get("Contact Email", "") or "")
                ok = add_followup({
                    "company_name":  company_clean,
                    "exhibition":    "" if fu_exh == "—" else fu_exh,
                    "stage_at_time": "",
                    "followup_date": fu_date_str,
                    "followup_time": fu_time_str,
                    "assigned_to":   fu_user,
                    "notes":         fu_notes,
                    "created_by":    get_display_name(),
                })
                if ok:
                    notify_followup_assigned(
                        assigned_to=fu_user, assigned_by=get_display_name(),
                        company=company_clean, exhibition=("" if fu_exh == "—" else fu_exh),
                        fu_date=f"{fu_date_str} {fu_time_str}", notes=fu_notes,
                        contact_name=c_name, contact_phone=c_phone, contact_email=c_email,
                    )
                    get_due_followups.clear()
                    get_due_count.clear()
                    st.session_state["_fu_added_msg"] = True
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
    company    = row.get("Company Name", "—")
    exh        = row.get("Exhibition",   "")
    fu_date    = row.get("Follow-up Date", "—")
    fu_time    = str(row.get("Follow-up Time", "") or "")
    assigned   = row.get("Assigned To",  "—")
    stage      = row.get("Stage at Time", "")
    notes      = row.get("Notes",         "")
    status     = row.get("Status",        "Pending")
    created_by = row.get("Created By",    "")
    when_display = f"{fu_date} {fu_time}".strip()

    # Determine if overdue
    is_overdue = False
    try:
        is_overdue = (status == "Pending" and
                      pd.to_datetime(fu_date, dayfirst=True).date() <= today)
    except Exception:
        pass

    icon = "🔴" if is_overdue else ("✅" if status == "Done" else "📅")

    with st.container(border=True):
        lc, mc = st.columns([8, 1])
        with lc:
            st.markdown(f"**{icon}  {company}**" + (f"  ·  {exh}" if exh else ""))
            st.caption(f"📅 {when_display}  ·  👤 {assigned}  ·  Status: **{status}**")
            if stage:
                st.caption(f"Stage when added: {stage}")
            if notes:
                st.caption(f"📝 {notes}")
        with mc:
            with st.popover("⋮", use_container_width=True):
                if status != "Done":
                    if st.button("✓ Mark Done", key=f"done_{idx}", type="primary", use_container_width=True):
                        update_followup_status(idx, "Done")
                        st.rerun()
                else:
                    if st.button("↩ Reopen", key=f"reopen_{idx}", use_container_width=True):
                        update_followup_status(idx, "Pending")
                        st.rerun()

                if can_modify(created_by):
                    st.divider()
                    with st.form(f"edit_fu_{idx}"):
                        st.caption("✏️ Edit follow-up")
                        e_company = st.text_input("Company / Client", value=str(company))
                        ec1, ec2, ec3 = st.columns(3)
                        with ec1:
                            try:
                                _fd = pd.to_datetime(fu_date, dayfirst=True).date()
                            except Exception:
                                _fd = today
                            e_date = st.date_input("Follow-up Date", value=_fd)
                        with ec2:
                            try:
                                _ft = datetime.strptime(fu_time, "%I:%M %p").time()
                            except Exception:
                                _ft = time(10, 0)
                            e_time = st.time_input("Time (UAE)", value=_ft, step=900)
                        with ec3:
                            e_assigned = st.selectbox(
                                "Assign To", USERS,
                                index=USERS.index(assigned) if assigned in USERS else 0,
                            )
                        e_notes = st.text_input("Notes", value=str(notes))
                        if st.form_submit_button("💾 Save changes", type="primary", use_container_width=True):
                            update_followup_fields(idx, {
                                "Company Name":  e_company,
                                "Follow-up Date": e_date.strftime("%d-%b-%Y"),
                                "Follow-up Time": e_time.strftime("%I:%M %p"),
                                "Assigned To":   e_assigned,
                                "Notes":         e_notes,
                                "Reminder Sent": "",
                            })
                            st.rerun()

                    st.divider()
                    if not st.session_state.get(f"confirm_delfu_{idx}"):
                        if st.button("🗑 Delete", key=f"delfu_{idx}", use_container_width=True):
                            st.session_state[f"confirm_delfu_{idx}"] = True
                            st.rerun()
                    else:
                        st.warning("Delete this follow-up permanently?")
                        if st.button("Yes, delete", key=f"yesdelfu_{idx}", type="primary", use_container_width=True):
                            delete_followup(idx)
                            st.session_state.pop(f"confirm_delfu_{idx}", None)
                            st.rerun()
                        if st.button("Cancel", key=f"nodelfu_{idx}", use_container_width=True):
                            st.session_state.pop(f"confirm_delfu_{idx}", None)
                            st.rerun()
                else:
                    st.divider()
                    st.caption(f"Only {created_by or 'the creator'} or an admin can edit or delete this.")
