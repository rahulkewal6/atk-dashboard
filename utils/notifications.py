"""
Per-user notifications: the open tasks and follow-ups assigned to the logged-in
person, with a "NEW" flag for anything created in the last couple of days.

Takes the display name as a parameter (no import of utils.auth) to avoid a
circular import — auth.py imports this module for the sidebar badge.
"""
import time as _time
import streamlit as st
from datetime import datetime
from utils.sheets import get_tasks_df, get_followups_df
from utils.timeutil import time_with_ist

_NEW_DAYS = 2
_CACHE_TTL = 60


def _is_new(created_date):
    try:
        d = datetime.strptime(str(created_date).strip(), "%d-%b-%Y").date()
        return (datetime.now().date() - d).days <= _NEW_DAYS
    except Exception:
        return False


def get_my_items(name):
    """Return (tasks, followups) assigned to `name` that are still open. Cached per session."""
    ck = f"_notif_{name}"
    tk = ck + "_ts"
    now = _time.time()
    if ck in st.session_state and now - st.session_state.get(tk, 0) < _CACHE_TTL:
        return st.session_state[ck]

    tasks, followups = [], []
    try:
        tdf = get_tasks_df()
        if not tdf.empty and "Assigned To" in tdf.columns:
            for _, r in tdf.iterrows():
                if str(r.get("Assigned To", "")) == name and str(r.get("Status", "")) in ("Pending", "In Progress"):
                    tasks.append(r.to_dict())
        fdf = get_followups_df()
        if not fdf.empty and "Assigned To" in fdf.columns:
            for _, r in fdf.iterrows():
                if str(r.get("Assigned To", "")) == name and str(r.get("Status", "")) != "Done":
                    followups.append(r.to_dict())
    except Exception:
        pass

    st.session_state[ck] = (tasks, followups)
    st.session_state[tk] = now
    return tasks, followups


def clear_cache(name):
    for k in (f"_notif_{name}", f"_notif_{name}_ts"):
        st.session_state.pop(k, None)


def new_count(name):
    """Count of items created in the last couple of days (for the sidebar badge)."""
    tasks, followups = get_my_items(name)
    return sum(1 for t in tasks if _is_new(t.get("Created Date"))) + \
           sum(1 for f in followups if _is_new(f.get("Created Date")))


def render_panel(name):
    """Full notification panel for the Home page."""
    tasks, followups = get_my_items(name)
    total = len(tasks) + len(followups)
    new_n = new_count(name)

    with st.container(border=True):
        head = f"### 🔔 Notifications for {name}"
        st.markdown(head)
        if total == 0:
            st.success("You're all caught up — nothing assigned to you right now. 🎉")
            return
        if new_n:
            st.caption(f"🆕 {new_n} new · {total} open assigned to you")
        else:
            st.caption(f"{total} open assigned to you")

        if tasks:
            st.markdown("**📋 Your tasks**")
            for t in tasks:
                badge = "🆕 " if _is_new(t.get("Created Date")) else ""
                tm = str(t.get("Due Time", "") or "")
                due = f"{t.get('Due Date','')} · {time_with_ist(tm)}".strip(" ·") if tm else str(t.get("Due Date", "") or "—")
                st.markdown(f"- {badge}{t.get('Title','')}  ·  📅 {due}  ·  _{t.get('Status','')}_")
        if followups:
            st.markdown("**📅 Your follow-ups**")
            for f in followups:
                badge = "🆕 " if _is_new(f.get("Created Date")) else ""
                ftm = str(f.get("Follow-up Time", "") or "")
                when = f"{f.get('Follow-up Date','')} · {time_with_ist(ftm)}".strip(" ·") if ftm else str(f.get("Follow-up Date", "") or "—")
                st.markdown(f"- {badge}{f.get('Company Name','')}  ·  📅 {when}")

        l1, l2 = st.columns(2)
        l1.page_link("pages/0_Tasks.py",      label="Go to Tasks",      icon="📋", use_container_width=True)
        l2.page_link("pages/2_Follow_Ups.py", label="Go to Follow-ups", icon="📅", use_container_width=True)
