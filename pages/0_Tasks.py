import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from utils.sheets import (
    get_tasks_df, add_task, update_task, update_task_fields, delete_task,
    get_due_followups, update_followup_status,
)
from utils.constants import TASK_PRIORITIES, TASK_STATUSES, USERS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, can_modify, get_display_name
from utils.notify import notify_task_assigned

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

# Show success message after a task was added (survives the form reset rerun)
if st.session_state.pop("_task_added_msg", None):
    st.success("✅ Task added successfully.")

# ── Add new task ──────────────────────────────────────────────────────────────
with st.expander("➕ Add New Task"):
    with st.form("add_task_form", clear_on_submit=True):
        t1, t2 = st.columns(2)
        with t1:
            title      = st.text_input("Task *")
            assigned   = st.selectbox("Assign To", USERS)
            priority   = st.selectbox("Priority", TASK_PRIORITIES)
        with t2:
            due_date   = st.date_input("Due Date", value=date.today())
            due_time   = st.time_input("Due Time (UAE)", value=time(18, 0), step=900)
            created_by = st.selectbox("Created By", USERS)
            notes      = st.text_input("Notes", placeholder="Any extra detail…")

        if st.form_submit_button("Add Task"):
            if not title:
                st.error("Task title is required.")
            else:
                due_str  = due_date.strftime("%d-%b-%Y")
                time_str = due_time.strftime("%I:%M %p")
                ok = add_task({
                    "title":       title,
                    "assigned_to": assigned,
                    "priority":    priority,
                    "due_date":    due_str,
                    "due_time":    time_str,
                    "notes":       notes,
                    "created_by":  created_by,
                    "source":      "Manual",
                })
                if ok:
                    notify_task_assigned(title, assigned, created_by, priority,
                                         f"{due_str} {time_str}", notes)
                    st.session_state["_task_added_msg"] = True
                    st.rerun()
                else:
                    st.error("Could not save. Check Google Sheets connection.")

st.markdown("---")

# ── Task list ─────────────────────────────────────────────────────────────────
view = st.radio(
    "View", ["🕐 Active", "✅ Completed", "All"],
    horizontal=True, label_visibility="collapsed",
)
filter_user = st.selectbox("Filter by person", ["All"] + USERS)

df = get_tasks_df()

if df.empty:
    st.info("No tasks yet. Add one above.")
    st.stop()

# Apply filters
if filter_user != "All" and "Assigned To" in df.columns:
    df = df[df["Assigned To"] == filter_user]
if "Status" in df.columns:
    if view == "🕐 Active":
        df = df[df["Status"].isin(["Pending", "In Progress"])]
    elif view == "✅ Completed":
        df = df[df["Status"] == "Done"]

if df.empty:
    st.info("No tasks in this view.")
    st.stop()

is_completed_view = (view == "✅ Completed")

# Sort: completed view → most recently completed first; otherwise Pending first
df = df.copy()
if is_completed_view:
    df["_sort"] = pd.to_datetime(df.get("Completed Date", ""), dayfirst=True, errors="coerce")
    df = df.sort_values("_sort", ascending=False).drop(columns=["_sort"])
elif "Status" in df.columns:
    order = {"Pending": 0, "In Progress": 1, "Done": 2}
    df["_sort"] = df["Status"].map(order).fillna(3)
    df = df.sort_values("_sort").drop(columns=["_sort"])

st.markdown(f"**{len(df)} task(s)**")

_PRIORITY_COLOR = {"High": "🔴", "Medium": "🟡", "Low": "⚪"}
_STATUS_COLOR   = {"Pending": "🕐", "In Progress": "🔄", "Done": "✅"}

