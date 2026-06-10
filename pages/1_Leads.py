import streamlit as st
import pandas as pd
from datetime import date
from utils.sheets import get_pipeline_df, add_lead, update_lead_field, log_stage_change, get_stage_history, add_followup, get_due_count
from utils.constants import PIPELINE_STAGES, EXHIBITIONS, SOURCES, USERS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, is_admin

st.set_page_config(page_title="Leads", page_icon="🔴", layout="wide")
inject_css()
require_login()
show_logo()
show_user_bar()

# Stages where action is needed — shown in red
_PENDING_STAGES = {
    "Hot Lead (Apollo)", "Hot Lead (Deepak)", "Hot Lead (Inbound)",
    "Info Request Replied",
    "Waiting for Design Feedback", "Waiting for Final Approval",
    "No Response — Follow Up Later", "Client Requested Discount",
    "Additional Changes Requested", "New Brief Received (Client Changed)",
}

# Stages where work is actively progressing — shown in green
_ACTIVE_STAGES = {
    "Brief Received (v1)", "Brief Received (v2)", "Brief Received (v3)",
    "Brief Sent to Designer",
    "Design Option 1 Sent", "Design Option 2 Sent", "Design Option 3 Sent",
    "Revised Brief Sent to Designer",
    "Brief Sent to Vendor", "Vendor Quotation Received",
    "Client Quotation Prepared", "Client Quotation 1 Sent",
    "Discounted Quotation Sent", "Revised Quotation Sent",
    "Waiting for Final Approval",
}

def _stage_pill(stage: str) -> str:
    """Coloured HTML pill for the current stage."""
    if stage in _PENDING_STAGES:
        color, bg = "#c0392b", "#fdecea"
    elif stage == "Won":
        color, bg = "#1a7a3f", "#e8f8ed"
    elif stage == "Lost":
        color, bg = "#777", "#f0f0f0"
    elif stage in _ACTIVE_STAGES:
        color, bg = "#1a7a3f", "#e8f8ed"
    else:
        color, bg = "#b35c00", "#fff3e6"
    return (
        f'<span style="background:{bg};color:{color};padding:3px 12px;'
        f'border-radius:12px;font-size:0.8em;font-weight:600;'
        f'border:1px solid {color}40;">{stage}</span>'
    )


st.title("🔴 Leads")
st.markdown("All active leads and their current stages.")

# Sidebar notification badge for due follow-ups
_due = get_due_count()
if _due:
    st.sidebar.error(f"🔔 {_due} follow-up{'s' if _due > 1 else ''} due — check Tasks")

