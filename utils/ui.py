"""Shared small UI helpers."""
import streamlit as st
from datetime import datetime, timedelta


def _fmt(dt):
    h = dt.hour % 12 or 12
    ap = "AM" if dt.hour < 12 else "PM"
    return f"{h}:{dt.minute:02d} {ap}"


# 96 options: 12:00 AM, 12:15 AM, … 11:45 PM (15-minute steps)
_BASE = datetime(2000, 1, 1, 0, 0)
TIME_OPTIONS = [_fmt(_BASE + timedelta(minutes=15 * i)) for i in range(96)]


def _normalize(value, fallback="6:00 PM"):
    if value:
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                return _fmt(datetime.strptime(str(value).strip(), fmt))
            except Exception:
                continue
    return fallback


def time_select(label, default="6:00 PM", key=None, label_visibility="visible"):
    """A 12-hour AM/PM time dropdown in 15-minute steps. Returns 'h:mm AM/PM'."""
    norm = _normalize(default)
    if norm not in TIME_OPTIONS:
        norm = "6:00 PM"
    return st.selectbox(label, TIME_OPTIONS, index=TIME_OPTIONS.index(norm),
                        key=key, label_visibility=label_visibility)


def uae_now():
    """Current time in UAE (UTC+4, no daylight saving)."""
    return datetime.utcnow() + timedelta(hours=4)
