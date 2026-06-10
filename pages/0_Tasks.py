import streamlit as st
from datetime import datetime, date
from utils.sheets import get_tasks_df, add_task, update_task, get_due_followups, update_followup_status
from utils.constants import TASK_PRIORITIES, TASK_STATUSES, USERS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

st.set_page_config(page_title="Tasks", page_icon="📋", layout="wide")
inject_css()
require_login()
show_logo()
show_user_bar()

st.title("📋 Tasks")

# ── Due follow-ups banner ─────────────────────────────────────────────────────
due = get_due_followups()
if due:
    st.markdown(
        f'<div style="background:#fdecea;border-left:4px solid #c0392b;'
        f'padding:12px 16px;border-radius:6px;margin-bottom:16px;">'
        f'<strong style="color:#c0392b;">🔔 {len(due)} follow-up{"s" if len(due) > 1 else ""} due!</strong>'
        f'</div>',
        unsafe_allow_html=True,
    )
    for item in due:
        row_idx = item["_row_idx"]
        company = item.get("Company Name", "—")
        fu_date = item.get("Follow-up Date", "—")
        assigned = item.get("Assigned To", "—")
        notes   = item.get("Notes", "")
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        col1.markdown(f"**{company}**")
        col2.caption(f"📅 {fu_date}")
        col3.caption(f"👤 {assigned}")
        with col4:
            if st.button("✓ Done", key=f"fu_done_{row_idx}", type="primary"):
                update_followup_status(row_idx, "Done")
                get_due_followups.clear()
                st.rerun()
    st.markdown("---")

# ── Add new task ──────────────────────────────────────────────────────────────
with st.expander("➕ Add New Task"):
    with st.form("add_task_form"):
        t1, t2 = st.columns(2)
        with t1:
            title      = st.text_input("Task *")
            assigned   = st.selectbox("Assign To", USERS)
            priority   = st.selectbox("Priority", TASK_PRIORITIES)
        with t2:
            due_date   = st.date_input("Due Date", value=date.today())
            created_by = st.selectbox("Created By", USERS)
            notes      = st.text_input("Notes", placeholder="Any extra detail…")

        if st.form_submit_button("Add Task"):
            if not title:
                st.error("Task title is required.")
            else:
                ok = add_task({
                    "title":       title,
                    "assigned_to": assigned,
                    "priority":    priority,
                    "due_date":    due_date.strftime("%d-%b-%Y"),
                    "notes":       notes,
                    "created_by":  created_by,
                    "source":      "Manual",
                })
                if ok:
                    st.success("Task added!")
                    st.rerun()
                else:
                    st.error("Could not save. Check Google Sheets connection.")

st.markdown("---")

# ── Task list ─────────────────────────────────────────────────────────────────
fc1, fc2 = st.columns(2)
with fc1:
    filter_user   = st.selectbox("Filter by person", ["All"] + USERS)
with fc2:
    filter_status = st.selectbox("Filter by status", ["Pending & In Progress", "All", "Done"])

df = get_tasks_df()

if df.empty:
    st.info("No tasks yet. Add one above.")
    st.stop()

# Apply filters
if filter_user != "All" and "Assigned To" in df.columns:
    df = df[df["Assigned To"] == filter_user]
if filter_status == "Pending & In Progress" and "Status" in df.columns:
    df = df[df["Status"].isin(["Pending", "In Progress"])]
elif filter_status == "Done" and "Status" in df.columns:
    df = df[df["Status"] == "Done"]

if df.empty:
    st.info("No tasks match the current filter.")
    st.stop()

# Sort: Pending first, then by Due Date
if "Status" in df.columns:
    order = {"Pending": 0, "In Progress": 1, "Done": 2}
    df = df.copy()
    df["_sort"] = df["Status"].map(order).fillna(3)
    df = df.sort_values("_sort").drop(columns=["_sort"])

st.markdown(f"**{len(df)} task(s)**")

_PRIORITY_COLOR = {"High": "🔴", "Medium": "🟡", "Low": "⚪"}
_STATUS_COLOR   = {"Pending": "🕐", "In Progress": "🔄", "Done": "✅"}

for idx, row in df.iterrows():
    task_id  = row.get("Task ID", "")
    title    = row.get("Title", "—")
    assigned = row.get("Assigned To", "")
    priority = row.get("Priority", "Medium")
    status   = row.get("Status", "Pending")
    due      = row.get("Due Date", "")
    notes    = row.get("Notes", "")
    source   = row.get("Source", "Manual")
    src_co   = row.get("Source Company", "")

    p_icon = _PRIORITY_COLOR.get(priority, "⚪")
    s_icon = _STATUS_COLOR.get(status, "🕐")
    label  = f"{s_icon}  {title}"
    if src_co:
        label += f"  ·  {src_co}"

    with st.expander(label):
        lc, rc = st.columns([3, 1])
        with lc:
            st.caption(f"{p_icon} {priority}  ·  👤 {assigned}  ·  📅 {due}")
            if notes:
                st.markdown(f"_{notes}_")
            if source != "Manual":
                st.caption(f"From: {source} follow-up")
        with rc:
            with st.form(f"task_upd_{idx}"):
                new_status = st.selectbox(
                    "Status", TASK_STATUSES,
                    index=TASK_STATUSES.index(status) if status in TASK_STATUSES else 0,
                    label_visibility="collapsed",
                )
                if st.form_submit_button("Update", use_container_width=True, type="primary"):
                    update_task(idx, "Status", new_status)
                    st.rerun()
