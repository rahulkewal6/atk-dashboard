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
