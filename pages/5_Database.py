import streamlit as st
import pandas as pd
import io
from utils.sheets import (
    get_exhibitor_df, add_exhibitor_rows, delete_event_exhibitors,
    update_call_status, get_all_exhibitor_events, get_event_sheet_url,
)
from utils.constants import EXHIBITIONS, USERS, CALL_STATUSES
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, is_admin

st.set_page_config(page_title="Database", page_icon="🗄️", layout="wide")
inject_css()
require_login()
show_logo()
show_user_bar()

st.title("🗄️ Exhibitor Database")
st.markdown("Each exhibitor list is stored in its own Google Sheet. Click a list to view, track calls, and export.")

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "db_viewing" not in st.session_state:
    st.session_state.db_viewing = None

# ── LOAD REGISTRY (fast — 1 API call) ────────────────────────────────────────
all_events = get_all_exhibitor_events()   # [{name, url, total, called, ...}]

# ── SUMMARY METRICS ───────────────────────────────────────────────────────────
lists_count = len(all_events)
total_contacts = sum(ev["total"]  for ev in all_events)
total_called   = sum(ev["called"] for ev in all_events)
total_pending  = total_contacts - total_called

col1, col2, col3, col4 = st.columns(4)
col1.metric("Lists Stored",    lists_count)
col2.metric("Total Contacts",  total_contacts)
col3.metric("Called ✅",       total_called)
col4.metric("Pending 🕐",      total_pending)

st.markdown("---")

# ── UPLOAD ────────────────────────────────────────────────────────────────────
with st.expander("⬆️ Upload New List"):
    st.caption("Supported: Excel (.xlsx, .xls) or CSV (.csv). A new Google Sheet is created automatically for each list.")

    c1, c2 = st.columns(2)
    with c1:
        list_type = st.radio("List type", ["Exhibition list", "Personal / custom list"], horizontal=True, key="db_list_type")
        if list_type == "Exhibition list":
            event_choice   = st.selectbox("Exhibition", EXHIBITIONS, key="db_event_sel")
            event_override = st.text_input("Or type a different name (e.g. JITEX 2026, Big 5)", placeholder="Leave blank to use selection above", key="db_event_override")
        else:
            event_choice   = ""
            event_override = st.text_input("List name *", placeholder="e.g. Bhavika LinkedIn Leads…", key="db_event_custom")
        event_date  = st.date_input("Event Start Date (optional)", value=None, key="db_event_date")
        uploaded_by = st.selectbox("Uploaded by *", USERS, key="db_uploader")
    with c2:
        uploaded_file = st.file_uploader("Drop your file here", type=["xlsx", "xls", "csv"], key="db_file")

    if uploaded_file:
        try:
            raw_df = (pd.read_csv(uploaded_file) if uploaded_file.name.lower().endswith(".csv")
                      else pd.read_excel(uploaded_file, engine="openpyxl"))
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        st.markdown(f"**{len(raw_df)} rows detected — first 5 rows:**")
        st.dataframe(raw_df.head(5), use_container_width=True, hide_index=True)

        st.markdown("**Map your columns → our fields:**")
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
            event_label = (event_override.strip() or event_choice) if list_type == "Exhibition list" else event_override.strip()
            if not event_label:
                st.error("Please enter a list name.")
            else:
                event_date_str = event_date.strftime("%d-%b-%Y") if event_date else ""
                mapping = {
                    "Company Name": map_company, "Stand Number": map_stand,
                    "Hall / Pavilion": map_hall, "Country": map_country,
                    "Website": map_website, "Email": map_email,
                    "Phone": map_phone, "Contact Name": map_contact,
                }
                rows = []
                for _, r in raw_df.iterrows():
                    row = {
                        "Event Name": event_label, "Event Date": event_date_str,
                        "Uploaded By": uploaded_by, "Call Status": "Not Called",
                    }
                    for field, src_col in mapping.items():
                        row[field] = str(r[src_col]) if src_col != "— skip —" and src_col in r else ""
                    rows.append(row)
                with st.spinner(f"Creating Google Sheet and uploading {len(rows)} contacts…"):
                    ok = add_exhibitor_rows(rows, event_label)
                if ok:
                    sheet_url = get_event_sheet_url(event_label)
                    st.success(f"✅ {len(rows)} contacts uploaded for **{event_label}**")
                    if sheet_url:
                        st.markdown(
                            f"<a href='{sheet_url}' target='_blank' style='color:#FF6600; font-weight:600;'>"
                            f"📊 Open {event_label} in Google Sheets →</a>",
                            unsafe_allow_html=True,
                        )
                    st.rerun()
                else:
                    st.error("Upload failed. Check Google Sheets connection.")

