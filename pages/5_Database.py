import streamlit as st
import pandas as pd
import io
from datetime import datetime
from utils.sheets import get_exhibitor_df, add_exhibitor_rows, delete_event_exhibitors
from utils.constants import EXHIBITIONS, USERS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, is_admin

st.set_page_config(page_title="Database", page_icon="🗄️", layout="wide")
inject_css()
require_login()
show_logo()
show_user_bar()

st.title("🗄️ Exhibitor Database")
st.markdown("Central store for all exhibitor lists. Upload once — everyone on the team can browse and download.")

# ── SUMMARY METRICS ─────────────────────────────────────────────────────────
df_all = get_exhibitor_df()

col1, col2, col3, col4 = st.columns(4)
if not df_all.empty:
    events    = df_all["Event Name"].nunique() if "Event Name" in df_all.columns else 0
    total     = len(df_all)
    has_email = int(df_all["Email"].astype(str).str.contains("@", na=False).sum()) if "Email" in df_all.columns else 0
    no_email  = total - has_email
else:
    events = total = has_email = no_email = 0

col1.metric("Events Loaded", events)
col2.metric("Total Contacts", total)
col3.metric("Have Email ✅", has_email)
col4.metric("Missing Email ⚠️", no_email)

st.markdown("---")

# ── UPLOAD ───────────────────────────────────────────────────────────────────
with st.expander("⬆️ Upload New Exhibitor List"):
    st.caption("Supported formats: Excel (.xlsx, .xls) or CSV (.csv)")

    c1, c2 = st.columns(2)
    with c1:
        event_choice = st.selectbox("Exhibition *", EXHIBITIONS, key="db_event")
        event_custom = st.text_input("Or type a custom event name", key="db_event_custom")
        uploaded_by  = st.selectbox("Uploaded by *", USERS, key="db_uploader")
    with c2:
        uploaded_file = st.file_uploader(
            "Drop your file here", type=["xlsx", "xls", "csv"], key="db_file"
        )

    if uploaded_file:
        # Read file
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file, engine="openpyxl")
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        st.markdown(f"**Preview — {len(raw_df)} rows detected:**")
        st.dataframe(raw_df.head(5), use_container_width=True, hide_index=True)

        # Column mapping
        st.markdown("**Map your columns → our fields** (select '— skip —' for any column you don't have):")
        col_opts = ["— skip —"] + list(raw_df.columns)

        def best_guess(keywords):
            """Auto-select a column if its name contains any keyword."""
            for kw in keywords:
                for c in raw_df.columns:
                    if kw.lower() in c.lower():
                        return col_opts.index(c)
            return 0

        mc1, mc2, mc3 = st.columns(3)
        mc4, mc5, mc6 = st.columns(3)
        mc7, mc8      = st.columns(2)

        with mc1: map_company = st.selectbox("Company Name",    col_opts, index=best_guess(["company","name","exhibitor","brand"]))
        with mc2: map_stand   = st.selectbox("Stand Number",    col_opts, index=best_guess(["stand","booth","stall"]))
        with mc3: map_hall    = st.selectbox("Hall / Pavilion", col_opts, index=best_guess(["hall","pavilion","zone"]))
        with mc4: map_country = st.selectbox("Country",         col_opts, index=best_guess(["country","nation"]))
        with mc5: map_website = st.selectbox("Website",         col_opts, index=best_guess(["website","web","url","site"]))
        with mc6: map_email   = st.selectbox("Email",           col_opts, index=best_guess(["email","e-mail","mail"]))
        with mc7: map_phone   = st.selectbox("Phone",           col_opts, index=best_guess(["phone","mobile","tel","contact"]))
        with mc8: map_contact = st.selectbox("Contact Name",    col_opts, index=best_guess(["contact","person","rep","first"]))

        if st.button("✅ Upload to Database", type="primary"):
            event_label = event_custom.strip() if event_custom.strip() else event_choice

            mapping = {
                "Company Name":    map_company,
                "Stand Number":    map_stand,
                "Hall / Pavilion": map_hall,
                "Country":         map_country,
                "Website":         map_website,
                "Email":           map_email,
                "Phone":           map_phone,
                "Contact Name":    map_contact,
            }

            rows = []
            for _, r in raw_df.iterrows():
                row = {"Event Name": event_label, "Uploaded By": uploaded_by}
                for field, src_col in mapping.items():
                    row[field] = str(r[src_col]) if src_col != "— skip —" and src_col in r else ""
                rows.append(row)

            with st.spinner(f"Uploading {len(rows)} contacts…"):
                ok = add_exhibitor_rows(rows)

            if ok:
                st.success(f"✅ {len(rows)} contacts uploaded for **{event_label}**")
                st.rerun()
            else:
                st.error("Upload failed. Check Google Sheets connection.")

