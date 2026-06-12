import streamlit as st
import pandas as pd
from utils.sheets import get_pipeline_df
from utils.constants import EXHIBITIONS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

inject_css()
require_login()
show_logo()
show_user_bar()

st.title("📈 Reports")
st.markdown("Monthly performance summary across all exhibitions.")

df = get_pipeline_df()

if df.empty or "Current Stage" not in df.columns:
    st.info("No pipeline data yet. Leads will appear here once added.")
    st.stop()

closed_stages = ["Won", "Lost", "No Response — Follow Up Later"]

# --- SUMMARY METRICS ---
col1, col2, col3, col4 = st.columns(4)
total = len(df)
won = len(df[df["Current Stage"] == "Won"])
lost = len(df[df["Current Stage"] == "Lost"])
active = len(df[~df["Current Stage"].isin(closed_stages)])

with col1:
    st.metric("Total Leads", total)
with col2:
    st.metric("✅ Won", won)
with col3:
    st.metric("❌ Lost", lost)
with col4:
    st.metric("📋 Active", active)

st.markdown("---")

# --- BY EXHIBITION ---
st.subheader("Performance by Exhibition")
if "Exhibition" in df.columns:
    expo_rows = []
    for expo in sorted(df["Exhibition"].dropna().unique()):
        edf = df[df["Exhibition"] == expo]
        expo_rows.append({
            "Exhibition": expo,
            "Total Leads": len(edf),
            "Active": len(edf[~edf["Current Stage"].isin(closed_stages)]),
            "Won": len(edf[edf["Current Stage"] == "Won"]),
            "Lost": len(edf[edf["Current Stage"] == "Lost"]),
            "No Response": len(edf[edf["Current Stage"] == "No Response — Follow Up Later"]),
        })
    st.dataframe(pd.DataFrame(expo_rows), use_container_width=True)

st.markdown("---")

# --- BY SOURCE ---
st.subheader("Leads by Source")
if "Source" in df.columns:
    source_rows = []
    for src in sorted(df["Source"].dropna().unique()):
        sdf = df[df["Source"] == src]
        source_rows.append({
            "Source": src,
            "Total": len(sdf),
            "Active": len(sdf[~sdf["Current Stage"].isin(closed_stages)]),
            "Won": len(sdf[sdf["Current Stage"] == "Won"]),
        })
    st.dataframe(pd.DataFrame(source_rows), use_container_width=True)

st.markdown("---")

# --- STAGE DISTRIBUTION ---
st.subheader("Stage Distribution")
if "Current Stage" in df.columns:
    stage_counts = (
        df["Current Stage"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Stage", "Current Stage": "Count"})
    )
    st.dataframe(stage_counts, use_container_width=True)

st.markdown("---")

# --- QUOTATION SUMMARY ---
st.subheader("Quotation Pipeline")
quote_cols = [c for c in ["Company Name", "Exhibition", "Client Quote (AED)", "Current Stage"] if c in df.columns]
quote_df = df[df["Client Quote (AED)"].astype(str).str.strip() != ""][quote_cols] if "Client Quote (AED)" in df.columns else pd.DataFrame()
if not quote_df.empty:
    st.dataframe(quote_df, use_container_width=True)
    try:
        total_pipeline = pd.to_numeric(quote_df["Client Quote (AED)"], errors="coerce").sum()
        st.metric("Total Pipeline Value (AED)", f"{total_pipeline:,.0f}")
    except Exception:
        pass
else:
    st.info("No quotations logged yet.")
