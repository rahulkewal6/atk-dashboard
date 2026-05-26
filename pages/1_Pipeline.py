import streamlit as st
import pandas as pd
from utils.sheets import get_pipeline_df, add_lead, update_lead_field, log_stage_change, get_stage_history
from utils.constants import PIPELINE_STAGES, STAGE_COLORS, EXHIBITIONS, SOURCES, USERS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, is_admin

st.set_page_config(page_title="Pipeline", page_icon="🔴", layout="wide")
inject_css()
require_login()
show_logo()
show_user_bar()

st.title("🔴 Pipeline")
st.markdown("All active leads and their current stages.")

# --- ADD NEW LEAD ---
with st.expander("➕ Add New Lead"):
    with st.form("add_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company Name *")
            exhibition = st.selectbox("Exhibition *", EXHIBITIONS)
            source = st.selectbox("Source *", SOURCES)
            source_custom = st.text_input("Specify source (if Other)", placeholder="e.g. WhatsApp referral, Trade show walk-in…")
        with col2:
            contact_name = st.text_input("Contact Name")
            contact_email = st.text_input("Contact Email")
            contact_phone = st.text_input("Contact Phone", placeholder="+971 50 XXX XXXX")
            added_by = st.selectbox("Added by *", USERS)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Lead")
        if submitted:
            if not company:
                st.error("Company name is required.")
            else:
                # Resolve source — use custom text if "Other (specify)" selected
                actual_source = source_custom.strip() if source == "Other (specify)" and source_custom.strip() else source

                # Default stage based on source
                if actual_source == "Apollo":
                    default_stage = "Hot Lead (Apollo)"
                elif actual_source == "Deepak":
                    default_stage = "Hot Lead (Deepak)"
                else:
                    default_stage = "Hot Lead (Inbound)"

                ok = add_lead({
                    "company_name": company,
                    "exhibition": exhibition,
                    "source": actual_source,
                    "contact_email": contact_email,
                    "contact_name": contact_name,
                    "contact_phone": contact_phone,
                    "current_stage": default_stage,
                    "notes": notes,
                    "updated_by": added_by,
                })
                if ok:
                    st.success(f"Lead added: {company}")
                    st.rerun()
                else:
                    st.error("Could not save. Check Google Sheets connection.")

st.markdown("---")

# --- FILTERS ---
col1, col2, col3 = st.columns(3)
with col1:
    filter_exhibition = st.multiselect("Exhibition", ["All"] + EXHIBITIONS, default=["All"])
with col2:
    filter_source = st.multiselect("Source", ["All"] + SOURCES, default=["All"])
with col3:
    filter_stage = st.multiselect("Stage", ["All"] + PIPELINE_STAGES, default=["All"])

# --- LOAD + FILTER DATA ---
df = get_pipeline_df()

if df.empty:
    st.info("No leads yet. Add your first lead above.")
    st.stop()

filtered = df.copy()
if "All" not in filter_exhibition and "Exhibition" in filtered.columns:
    filtered = filtered[filtered["Exhibition"].isin(filter_exhibition)]
if "All" not in filter_source and "Source" in filtered.columns:
    filtered = filtered[filtered["Source"].isin(filter_source)]
if "All" not in filter_stage and "Current Stage" in filtered.columns:
    filtered = filtered[filtered["Current Stage"].isin(filter_stage)]

st.markdown(f"**{len(filtered)} lead(s)**")

if filtered.empty:
    st.info("No leads match the current filters.")
    st.stop()

