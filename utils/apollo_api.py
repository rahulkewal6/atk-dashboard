import requests
import streamlit as st

BASE_URL = "https://api.apollo.io/v1"


def _headers():
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": st.secrets.get("APOLLO_API_KEY", ""),
    }


@st.cache_data(ttl=300)
def get_sequences():
    try:
        r = requests.post(
            f"{BASE_URL}/emailer_campaigns/search",
            headers=_headers(),
            json={"per_page": 50},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("emailer_campaigns", [])
        return []
    except Exception:
        return []


@st.cache_data(ttl=300)
def get_sequence_detail(campaign_id: str):
    try:
        r = requests.get(
            f"{BASE_URL}/emailer_campaigns/{campaign_id}",
            headers=_headers(),
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("emailer_campaign", {})
        return {}
    except Exception:
        return {}


@st.cache_data(ttl=300)
def get_replied_contacts(campaign_id: str, max_pages: int = 8):
    """
    Return the list of contacts who REPLIED within a sequence.
    Apollo exposes per-message reply flags (but not per-person opens), so this
    scans the sequence's sent messages and keeps the ones marked replied.
    """
    out = []
    if not campaign_id:
        return out
    try:
        page = 1
        while page <= max_pages:
            r = requests.post(
                f"{BASE_URL}/emailer_messages/search",
                headers=_headers(),
                json={"emailer_campaign_ids": [campaign_id], "per_page": 100, "page": page},
                timeout=15,
            )
            if r.status_code != 200:
                break
            msgs = r.json().get("emailer_messages", [])
            if not msgs:
                break
            for m in msgs:
                if m.get("replied"):
                    out.append({
                        "Name": m.get("to_name", "") or "",
                        "Email": m.get("to_email", "") or "",
                        "Replied On": (m.get("completed_at") or "")[:10],
                        "Type": m.get("reply_class") or "",
                    })
            if len(msgs) < 100:
                break
            page += 1
        return out
    except Exception:
        return out


@st.cache_data(ttl=300)
def get_mailboxes():
    try:
        r = requests.get(
            f"{BASE_URL}/email_accounts",
            headers=_headers(),
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("email_accounts", [])
        return []
    except Exception:
        return []
