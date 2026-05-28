import streamlit as st
import pandas as pd
import io
from datetime import date
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
st.markdown("Central store for all exhibitor lists. Upload once — everyone can browse and download.")

# ── SESSION STATE ────────────────────────────────────────────────────────────
if "db_viewing" not in st.session_state:
    st.session_state.db_viewing = None   # which list is open in detail view

# ── LOAD DATA ────────────────────────────────────────────────────────────────
df_all = get_exhibitor_df()

# ── SUMMARY METRICS ──────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
if not df_all.empty:
    events    = df_all["Event Name"].nunique() if "Event Name" in df_all.columns else 0
    total     = len(df_all)
    has_email = int(df_all["Email"].astype(str).str.contains("@", na=False).sum()) if "Email" in df_all.columns else 0
    no_email  = total - has_email
else:
    events = total = has_email = no_email = 0

col1.metric("Lists Stored", events)
col2.metric("Total Contacts", total)
col3.metric("Have Email ✅", has_email)
col4.metric("Missing Email ⚠️", no_email)

st.markdown("---")

# ── UPLOAD ───────────────────────────────────────────────────────────────────
with st.expander("⬆️ Upload New List"):
    st.caption("Supported: Excel (.xlsx, .xls) or CSV (.csv)")

    c1, c2 = st.columns(2)
    with c1:
        list_type = st.radio(
            "List type",
            ["Exhibition list", "Personal / custom list"],
            horizontal=True,
            key="db_list_type",
        )
        if list_type == "Exhibition list":
            event_choice = st.selectbox("Exhibition", EXHIBITIONS, key="db_event_sel")
            event_override = st.text_input(
                "Or type a different name (e.g. JITEX 2026, Big 5 2026)",
                placeholder="Leave blank to use the selection above",
                key="db_event_override",
            )
        else:
            event_choice  = ""
            event_override = st.text_input(
                "List name *",
                placeholder="e.g. Bhavika LinkedIn Leads, Deepak Cold Calls May 2026…",
                key="db_event_custom",
            )
        event_date = st.date_input("Event Start Date", value=None, key="db_event_date")
        uploaded_by = st.selectbox("Uploaded by *", USERS, key="db_uploader")

    with c2:
        uploaded_file = st.file_uploader(
            "Drop your file here", type=["xlsx", "xls", "csv"], key="db_file"
        )

    if uploaded_file:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file, engine="openpyxl")
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        st.markdown(f"**{len(raw_df)} rows detected — first 5 rows:**")
        st.dataframe(raw_df.head(5), use_container_width=True, hide_index=True)

        st.markdown("**Map your columns → our fields** ('— skip —' = column not in your file):")
        col_opts = ["— skip —"] + list(raw_df.columns)

        def best_guess(keywords):
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
        with mc7: map_phone   = st.selectbox("Phone",           col_opts, index=best_guess(["phone","mobile","tel"]))
        with mc8: map_contact = st.selectbox("Contact Name",    col_opts, index=best_guess(["contact","person","rep","first"]))

        if st.button("✅ Upload to Database", type="primary"):
            event_label = (
                event_override.strip() or event_choice
                if list_type == "Exhibition list"
                else event_override.strip()
            )
            if not event_label:
                st.error("Please enter a list name.")
            else:
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
                event_date_str = event_date.strftime("%d-%b-%Y") if event_date else ""
                rows = []
                for _, r in raw_df.iterrows():
                    row = {"Event Name": event_label, "Event Date": event_date_str, "Uploaded By": uploaded_by}
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

