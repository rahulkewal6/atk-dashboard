import streamlit as st
from utils.sheets import get_pipeline_df
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar
from utils.brief_ui import render_brief_composer

inject_css()
require_login()
show_logo()
show_user_bar()

st.title("📐 Design Brief")
st.caption("Compose the brief, preview it, and send it straight to Imran — the lead auto-moves to "
           "'Brief Sent to Designer'.")

df = get_pipeline_df()
companies = (
    sorted(df["Company Name"].dropna().astype(str).unique().tolist())
    if not df.empty and "Company Name" in df.columns else []
)

# Prefill can come from a lead's "Send Design Brief" button
pre = st.session_state.pop("brief_prefill", None)

options = ["✏️ Type a new client"] + companies
default_idx = 0
if pre and pre.get("company") in companies:
    default_idx = options.index(pre["company"])

pick = st.selectbox("Client / lead", options, index=default_idx)

prefill = {"company": "", "exhibition": "", "size": "", "row_number": None}
if pick != "✏️ Type a new client" and not df.empty:
    match = df[df["Company Name"].astype(str) == pick]
    if not match.empty:
        row = match.iloc[0]
        prefill = {
            "company": pick,
            "exhibition": str(row.get("Exhibition", "") or ""),
            "size": str(row.get("Stand Size", "") or ""),
            "row_number": int(match.index[0]) + 1,
        }

st.markdown("---")
render_brief_composer(prefill)