st.markdown("---")

# ── BROWSE + DOWNLOAD ────────────────────────────────────────────────────────
st.subheader("Browse & Download")

if df_all.empty:
    st.info("No exhibitor data yet. Upload your first list above.")
    st.stop()

events_available = sorted(df_all["Event Name"].dropna().unique().tolist()) if "Event Name" in df_all.columns else []

fc1, fc2, fc3 = st.columns([2, 2, 1])
with fc1:
    selected_event = st.selectbox("Filter by Event", ["All events"] + events_available)
with fc2:
    search_term = st.text_input("Search company or email", placeholder="Type to filter…")
with fc3:
    st.markdown("<br>", unsafe_allow_html=True)
    only_with_email = st.checkbox("Has email only")

# Apply filters
filtered = df_all.copy()
if selected_event != "All events" and "Event Name" in filtered.columns:
    filtered = filtered[filtered["Event Name"] == selected_event]
if search_term:
    mask = filtered.apply(lambda col: col.astype(str).str.contains(search_term, case=False, na=False)).any(axis=1)
    filtered = filtered[mask]
if only_with_email and "Email" in filtered.columns:
    filtered = filtered[filtered["Email"].astype(str).str.contains("@", na=False)]

st.markdown(f"**{len(filtered)} contact(s) shown**")

display_cols = [c for c in [
    "Event Name", "Company Name", "Stand Number", "Hall / Pavilion",
    "Country", "Email", "Website", "Phone", "Contact Name", "Uploaded By", "Upload Date"
] if c in filtered.columns]

st.dataframe(filtered[display_cols].reset_index(drop=True), use_container_width=True, hide_index=True)

# Download buttons
dl1, dl2 = st.columns(2)
with dl1:
    csv_bytes = filtered[display_cols].to_csv(index=False).encode("utf-8")
    fname = f"{selected_event.replace(' ', '_')}_exhibitors.csv" if selected_event != "All events" else "all_exhibitors.csv"
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv_bytes,
        file_name=fname,
        mime="text/csv",
        use_container_width=True,
    )

with dl2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        filtered[display_cols].to_excel(writer, index=False, sheet_name="Exhibitors")
    xlsx_bytes = buffer.getvalue()
    xname = fname.replace(".csv", ".xlsx")
    st.download_button(
        label="⬇️ Download as Excel",
        data=xlsx_bytes,
        file_name=xname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

# ── ADMIN: DELETE EVENT DATA ─────────────────────────────────────────────────
if is_admin() and selected_event != "All events":
    st.markdown("---")
    with st.expander("🗑️ Admin — Delete Event Data"):
        st.warning(f"This will permanently delete all **{selected_event}** contacts from the database.")
        confirm = st.text_input(f"Type the event name to confirm deletion")
        if st.button("Delete", type="primary"):
            if confirm.strip() == selected_event:
                ok = delete_event_exhibitors(selected_event)
                if ok:
                    st.success(f"Deleted all contacts for {selected_event}")
                    st.rerun()
                else:
                    st.error("Delete failed.")
            else:
                st.error("Event name doesn't match. Nothing deleted.")