for idx, row in df.iterrows():
    title      = row.get("Title", "—")
    assigned   = row.get("Assigned To", "")
    priority   = row.get("Priority", "Medium")
    status     = row.get("Status", "Pending")
    due        = row.get("Due Date", "")
    due_time   = str(row.get("Due Time", "") or "")
    notes      = row.get("Notes", "")
    source     = row.get("Source", "Manual")
    src_co     = row.get("Source Company", "")
    created_by = row.get("Created By", "")
    comp_by    = str(row.get("Completed By", "") or "")
    comp_date  = str(row.get("Completed Date", "") or "")

    p_icon = _PRIORITY_COLOR.get(priority, "⚪")
    s_icon = _STATUS_COLOR.get(status, "🕐")
    due_display = (f"{due} {due_time}".strip()) or "—"

    with st.container(border=True):
        tc, mc = st.columns([8, 1])
        with tc:
            meta = f"{p_icon} {priority}  ·  👤 {assigned or '—'}  ·  📅 {due_display}"
            if src_co:
                meta += f"  ·  {src_co}"
            st.markdown(f"**{s_icon}  {title}**")
            st.caption(meta)
            if notes:
                st.caption(f"📝 {notes}")
            if source != "Manual":
                st.caption(f"From: {source} follow-up")
            if status == "Done" and (comp_by or comp_date):
                done_line = "✅ Completed"
                if comp_by:
                    done_line += f" by {comp_by}"
                if comp_date:
                    done_line += f" on {comp_date}"
                st.caption(done_line)
        with mc:
            with st.popover("⋮", use_container_width=True):
                st.caption("Status")
                new_status = st.selectbox(
                    "Status", TASK_STATUSES,
                    index=TASK_STATUSES.index(status) if status in TASK_STATUSES else 0,
                    key=f"taskstatus_{idx}", label_visibility="collapsed",
                )
                if st.button("Update status", key=f"taskstatusbtn_{idx}", use_container_width=True):
                    if new_status == "Done":
                        update_task_fields(idx, {
                            "Status": "Done",
                            "Completed By": get_display_name(),
                            "Completed Date": date.today().strftime("%d-%b-%Y"),
                        })
                    else:
                        # reopened — clear completion record
                        update_task_fields(idx, {
                            "Status": new_status,
                            "Completed By": "",
                            "Completed Date": "",
                        })
                    st.rerun()

                if can_modify(created_by):
                    st.divider()
                    with st.form(f"edit_task_{idx}"):
                        st.caption("✏️ Edit task")
                        e_title = st.text_input("Task", value=str(title))
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            e_assigned = st.selectbox(
                                "Assign To", USERS,
                                index=USERS.index(assigned) if assigned in USERS else 0,
                            )
                            e_priority = st.selectbox(
                                "Priority", TASK_PRIORITIES,
                                index=TASK_PRIORITIES.index(priority) if priority in TASK_PRIORITIES else 1,
                            )
                        with ec2:
                            try:
                                _dd = datetime.strptime(str(due), "%d-%b-%Y").date()
                            except Exception:
                                _dd = date.today()
                            e_due = st.date_input("Due Date", value=_dd)
                            try:
                                _dt = datetime.strptime(due_time, "%I:%M %p").time()
                            except Exception:
                                _dt = time(18, 0)
                            e_time = st.time_input("Due Time (UAE)", value=_dt, step=900)
                        e_notes = st.text_input("Notes", value=str(notes))
                        if st.form_submit_button("💾 Save changes", type="primary", use_container_width=True):
                            update_task_fields(idx, {
                                "Title":       e_title,
                                "Assigned To": e_assigned,
                                "Priority":    e_priority,
                                "Due Date":    e_due.strftime("%d-%b-%Y"),
                                "Due Time":    e_time.strftime("%I:%M %p"),
                                "Notes":       e_notes,
                                "Reminder Sent": "",
                            })
                            st.rerun()

                    st.divider()
                    if not st.session_state.get(f"confirm_deltask_{idx}"):
                        if st.button("🗑 Delete task", key=f"deltask_{idx}", use_container_width=True):
                            st.session_state[f"confirm_deltask_{idx}"] = True
                            st.rerun()
                    else:
                        st.warning("Delete this task permanently?")
                        if st.button("Yes, delete", key=f"yesdeltask_{idx}", type="primary", use_container_width=True):
                            delete_task(idx)
                            st.session_state.pop(f"confirm_deltask_{idx}", None)
                            st.rerun()
                        if st.button("Cancel", key=f"nodeltask_{idx}", use_container_width=True):
                            st.session_state.pop(f"confirm_deltask_{idx}", None)
                            st.rerun()
                else:
                    st.divider()
                    st.caption(f"Only {created_by or 'the creator'} or an admin can edit or delete this.")
