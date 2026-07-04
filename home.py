import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets import get_pipeline_df, get_tasks_df, get_followups_df, get_due_count
from utils.constants import STAGE_TIERS, TIER_STYLE
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, get_display_name
from utils.notifications import render_panel
from utils.ui import greeting_header

inject_css()
require_login()
show_logo()
show_user_bar()

# Home-only dark skin (this CSS runs only while the Home page renders)
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background: #0D0E10 !important; }
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] span { color: #D6D9DE; }
    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3 { color: #FFFFFF !important; }
    [data-testid="stAppViewContainer"] [data-testid="stVerticalBlockBorderWrapper"] {
        background: #16181D !important;
        border-color: #26282E !important;
        box-shadow: none;
    }
    [data-testid="stAppViewContainer"] .atk-stat {
        background: #16181D !important;
        border-color: #26282E !important;
    }
    [data-testid="stAppViewContainer"] .atk-stat .l { color: #8A8F98 !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }
    [data-testid="stAppViewContainer"] hr { border-color: #26282E !important; }
    [data-testid="stPageLink"] a { color: #D6D9DE !important; border: 1px solid #2E313A;
        border-radius: 8px; }
    [data-testid="stPageLink"] a:hover { color: #FF7D2B !important; border-color: #FF6600; }
    [data-testid="stAppViewContainer"] [data-testid="stDataFrame"] > div {
        border-color: #26282E !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

_due = get_due_count()
if _due:
    st.sidebar.error(f"🔔 {_due} follow-up{'s' if _due > 1 else ''} due — check Tasks")

# Stages where the design still has to be sent to the client
_DESIGN_PENDING_STAGES = {
    "Brief Received (v1)", "Brief Received (v2)", "Brief Received (v3)",
    "New Brief Received (Client Changed)",
    "Brief Sent to Designer", "Revised Brief Sent to Designer",
    "Additional Changes Requested",
}

# ── Gather metrics ────────────────────────────────────────────────────────────
tasks_df = get_tasks_df()
pending_tasks = 0
if not tasks_df.empty and "Status" in tasks_df.columns:
    pending_tasks = int(tasks_df["Status"].isin(["Pending", "In Progress"]).sum())

fu_df = get_followups_df()
fu_week = 0
today = datetime.now().date()
week_end = today + timedelta(days=7)
if not fu_df.empty and "Follow-up Date" in fu_df.columns and "Status" in fu_df.columns:
    try:
        dates = pd.to_datetime(fu_df["Follow-up Date"], dayfirst=True, errors="coerce").dt.date
        fu_week = int(((fu_df["Status"] != "Done") & (dates <= week_end)).sum())
    except Exception:
        pass

df = get_pipeline_df()
action_needed = 0
designs_to_send = 0
if not df.empty and "Current Stage" in df.columns:
    stages = df["Current Stage"].astype(str)
    action_needed   = int((stages.map(lambda s: STAGE_TIERS.get(s, "")) == "red").sum())
    designs_to_send = int(stages.isin(_DESIGN_PENDING_STAGES).sum())

# ── Greeting + insight (reference-style briefing header) ─────────────────────
_bits = []
if action_needed:
    _bits.append(f'<b style="color:#FF7D2B;">{action_needed} lead(s) need your action</b>')
if fu_week:
    _bits.append(f"{fu_week} follow-up(s) this week")
if pending_tasks:
    _bits.append(f"{pending_tasks} pending task(s)")
greeting_header(get_display_name() or "there",
                " — ".join(_bits) if _bits else "All clear today. 🎉", dark=True)

# Personal notification panel — what's assigned to whoever is logged in
render_panel(get_display_name())

# ── Metric cards ──────────────────────────────────────────────────────────────
# Bright variants — Home renders on a dark background
_CARDS = [
    ("#FF6B6B", action_needed,   "Leads — action needed"),
    ("#F5B84A", designs_to_send, "Designs to send"),
    ("#6FB7F2", fu_week,         "Follow-ups this week"),
    ("#FF8C5A", pending_tasks,   "Pending tasks"),
]
st.markdown(
    '<div class="atk-stats">'
    + "".join(
        f'<div class="atk-stat" style="border-top:3px solid {c};">'
        f'<div class="n" style="color:{c};">{n}</div>'
        f'<div class="l">{label}</div></div>'
        for c, n, label in _CARDS
    )
    + "</div>",
    unsafe_allow_html=True,
)

# Quick links to act on each metric
l1, l2, l3, l4 = st.columns(4)
l1.page_link("pages/1_Leads.py",      label="Open Leads",      icon="🎯", use_container_width=True)
l2.page_link("pages/1_Leads.py",      label="Open Designs",    icon="🎨", use_container_width=True)
l3.page_link("pages/2_Follow_Ups.py", label="Open Follow-ups", icon="📅", use_container_width=True)
l4.page_link("pages/0_Tasks.py",      label="Open Tasks",      icon="📋", use_container_width=True)

st.markdown("---")

# ── Pipeline summary ──────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
if not df.empty and "Current Stage" in df.columns:
    hot     = len(df[df["Current Stage"].str.contains("Hot Lead", na=False)])
    active  = len(df[~df["Current Stage"].isin(["Won", "Lost", "No Response — Follow Up Later"])])
    won     = len(df[df["Current Stage"] == "Won"])
    waiting = len(df[df["Current Stage"].str.contains("Waiting", na=False)])
else:
    hot = active = won = waiting = 0

col1.metric("🔴 Hot Leads", hot, help="Needs immediate action")
col2.metric("📋 Active Pipeline", active)
col3.metric("✅ Won", won)
col4.metric("⏳ Awaiting Response", waiting)

st.markdown("---")

# ── Leads needing action ──────────────────────────────────────────────────────
st.subheader("🔴 Action Needed — Act Now")

if not df.empty and "Current Stage" in df.columns:
    red_df = df[df["Current Stage"].astype(str).map(lambda s: STAGE_TIERS.get(s, "")) == "red"]
    if not red_df.empty:
        display_cols = [c for c in ["Company Name", "Exhibition", "Current Stage", "Source", "Contact Email", "Date Added"] if c in red_df.columns]
        st.dataframe(red_df[display_cols], use_container_width=True, hide_index=True)
        st.caption("Go to the **Leads** page to update stages.")
    else:
        st.success("Nothing pending from our side right now. 🎉")
else:
    st.info("No pipeline data yet. Add leads in the **Leads** page.")

st.markdown("---")
st.caption("ATK Exhibitions | Rahul & Bhavika")
