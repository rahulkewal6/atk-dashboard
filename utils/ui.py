"""Shared small UI helpers (Streamlit-dependent)."""
import streamlit as st
from datetime import datetime, timedelta
from utils.timeutil import TIME_OPTIONS, normalize_time


def time_select(label, default="6:00 PM", key=None, label_visibility="visible"):
    """A 12-hour AM/PM time dropdown in 15-minute steps. Returns 'h:mm AM/PM' (UAE)."""
    norm = normalize_time(default)
    if norm not in TIME_OPTIONS:
        norm = "6:00 PM"
    return st.selectbox(label, TIME_OPTIONS, index=TIME_OPTIONS.index(norm),
                        key=key, label_visibility=label_visibility)


def uae_now():
    """Current time in UAE (UTC+4, no daylight saving)."""
    return datetime.utcnow() + timedelta(hours=4)


def greeting_header(name, insight_html=""):
    """Reference-style page header: date · greeting · one-line insight."""
    now = uae_now()
    h = now.hour
    word = "Good morning" if h < 12 else ("Good afternoon" if h < 17 else "Good evening")
    date_str = now.strftime("%A, %B %-d").upper()
    st.markdown(
        f'<div style="margin:0 0 14px;">'
        f'<div style="font-size:0.72rem;letter-spacing:0.08em;color:#8A8F98;">{date_str}</div>'
        f'<div style="font-size:1.45rem;font-weight:700;color:#16181D;margin:2px 0;">{word}, {name}.</div>'
        + (f'<div style="font-size:0.9rem;color:#5C626B;">{insight_html}</div>' if insight_html else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def pipeline_bars(counts, styles, title="Pipeline by stage"):
    """Reference-style stage bars. counts: {tier: n}; styles: TIER_STYLE-like dict."""
    total = sum(counts.values())
    if total == 0:
        return
    rows = ""
    for tier, n in counts.items():
        if n == 0:
            continue
        s = styles[tier]
        pct = round(n * 100 / total)
        rows += (
            f'<span style="color:{s["color"]};font-size:0.78rem;">● {s["label"]}</span>'
            f'<div style="height:6px;border-radius:3px;background:#EEF0F3;align-self:center;">'
            f'<div style="width:{pct}%;height:6px;border-radius:3px;background:{s["color"]};"></div></div>'
            f'<span style="color:#4B5563;font-size:0.78rem;text-align:right;">{n} · {pct}%</span>'
        )
    st.markdown(
        f'<div style="background:#fff;border:1px solid #E6E8EC;border-radius:12px;'
        f'padding:14px 16px;margin:0 0 14px;box-shadow:0 1px 2px rgba(16,24,40,0.04);">'
        f'<div style="font-size:0.88rem;font-weight:600;color:#16181D;margin-bottom:10px;">{title} '
        f'<span style="color:#8A8F98;font-weight:400;">— {total} lead(s)</span></div>'
        f'<div style="display:grid;grid-template-columns:170px 1fr 62px;gap:8px 12px;">{rows}</div></div>',
        unsafe_allow_html=True,
    )