# ── DETAIL VIEW (when a list is selected) ────────────────────────────────────
if st.session_state.db_viewing:
    selected = st.session_state.db_viewing

    if st.button("← Back to all lists"):
        st.session_state.db_viewing = None
        st.rerun()

    detail_df = df_all[df_all["Event Name"] == selected].copy() if "Event Name" in df_all.columns else pd.DataFrame()

    # Show event date if available
    if not detail_df.empty and "Event Date" in detail_df.columns:
        ev_date = detail_df["Event Date"].replace("", float("nan")).dropna().iloc[0] if not detail_df["Event Date"].replace("", float("nan")).dropna().empty else None
        if ev_date:
            st.subheader(f"📋 {selected}   •   📅 {ev_date}")
        else:
            st.subheader(f"📋 {selected}")
    else:
        st.subheader(f"📋 {selected}")

    if detail_df.empty:
        st.info("No contacts found for this list.")
    else:
        # Search + filter
        s1, s2 = st.columns([3, 1])
        with s1:
            search = st.text_input("Search", placeholder="Company name, email, country…", key="detail_search")
        with s2:
            st.markdown("<br>", unsafe_allow_html=True)
            email_only = st.checkbox("Has email only", key="detail_email_only")

        if search:
            mask = detail_df.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
            detail_df = detail_df[mask]
        if email_only and "Email" in detail_df.columns:
            detail_df = detail_df[detail_df["Email"].astype(str).str.contains("@", na=False)]

        display_cols = [c for c in [
            "Company Name", "Stand Number", "Hall / Pavilion",
            "Country", "Email", "Website", "Phone", "Contact Name", "Event Date", "Upload Date"
        ] if c in detail_df.columns]

        st.markdown(f"**{len(detail_df)} contact(s)**")
        st.dataframe(detail_df[display_cols].reset_index(drop=True), use_container_width=True, hide_index=True)

        # Downloads
        dl1, dl2 = st.columns(2)
        safe_name = selected.replace(" ", "_").replace("/", "-")
        with dl1:
            st.download_button(
                "⬇️ Download CSV",
                data=detail_df[display_cols].to_csv(index=False).encode("utf-8"),
                file_name=f"{safe_name}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                detail_df[display_cols].to_excel(w, index=False, sheet_name="Contacts")
            st.download_button(
                "⬇️ Download Excel",
                data=buf.getvalue(),
                file_name=f"{safe_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        # Admin delete
        if is_admin():
            st.markdown("---")
            with st.expander("🗑️ Admin — Delete this list"):
                st.warning(f"Permanently deletes all {len(df_all[df_all['Event Name']==selected])} contacts for **{selected}**.")
                confirm = st.text_input("Type the list name to confirm")
                if st.button("Delete permanently", type="primary"):
                    if confirm.strip() == selected:
                        if delete_event_exhibitors(selected):
                            st.success("Deleted.")
                            st.session_state.db_viewing = None
                            st.rerun()
                        else:
                            st.error("Delete failed.")
                    else:
                        st.error("Name doesn't match.")

    st.stop()

# ── LIBRARY VIEW (default — shows all lists as cards) ────────────────────────
st.subheader("All Lists")

if df_all.empty:
    st.info("No lists uploaded yet. Use the upload section above to get started.")
    st.stop()

# Build summary table
summary_rows = []
for event in sorted(df_all["Event Name"].dropna().unique()):
    edf = df_all[df_all["Event Name"] == event]
    count       = len(edf)
    with_email  = int(edf["Email"].astype(str).str.contains("@", na=False).sum()) if "Email" in edf.columns else 0
    uploader    = edf["Uploaded By"].dropna().iloc[-1] if "Uploaded By" in edf.columns and not edf.empty else "—"
    upload_date = edf["Upload Date"].dropna().iloc[-1] if "Upload Date" in edf.columns and not edf.empty else "—"
    event_date_val = edf["Event Date"].dropna().replace("", float("nan")).dropna().iloc[0] if "Event Date" in edf.columns and not edf["Event Date"].replace("", float("nan")).dropna().empty else "—"
    summary_rows.append({
        "List Name":    event,
        "Event Date":   event_date_val,
        "Contacts":     count,
        "Have Email":   with_email,
        "Missing Email":count - with_email,
        "Uploaded By":  uploader,
        "Last Updated": upload_date,
    })

summary_df = pd.DataFrame(summary_rows)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

st.markdown("**Click a list below to open it:**")

# One button per list
btn_cols = st.columns(min(len(summary_rows), 4))
for i, row in enumerate(summary_rows):
    with btn_cols[i % 4]:
        if st.button(
            f"📂 {row['List Name']}\n{row['Contacts']} contacts",
            use_container_width=True,
            key=f"open_{i}",
        ):
            st.session_state.db_viewing = row["List Name"]
            st.rerun()
