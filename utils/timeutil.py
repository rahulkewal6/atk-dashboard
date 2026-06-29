"""
Pure time helpers — NO Streamlit dependency, so both the app and the GitHub
Action scripts can use them.

All stored times are UAE (UTC+4). India (IST) is always UAE + 1 hour 30 min
(neither observes daylight saving), so the conversion is exact and fixed.
"""
from datetime import datetime, timedelta


def _fmt(dt):
    h = dt.hour % 12 or 12
    ap = "AM" if dt.hour < 12 else "PM"
    return f"{h}:{dt.minute:02d} {ap}"


def normalize_time(value, fallback="6:00 PM"):
    """Accept '06:00 PM', '6:00 PM' or '18:00' → '6:00 PM'."""
    if value:
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                return _fmt(datetime.strptime(str(value).strip(), fmt))
            except Exception:
                continue
    return fallback


# 96 options: 12:00 AM, 12:15 AM, … 11:45 PM (15-minute steps)
_BASE = datetime(2000, 1, 1, 0, 0)
TIME_OPTIONS = [_fmt(_BASE + timedelta(minutes=15 * i)) for i in range(96)]


def ist_of(uae_time_str):
    """UAE 'h:mm AM/PM' → IST 'h:mm AM/PM' (UAE + 1h30m)."""
    try:
        dt = datetime.strptime(normalize_time(uae_time_str), "%I:%M %p") + timedelta(hours=1, minutes=30)
        return _fmt(dt)
    except Exception:
        return ""


def time_with_ist(uae_time_str):
    """'1:00 PM' → '1:00 PM UAE · 2:30 PM IST'."""
    s = str(uae_time_str).strip()
    if not s:
        return ""
    base = normalize_time(s)
    ist = ist_of(s)
    return f"{base} UAE · {ist} IST" if ist else f"{base} UAE"
