import streamlit as st
import pandas as pd
from utils.apollo_api import get_sequences, get_sequence_detail, get_mailboxes
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

inject_css()
require_login()
show_logo()
show_user_bar()

st.title("📊 Sequences")
st.markdown("Apollo email sequences — live stats, refreshed every 5 minutes.")


def _num(value):
    """Safely turn an Apollo value into a float (Apollo sometimes returns blanks/strings)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# ── MAILBOX HEALTH ──────────────────────────────────────────────────────────
st.subheader("Mailbox Health")
with st.spinner("Loading mailboxes..."):
    mailboxes = get_mailboxes()

if mailboxes:
    mb_data = []
    for mb in mailboxes:
        sent = mb.get("sent_today_count", 0) or 0
        limit = mb.get("send_limit_per_day", 0) or 0
        pct = int((sent / limit) * 100) if limit > 0 else 0
        mb_data.append({
            "Email": mb.get("email", ""),
            "Status": "✅ Active" if mb.get("active") else "⚠️ Inactive",
            "Sent Today": sent,
            "Daily Limit": limit,
            "Used %": f"{pct}%",
        })
    st.dataframe(pd.DataFrame(mb_data), use_container_width=True, hide_index=True)
else:
    st.warning("Could not load mailboxes. Check Apollo API connection.")

st.markdown("---")

# ── SEQUENCES ───────────────────────────────────────────────────────────────
st.subheader("Active Sequences")
with st.spinner("Loading sequences from Apollo..."):
    sequences = get_sequences()

if not sequences:
    st.warning("No sequences found. Check your Apollo API key in secrets.toml.")
    st.stop()

st.markdown(f"**{len(sequences)} sequence(s) found**")

# ── TOP SUMMARY CARDS (first 5) ─────────────────────────────────────────────
cols = st.columns(min(len(sequences), 5))
for i, seq in enumerate(sequences[:5]):
    with cols[i]:
        name = seq.get("name", "Unknown")
        statuses = seq.get("contact_statuses", {})
        active_count = statuses.get("active", seq.get("active_contact_count", 0))
        status = seq.get("status", "unknown")
        icon = "✅" if status == "active" else "⚠️" if status == "paused" else "⬜"
        reply_r = _num(seq.get("reply_rate", 0))
        st.metric(
            label=f"{icon} {name[:22]}",
            value=f"{active_count} active",
            delta=f"{reply_r*100:.1f}% reply",
        )

st.markdown("---")

# ── FULL SEQUENCE TABLE ──────────────────────────────────────────────────────
seq_rows = []
for seq in sequences:
    statuses = seq.get("contact_statuses", {})

    # contact counts — prefer contact_statuses dict, fall back to top-level fields
    active  = statuses.get("active",      seq.get("active_contact_count", 0))   or 0
    paused  = statuses.get("paused",      seq.get("paused_contact_count", 0))   or 0
    finished= statuses.get("finished",    seq.get("finished_contact_count", 0)) or 0
    bounced = (statuses.get("bounced", 0) or 0) + (statuses.get("hard_bounced", 0) or 0)
    not_sent= statuses.get("not_sent", 0) or 0
    total   = active + paused + finished + bounced + not_sent

    # email stats
    open_r   = _num(seq.get("open_rate",   0))
    reply_r  = _num(seq.get("reply_rate",  0))
    bounce_r = _num(seq.get("bounce_rate", 0))

    opened   = seq.get("unique_opened",   0) or 0
    replied  = seq.get("unique_replied",  0) or 0
    delivered= seq.get("unique_delivered",0) or 0

    seq_rows.append({
        "Sequence": seq.get("name", ""),
        "Status": seq.get("status", "").capitalize(),
        "Active": active,
        "Paused": paused,
        "Finished": finished,
        "Bounced": bounced,
        "Total": total,
        "Delivered": delivered,
        "Opened": opened,
        "Replied": replied,
        "Open %": f"{open_r*100:.1f}%",
        "Reply %": f"{reply_r*100:.1f}%",
        "Bounce %": f"{bounce_r*100:.1f}%",
    })

st.dataframe(pd.DataFrame(seq_rows), use_container_width=True, hide_index=True)

st.markdown("---")

# ── SEQUENCE DRILL-DOWN ──────────────────────────────────────────────────────
st.subheader("Sequence Detail")
seq_names = [s.get("name", "Unknown") for s in sequences]
selected = st.selectbox("Select a sequence to inspect", seq_names)

if selected:
    seq_obj = next((s for s in sequences if s.get("name") == selected), None)
    if seq_obj:
        # Show aggregate stats from the list (no extra API call needed for top-level stats)
        statuses = seq_obj.get("contact_statuses", {})
        active   = statuses.get("active",   seq_obj.get("active_contact_count",   0)) or 0
        paused   = statuses.get("paused",   seq_obj.get("paused_contact_count",   0)) or 0
        finished = statuses.get("finished", seq_obj.get("finished_contact_count", 0)) or 0
        bounced  = (statuses.get("bounced", 0) or 0) + (statuses.get("hard_bounced", 0) or 0)
        opened   = seq_obj.get("unique_opened",  0) or 0
        replied  = seq_obj.get("unique_replied", 0) or 0
        open_r   = _num(seq_obj.get("open_rate",  0)) * 100
        reply_r  = _num(seq_obj.get("reply_rate", 0)) * 100

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Active", active)
        col2.metric("Paused", paused)
        col3.metric("Finished", finished)
        col4.metric("Bounced", bounced)
        col5.metric("Open Rate", f"{open_r:.1f}%", delta=f"{opened} unique")
        col6.metric("Reply Rate", f"{reply_r:.1f}%", delta=f"{replied} unique")

        # Fetch email step details
        with st.spinner("Loading step details..."):
            detail = get_sequence_detail(seq_obj.get("id", ""))

        if detail:
            steps = detail.get("emailer_steps", [])
            if steps:
                st.markdown("**Email Steps:**")
                step_rows = []
                for step in steps:
                    templates = step.get("emailer_templates", [])
                    subject = templates[0].get("subject", "") if templates else ""
                    step_rows.append({
                        "Step": step.get("position", ""),
                        "Type": step.get("type", ""),
                        "Wait (days)": step.get("wait_time", ""),
                        "Subject": subject,
                    })
                st.dataframe(pd.DataFrame(step_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No email steps configured for this sequence.")
        else:
            st.info("No step detail available.")
