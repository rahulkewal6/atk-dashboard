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