st.markdown("---")

# ── DETAIL VIEW ───────────────────────────────────────────────────────────────
if st.session_state.db_viewing:
    selected = st.session_state.db_viewing
    event_tab_url = get_event_sheet_url(selected)

    hcol1, hcol2 = st.columns([1, 3])
    with hcol1:
        if st.button("← Back to all lists"):
            st.session_state.db_viewing = None
            st.rerun()
    with hcol2:
        if event_tab_url:
            st.markdown(
                f"<a href='{event_tab_url}' target='_blank' style='color:#FF6600; font-weight:600; font-size:1rem;'>"
                f"📊 Open {selected} in Google Sheets →</a>",
                unsafe_allow_html=True,
            )
            st.caption("Changes made in Google Sheets reflect here within 60 seconds.")

    with st.spinner("Loading contacts…"):
        detail_df = get_exhibitor_df(event_name=selected)

    if detail_df.empty:
        st.info("No contacts found for this list.")
        st.stop()

    # Header + progress bar
    ev_date = ""
    if "Event Date" in detail_df.columns:
        dates = detail_df["Event Date"].replace("", float("nan")).dropna()
        if not dates.empty:
            ev_date = f"   •   📅 {dates.iloc[0]}"

    st.subheader(f"📋 {selected}{ev_date}")

    total_list = len(detail_df)
    if "Call Status" in detail_df.columns:
        called_list  = int((detail_df["Call Status"].astype(str) != "Not Called").sum())
        pending_list = total_list - called_list
        pct = int((called_list / total_list) * 100) if total_list > 0 else 0
        st.markdown(f"**Progress: {called_list} / {total_list} called ({pct}%) — {pending_list} remaining**")
        st.progress(pct / 100)

    # Filters
    f1, f2, f3, f4 = st.columns([2, 2, 1, 1])
    with f1:
        status_filter = st.selectbox("Call Status", ["All"] + CALL_STATUSES, key="detail_status")
    with f2:
        search = st.text_input("Search", placeholder="Company, email, country…", key="detail_search")
    with f3:
        caller_filter = st.selectbox("Called By", ["All"] + USERS, key="detail_caller")
    with f4:
        st.markdown("<br>", unsafe_allow_html=True)
        email_only = st.checkbox("Has email only", key="detail_email")

    filtered = detail_df.copy()
    if status_filter != "All" and "Call Status" in filtered.columns:
        filtered = filtered[filtered["Call Status"].astype(str) == status_filter]
    if caller_filter != "All" and "Called By" in filtered.columns:
        filtered = filtered[filtered["Called By"].astype(str) == caller_filter]
    if search:
        mask = filtered.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]
    if email_only and "Email" in filtered.columns:
        filtered = filtered[filtered["Email"].astype(str).str.contains("@", na=False)]

    st.markdown(f"**{len(filtered)} contact(s) shown**")

    display_cols = [c for c in [
        "Company Name", "Call Status", "Called By", "Call Notes",
        "Stand Number", "Hall / Pavilion", "Country", "Email", "Website", "Phone", "Contact Name"
    ] if c in filtered.columns]

    st.dataframe(filtered[display_cols].reset_index(drop=True), use_container_width=True, hide_index=True)

    # ── INLINE CALL STATUS UPDATE ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**Update call status for a contact:**")
    st.caption("Or open the Google Sheets link above to update multiple rows at once.")

    company_list = filtered["Company Name"].dropna().unique().tolist() if "Company Name" in filtered.columns else []
    if company_list:
        uc1, uc2, uc3 = st.columns([2, 1, 1])
        with uc1:
            target_company = st.selectbox("Company", company_list, key="update_company")
        with uc2:
            current_status = ""
            if "Call Status" in filtered.columns:
                match = filtered[filtered["Company Name"] == target_company]["Call Status"].values
                current_status = match[0] if len(match) > 0 else "Not Called"
            new_status = st.selectbox("Status", CALL_STATUSES,
                                      index=CALL_STATUSES.index(current_status) if current_status in CALL_STATUSES else 0,
                                      key="update_status")
        with uc3:
            caller = st.selectbox("Called by", USERS, key="update_caller")
        call_notes = st.text_input("Notes (optional)", placeholder="e.g. Spoke to Ahmed, call back Thursday", key="update_notes")

        if st.button("💾 Save Call Status", type="primary"):
            with st.spinner("Saving…"):
                ok = update_call_status(selected, target_company, new_status, caller, call_notes)
            if ok:
                st.success(f"✅ Updated: {target_company} → {new_status}")
                st.rerun()
            else:
                st.warning("Could not update. Try editing directly in Google Sheets.")

    # Downloads
    st.markdown("---")
    safe_name = selected.replace(" ", "_").replace("/", "-")
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button("⬇️ Download CSV",
                           data=filtered[display_cols].to_csv(index=False).encode("utf-8"),
                           file_name=f"{safe_name}.csv", mime="text/csv",
                           use_container_width=True)
    with dl2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            filtered[display_cols].to_excel(w, index=False, sheet_name="Contacts")
        st.download_button("⬇️ Download Excel", data=buf.getvalue(),
                           file_name=f"{safe_name}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with dl3:
        if event_tab_url:
            st.link_button("📊 Open Google Sheets", event_tab_url, use_container_width=True)

    if is_admin():
        st.markdown("---")
        with st.expander("🗑️ Admin — Delete this list"):
            st.warning(f"Permanently deletes all {total_list} contacts for **{selected}** and removes the Google Sheet.")
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

# ── LIBRARY VIEW ──────────────────────────────────────────────────────────────
st.subheader("All Lists")

if not all_events:
    st.info("No lists uploaded yet. Use the upload section above to get started.")
    st.stop()

st.markdown("")

# Summary table from registry (no extra API calls needed)
summary_rows = []
for ev in sorted(all_events, key=lambda x: x["name"]):
    count    = ev["total"]
    called_n = ev["called"]
    pct_done = f"{int(called_n / count * 100)}%" if count > 0 else "0%"
    summary_rows.append({
        "List Name":   ev["name"],
        "Event Date":  ev["event_date"],
        "Contacts":    count,
        "Called":      called_n,
        "Pending":     count - called_n,
        "Progress":    pct_done,
        "Uploaded By": ev["uploaded_by"],
    })

st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

st.markdown("**Click a list to open it:**")
btn_cols = st.columns(min(len(all_events), 4))
for i, ev in enumerate(sorted(all_events, key=lambda x: x["name"])):
    with btn_cols[i % 4]:
        called_n = ev["called"]
        count    = ev["total"]
        label    = f"📂 {ev['name']}\n{called_n}/{count} called"
        if st.button(label, use_container_width=True, key=f"open_{i}"):
            st.session_state.db_viewing = ev["name"]
            st.rerun()
        if ev["url"]:
            st.markdown(
                f"<a href='{ev['url']}' target='_blank' "
                f"style='font-size:0.75rem; color:#FF6600;'>📊 Open Google Sheet</a>",
                unsafe_allow_html=True,
            )
