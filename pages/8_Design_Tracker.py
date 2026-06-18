import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.sheets import (
    get_pipeline_df, get_stage_history, update_lead_field,
    log_stage_change, add_task,
)
from utils.constants import USERS, TIER_STYLE
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, get_display_name

inject_css()
require_login()
show_logo()
show_user_bar()

# Stages that mean "brief is with the designer, waiting for the design"
DESIGN_STAGES = ["Brief Sent to Designer", "Revised Brief Sent to Designer"]
CHASE_DAYS = 3  # waiting this many days or more → nudge to chase the designer

st.title("🎨 Design Tracker")
st.caption("Briefs sent to the designer — what we're still waiting on, and for how long.")


def _brief_sent_date(company, stage):
    """Date the lead entered its current design stage, from Stage History."""
    h = get_stage_history(company)
    if h.empty or "Stage" not in h.columns or "Date/Time" not in h.columns:
        return None
    rows = h[h["Stage"] == stage]
    if rows.empty:
        return None
    found = []
    for v in rows["Date/Time"]:
        for fmt in ("%d-%b-%Y %H:%M", "%d-%b-%Y"):
            try:
                found.append(datetime.strptime(str(v).strip(), fmt))
                break
            except Exception:
                continue
    return max(found).date() if found else None


df = get_pipeline_df()
if df.empty or "Current Stage" not in df.columns:
    st.info("No leads yet.")
    st.stop()

pending = df[df["Current Stage"].isin(DESIGN_STAGES)].copy()

if pending.empty:
    st.success("🎉 No briefs pending with the designer right now.")
    st.stop()

# Build display info with waiting days
today = date.today()
rows = []
for idx, row in pending.iterrows():
    company = str(row.get("Company Name", "Unknown"))
    stage   = str(row.get("Current Stage", ""))
    sent    = _brief_sent_date(company, stage)
    waiting = (today - sent).days if sent else None
    rows.append((idx, row, company, stage, sent, waiting))

# Sort by longest waiting first (unknown dates last)
rows.sort(key=lambda r: (r[5] is None, -(r[5] or 0)))

overdue = sum(1 for r in rows if r[5] is not None and r[5] >= CHASE_DAYS)
m1, m2 = st.columns(2)
m1.metric("Briefs with designer", len(rows))
m2.metric(f"Waiting {CHASE_DAYS}+ days", overdue)

st.markdown("---")

_s = TIER_STYLE["design_prog"]

for idx, row, company, stage, sent, waiting in rows:
    exhibition = str(row.get("Exhibition", ""))
    brief_ver  = row.get("Brief Version", "")

    with st.container(border=True):
        hl, hr = st.columns([5, 1])
        with hl:
            sent_txt = sent.strftime("%d %b %Y") if sent else "date not logged"
            if waiting is None:
                wait_txt = ""
            elif waiting == 0:
                wait_txt = " · sent today"
            else:
                wait_txt = f" · {waiting} day{'s' if waiting != 1 else ''} ago"
            chase = waiting is not None and waiting >= CHASE_DAYS
            dot = "🔴" if chase else "🟡"
            st.markdown(
                f'<div class="atk-lead-head">'
                f'<span class="atk-dot" style="background:{_s["color"]};"></span>'
                f'<span class="atk-company">{company}</span>'
                f'<span class="atk-exh">{exhibition}</span>'
                f'<span class="atk-pill" style="background:{_s["bg"]};color:{_s["color"]};'
                f'border:1px solid {_s["color"]}55;">{stage}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"📐 Brief v{brief_ver}  ·  📤 Sent to designer: {sent_txt}{wait_txt}")
            if chase:
                st.markdown(
                    f'<span style="color:#FF4D4F;font-weight:700;">⏰ Waiting {waiting} days — time to chase the designer</span>',
                    unsafe_allow_html=True,
                )
        with hr:
            with st.popover("Actions", use_container_width=True):
                # Design received → move the lead forward
                st.caption("✅ Design received")
                opt = st.selectbox("Which option came in?", [1, 2, 3], key=f"opt_{idx}")
                if st.button("Mark design received", key=f"recv_{idx}", type="primary", use_container_width=True):
                    update_lead_field(idx + 1, "Current Stage", f"Design Option {opt} Sent", get_display_name())
                    update_lead_field(idx + 1, "Design Options Sent", opt, get_display_name())
                    log_stage_change(company, f"Design Option {opt} Sent", get_display_name(),
                                     "Design received from designer")
                    st.rerun()

                st.divider()
                st.caption("📋 Chase the designer")
                chase_user = st.selectbox("Remind", USERS, key=f"chaseuser_{idx}")
                if st.button("Create chase task", key=f"chasebtn_{idx}", use_container_width=True):
                    add_task({
                        "title":          f"Chase designer for {company}",
                        "assigned_to":    chase_user,
                        "priority":       "High",
                        "due_date":       today.strftime("%d-%b-%Y"),
                        "notes":          f"Brief ({stage}) sent {sent_txt}{wait_txt}.",
                        "created_by":     get_display_name(),
                        "source":         "Design Tracker",
                        "source_company": company,
                    })
                    st.success(f"Task created for {chase_user}.")