# --- LEAD CARDS ---
for idx, row in filtered.iterrows():
    stage = str(row.get("Current Stage", ""))
    icon = STAGE_COLORS.get(stage, "⚪")
    exhibition = str(row.get("Exhibition", ""))
    company = str(row.get("Company Name", "Unknown"))

    with st.expander(f"{icon}  {company}  —  {exhibition}  |  {stage}"):
        col_left, col_right = st.columns([3, 2])

        # --- LEFT: Lead Info ---
        with col_left:
            st.markdown(f"**Source:** {row.get('Source', '')}  |  **Added:** {row.get('Date Added', '')}  |  **Updated by:** {row.get('Last Updated By', '')}")
            phone = row.get('Contact Phone', '') or ''
            email = row.get('Contact Email', '') or ''
            name  = row.get('Contact Name', '')  or ''
            contact_parts = [p for p in [name, email, phone] if p]
            st.markdown(f"**Contact:** {' · '.join(contact_parts) if contact_parts else '—'}")

            # Design options indicator
            try:
                design_count = int(row.get("Design Options Sent", 0) or 0)
            except (ValueError, TypeError):
                design_count = 0
            design_display = " ".join(["✅" if i < design_count else "⬜" for i in range(3)])
            st.markdown(f"**Design Options Sent:** {design_display}")

            # Quotation summary
            vendor_q = row.get("Vendor Quote (AED)", "")
            margin = row.get("Margin (AED)", "")
            client_q = row.get("Client Quote (AED)", "")
            discount = row.get("Discount Given", "No")
            if any([vendor_q, margin, client_q]):
                if is_admin():
                    # Admin sees everything including internal cost + margin
                    st.markdown(
                        f"**Vendor Quote:** AED {vendor_q}  |  "
                        f"**Margin:** AED {margin}  |  "
                        f"**Client Quote:** AED {client_q}  |  "
                        f"**Discount:** {discount}"
                    )
                else:
                    # Editors see client quote only — vendor cost + margin hidden
                    st.markdown(
                        f"**Client Quote:** AED {client_q}  |  "
                        f"**Discount:** {discount}"
                    )

            # Stage history
            st.markdown("**Stage History:**")
            history = get_stage_history(company)
            if not history.empty:
                display_cols = [c for c in ["Stage", "Updated By", "Date/Time", "Notes"] if c in history.columns]
                st.dataframe(history[display_cols].reset_index(drop=True), use_container_width=True)
            else:
                st.caption("No history logged yet.")

        # --- RIGHT: Update Form ---
        with col_right:
            with st.form(f"form_{idx}"):
                st.markdown("**Update Lead**")

                new_stage = st.selectbox(
                    "Stage",
                    PIPELINE_STAGES,
                    index=PIPELINE_STAGES.index(stage) if stage in PIPELINE_STAGES else 0,
                )
                updated_by = st.selectbox("Updated by", USERS)

                brief_ver = st.selectbox(
                    "Brief Version",
                    [1, 2, 3],
                    index=max(0, int(row.get("Brief Version", 1) or 1) - 1),
                )
                design_opts = st.selectbox(
                    "Design Options Sent",
                    [0, 1, 2, 3],
                    index=min(3, max(0, int(row.get("Design Options Sent", 0) or 0))),
                )

                # Quotation fields
                show_quote = any(k in new_stage for k in ["Vendor", "Quotation", "Quote", "Discount"])
                new_vendor_q = str(vendor_q)
                new_margin = str(margin)
                if show_quote:
                    st.markdown("**Quotation**")
                    if is_admin():
                        new_vendor_q = st.text_input("Vendor Quote (AED)", value=str(vendor_q))
                        new_margin = st.text_input("Margin (AED)", value=str(margin))
                    new_client_q = st.text_input("Client Quote (AED)", value=str(client_q))
                    new_discount = st.selectbox("Discount Given", ["No", "Yes"],
                                                index=0 if discount != "Yes" else 1)
                else:
                    new_client_q = str(client_q)
                    new_discount = str(discount)

                new_phone = st.text_input("Contact Phone", value=str(row.get("Contact Phone", "") or ""))
                new_notes = st.text_area("Notes", value=str(row.get("Notes", "")))

                save = st.form_submit_button("💾 Save Changes")
                if save:
                    row_number = idx + 1
                    update_lead_field(row_number, "Current Stage", new_stage, updated_by)
                    update_lead_field(row_number, "Brief Version", brief_ver, updated_by)
                    update_lead_field(row_number, "Design Options Sent", design_opts, updated_by)
                    update_lead_field(row_number, "Contact Phone", new_phone, updated_by)
                    update_lead_field(row_number, "Notes", new_notes, updated_by)
                    if show_quote:
                        update_lead_field(row_number, "Vendor Quote (AED)", new_vendor_q, updated_by)
                        update_lead_field(row_number, "Margin (AED)", new_margin, updated_by)
                        update_lead_field(row_number, "Client Quote (AED)", new_client_q, updated_by)
                        update_lead_field(row_number, "Discount Given", new_discount, updated_by)
                    log_stage_change(company, new_stage, updated_by, new_notes)
                    st.success("Saved!")
                    st.rerun()
