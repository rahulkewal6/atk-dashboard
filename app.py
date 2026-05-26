import streamlit as st
from utils.sheets import get_pipeline_df
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

st.set_page_config(
    page_title="ATK Sales Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
require_login()
show_logo()
show_user_bar()

st.title("🏢 ATK Exhibitions — Sales Dashboard")
st.caption("Use the sidebar to navigate between pages.")

df = get_pipeline_df()

# --- SUMMARY METRICS ---
col1, col2, col3, col4 = st.columns(4)

if not df.empty and "Current Stage" in df.columns:
    hot = len(df[df["Current Stage"].str.contains("Hot Lead", na=False)])
    active = len(df[~df["Current Stage"].isin(["Won", "Lost", "No Response — Follow Up Later"])])
    won = len(df[df["Current Stage"] == "Won"])
    waiting = len(df[df["Current Stage"].str.contains("Waiting", na=False)])
else:
    hot = active = won = waiting = 0

with col1:
    st.metric("🔴 Hot Leads", hot, help="Needs immediate action")
with col2:
    st.metric("📋 Active Pipeline", active)
with col3:
    st.metric("✅ Won", won)
with col4:
    st.metric("⏳ Awaiting Response", waiting)

st.markdown("---")

# --- HOT LEADS TABLE ---
st.subheader("🔴 Hot Leads — Act Now")

if not df.empty and "Current Stage" in df.columns:
    hot_df = df[df["Current Stage"].str.contains("Hot Lead", na=False)]
    if not hot_df.empty:
        display_cols = [c for c in ["Company Name", "Exhibition", "Source", "Contact Email", "Date Added"] if c in hot_df.columns]
        st.dataframe(hot_df[display_cols], use_container_width=True)
        st.caption("Go to **Pipeline** page in the sidebar to update stages.")
    else:
        st.success("No hot leads pending action right now.")
else:
    st.info("No pipeline data yet. Add leads in the **Pipeline** page.")

st.markdown("---")
st.caption("ATK Exhibitions | Rahul & Bhavika")