# ── Add New Lead ──────────────────────────────────────────────────────────────
with st.expander("➕ Add New Lead"):
    with st.form("add_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            company       = st.text_input("Company Name *")
            exhibition    = st.selectbox("Exhibition *", EXHIBITIONS)
            source        = st.selectbox("Source *", SOURCES)
            source_custom = st.text_input("Specify source (if Other)", placeholder="e.g. WhatsApp referral")
        with col2:
            contact_name  = st.text_input("Contact Name")
            contact_email = st.text_input("Contact Email")
            contact_phone = st.text_input("Contact Phone", placeholder="+971 50 XXX XXXX")
            added_by      = st.selectbox("Added by *", USERS)
        notes = st.text_area("Notes")
        if st.form_submit_button("Add Lead"):
            if not company:
                st.error("Company name is required.")
            else:
                actual_source = (
                    source_custom.strip()
                    if source == "Other (specify)" and source_custom.strip()
                    else source
                )
                default_stage = (
                    "Hot Lead (Apollo)"  if actual_source == "Apollo"  else
                    "Hot Lead (Deepak)"  if actual_source == "Deepak"  else
                    "Hot Lead (Inbound)"
                )
                ok = add_lead({
                    "company_name": company, "exhibition": exhibition,
                    "source": actual_source, "contact_email": contact_email,
                    "contact_name": contact_name, "contact_phone": contact_phone,
                    "current_stage": default_stage, "notes": notes, "updated_by": added_by,
                })
                if ok:
                    st.success(f"Lead added: {company}")
                    st.rerun()
                else:
                    st.error("Could not save. Check Google Sheets connection.")

st.markdown("---")

# ── Filters ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    filter_exhibition = st.multiselect("Exhibition", ["All"] + EXHIBITIONS, default=["All"])
with c2:
    filter_source = st.multiselect("Source", ["All"] + SOURCES, default=["All"])
with c3:
    filter_stage = st.multiselect("Stage", ["All"] + PIPELINE_STAGES, default=["All"])

# ── Load & filter ─────────────────────────────────────────────────────────────
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

# Header with attention counter
pending_count = int(filtered["Current Stage"].isin(_PENDING_STAGES).sum()) if "Current Stage" in filtered.columns else 0
hc1, hc2 = st.columns([3, 1])
hc1.markdown(f"**{len(filtered)} lead(s)**")
if pending_count:
    hc2.markdown(
        f'<p style="color:#c0392b;font-weight:700;text-align:right;margin:0;">'
        f'⚠️ {pending_count} need attention</p>',
        unsafe_allow_html=True,
    )

if filtered.empty:
    st.info("No leads match the current filters.")
    st.stop()

# ── Lead cards ────────────────────────────────────────────────────────────────
for idx, row in filtered.iterrows():
    stage      = str(row.get("Current Stage", ""))
    is_pending = stage in _PENDING_STAGES
    company    = str(row.get("Company Name", "Unknown"))
    exhibition = str(row.get("Exhibition", ""))

    is_active = stage in _ACTIVE_STAGES
    dot = "🔴" if is_pending else ("🟢" if is_active else ("✅" if stage == "Won" else ("❌" if stage == "Lost" else "▪️")))

    with st.expander(f"{dot}  {company}  —  {exhibition}  ·  {stage}"):

        # ── Quick stage update bar ────────────────────────────────────────────
        with st.form(f"quick_{idx}"):
            qc1, qc2, qc3 = st.columns([4, 2, 1])
            with qc1:
                q_stage = st.selectbox(
                    "Stage", PIPELINE_STAGES,
                    index=PIPELINE_STAGES.index(stage) if stage in PIPELINE_STAGES else 0,
                    label_visibility="collapsed",
                )
            with qc2:
                q_user = st.selectbox("By", USERS, label_visibility="collapsed")
            with qc3:
                q_save = st.form_submit_button("✓ Update", use_container_width=True, type="primary")
            if q_save:
                update_lead_field(idx + 1, "Current Stage", q_stage, q_user)
                log_stage_change(company, q_stage, q_user, "")
                st.rerun()

        st.markdown(_stage_pill(stage), unsafe_allow_html=True)
        st.write("")

        col_left, col_right = st.columns([3, 2])

        # ── Left: lead info ──────────────────────────────────────────────────
        with col_left:
            src          = row.get("Source", "")
            date_added   = row.get("Date Added", "")
            last_updated = row.get("Last Updated By", "")
            st.caption(f"📋 {src}  ·  Added {date_added}  ·  Updated by {last_updated}")

            phone = str(row.get("Contact Phone", "") or "")
            email = str(row.get("Contact Email", "") or "")
            name  = str(row.get("Contact Name",  "") or "")
            parts = [p for p in [name, email, phone] if p]
            st.markdown(f"**Contact:** {'  ·  '.join(parts) if parts else '—'}")

            try:
                design_count = int(row.get("Design Options Sent", 0) or 0)
            except (ValueError, TypeError):
                design_count = 0
            design_icons = " ".join(["✅" if i < design_count else "⬜" for i in range(3)])
            st.markdown(f"**Design Options Sent:** {design_icons}")

            vendor_q = row.get("Vendor Quote (AED)", "")
            margin   = row.get("Margin (AED)", "")
            client_q = row.get("Client Quote (AED)", "")
            discount = row.get("Discount Given", "No")

            if any([vendor_q, margin, client_q]):
                st.markdown("---")
                if is_admin():
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Vendor Quote",  f"AED {vendor_q}" if vendor_q else "—")
                    m2.metric("Margin",        f"AED {margin}"   if margin   else "—")
                    m3.metric("Client Quote",  f"AED {client_q}" if client_q else "—")
                else:
                    st.metric("Client Quote", f"AED {client_q}" if client_q else "—")
                if discount == "Yes":
                    st.caption("🏷️ Discount applied")

        # ── Right: update form ───────────────────────────────────────────────
        with col_right:
            with st.container(border=True):
                with st.form(f"form_{idx}"):
                    st.markdown("##### Update Lead")

                    new_stage = st.selectbox(
                        "Stage",
                        PIPELINE_STAGES,
                        index=PIPELINE_STAGES.index(stage) if stage in PIPELINE_STAGES else 0,
                    )
                    updated_by = st.selectbox("Updated by", USERS)

                    st.divider()

                    fc1, fc2 = st.columns(2)
                    with fc1:
                        brief_ver = st.selectbox(
                            "Brief v.",
                            [1, 2, 3],
                            index=max(0, int(row.get("Brief Version", 1) or 1) - 1),
                        )
                    with fc2:
                        design_opts = st.selectbox(
                            "Designs sent",
                            [0, 1, 2, 3],
                            index=min(3, max(0, int(row.get("Design Options Sent", 0) or 0))),
                        )

                    show_quote = any(k in new_stage for k in ["Vendor", "Quotation", "Quote", "Discount"])
                    new_vendor_q = str(vendor_q)
                    new_margin   = str(margin)
                    if show_quote:
                        st.divider()
                        st.caption("Quotation")
                        if is_admin():
                            new_vendor_q = st.text_input("Vendor Quote (AED)", value=str(vendor_q))
                            new_margin   = st.text_input("Margin (AED)",       value=str(margin))
                        new_client_q = st.text_input("Client Quote (AED)", value=str(client_q))
                        new_discount = st.selectbox("Discount Given", ["No", "Yes"],
                                                    index=0 if discount != "Yes" else 1)
                    else:
                        new_client_q = str(client_q)
                        new_discount = str(discount)

                    new_phone = st.text_input("Contact Phone", value=phone)
                    new_notes = st.text_area("Notes", value=str(row.get("Notes", "")), height=80)

                    if st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary"):
                        row_number = idx + 1
                        update_lead_field(row_number, "Current Stage",       new_stage,    updated_by)
                        update_lead_field(row_number, "Brief Version",       brief_ver,    updated_by)
                        update_lead_field(row_number, "Design Options Sent", design_opts,  updated_by)
                        update_lead_field(row_number, "Contact Phone",       new_phone,    updated_by)
                        update_lead_field(row_number, "Notes",               new_notes,    updated_by)
                        if show_quote:
                            update_lead_field(row_number, "Vendor Quote (AED)", new_vendor_q, updated_by)
                            update_lead_field(row_number, "Margin (AED)",        new_margin,   updated_by)
                            update_lead_field(row_number, "Client Quote (AED)", new_client_q, updated_by)
                            update_lead_field(row_number, "Discount Given",     new_discount, updated_by)
                        log_stage_change(company, new_stage, updated_by, new_notes)
                        st.success("Saved!")
                        st.rerun()

        # ── Add to Follow-up ─────────────────────────────────────────────────
        st.markdown("---")
        with st.expander("📅 Add to Follow-up"):
            with st.form(f"followup_{idx}"):
                fa, fb, fc_col = st.columns([2, 2, 3])
                with fa:
                    fu_date = st.date_input("Follow-up Date", value=date.today(),
                                            key=f"fu_date_{idx}")
                with fb:
                    fu_user = st.selectbox("Assign To", USERS, key=f"fu_user_{idx}")
                with fc_col:
                    fu_notes = st.text_input("Notes", placeholder="e.g. Follow up on quotation",
                                             key=f"fu_notes_{idx}")
                if st.form_submit_button("📅 Save Follow-up", type="primary"):
                    ok = add_followup({
                        "company_name":  company,
                        "exhibition":    exhibition,
                        "stage_at_time": stage,
                        "followup_date": fu_date.strftime("%d-%b-%Y"),
                        "assigned_to":   fu_user,
                        "notes":         fu_notes,
                        "created_by":    fu_user,
                    })
                    if ok:
                        st.success(f"✅ Follow-up set for {fu_date.strftime('%d %b %Y')} — will appear in Tasks when due.")
                        get_due_count.clear()
                    else:
                        st.error("Could not save. Check Google Sheets connection.")

        # ── Stage history (collapsed by default) ─────────────────────────────
        st.markdown("---")
        with st.expander("📋 Stage History", expanded=False):
            history = get_stage_history(company)
            if not history.empty:
                display_cols = [c for c in ["Stage", "Updated By", "Date/Time", "Notes"] if c in history.columns]
                st.dataframe(history[display_cols].reset_index(drop=True),
                             use_container_width=True, hide_index=True)
            else:
                st.caption("No history logged yet.")
