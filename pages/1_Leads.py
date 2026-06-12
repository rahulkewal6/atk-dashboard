import streamlit as st
import pandas as pd
from datetime import date
from utils.sheets import (
    get_pipeline_df, add_lead, update_lead_field, delete_lead,
    log_stage_change, get_stage_history, add_followup, get_due_count,
)
from utils.constants import PIPELINE_STAGES, STAGE_TIERS, TIER_STYLE, EXHIBITIONS, SOURCES, USERS
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, is_admin

inject_css()
require_login()
show_logo()
show_user_bar()


def _tier(stage: str) -> str:
    return STAGE_TIERS.get(stage, "red")


def _pill(stage: str) -> str:
    s = TIER_STYLE[_tier(stage)]
    return (
        f'<span class="atk-pill" style="background:{s["bg"]};color:{s["color"]};'
        f'border:1px solid {s["color"]}55;">{stage}</span>'
    )


def _lead_header(lead_no: int, company: str, exhibition: str, stage: str) -> str:
    s = TIER_STYLE[_tier(stage)]
    return (
        f'<div class="atk-lead-head">'
        f'<span class="atk-num">#{lead_no}</span>'
        f'<span class="atk-dot" style="background:{s["color"]};box-shadow:0 0 8px {s["color"]}66;"></span>'
        f'<span class="atk-company">{company}</span>'
        f'<span class="atk-exh">{exhibition}</span>'
        f'{_pill(stage)}'
        f'</div>'
    )


st.title("Leads")
st.caption(
    "🔴 action needed from us · 🟡 design in progress · 🟠 quotation in progress · "
    "🟢 design with client · 🔵 quotation with client"
)

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

# ── Load data ─────────────────────────────────────────────────────────────────
df = get_pipeline_df()
if df.empty:
    st.info("No leads yet. Add your first lead above.")
    st.stop()

# ── Status summary strip (clickable — filters the list) ──────────────────────
_CARD_TIERS = ["red", "design_prog", "quote_prog", "design_client", "quote_client", "won"]
_CARD_TO_STATUS = {
    "red":           "🔴 Action needed",
    "design_prog":   "🟡 Design in progress",
    "quote_prog":    "🟠 Quotation in progress",
    "design_client": "🟢 Design with client",
    "quote_client":  "🔵 Quotation with client",
    "won":           "✅ Won",
}
_STATUS_OPTIONS = ["All"] + list(_CARD_TO_STATUS.values()) + ["❌ Lost"]
if "lead_status" not in st.session_state:
    st.session_state["lead_status"] = "All"

if "Current Stage" in df.columns:
    tiers = df["Current Stage"].map(lambda s: _tier(str(s)))
    counts = {t: int((tiers == t).sum()) for t in _CARD_TIERS}
    sc = st.columns(len(_CARD_TIERS))
    for col, t in zip(sc, _CARD_TIERS):
        status_label = _CARD_TO_STATUS[t]
        selected = st.session_state["lead_status"] == status_label
        with col:
            with st.container(key=f"stat_{t}"):
                if st.button(
                    f"{counts[t]}  ·  {TIER_STYLE[t]['label']}" + ("  ✕" if selected else ""),
                    key=f"statbtn_{t}",
                    use_container_width=True,
                    help="Click to show only these leads — click again to show all",
                ):
                    st.session_state["lead_status"] = "All" if selected else status_label
                    st.rerun()

# ── Filters ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    filter_status = st.selectbox("Status", _STATUS_OPTIONS, key="lead_status")
with c2:
    filter_exhibition = st.multiselect("Exhibition", ["All"] + EXHIBITIONS, default=["All"])
with c3:
    filter_source = st.multiselect("Source", ["All"] + SOURCES, default=["All"])
with c4:
    filter_stage = st.multiselect("Stage", ["All"] + PIPELINE_STAGES, default=["All"])

filtered = df.copy()
_STATUS_TO_TIER = {v: k for k, v in _CARD_TO_STATUS.items()}
_STATUS_TO_TIER["❌ Lost"] = "lost"
if filter_status != "All" and "Current Stage" in filtered.columns:
    want = _STATUS_TO_TIER[filter_status]
    filtered = filtered[filtered["Current Stage"].map(lambda s: _tier(str(s))) == want]
if "All" not in filter_exhibition and "Exhibition" in filtered.columns:
    filtered = filtered[filtered["Exhibition"].isin(filter_exhibition)]
if "All" not in filter_source and "Source" in filtered.columns:
    filtered = filtered[filtered["Source"].isin(filter_source)]
if "All" not in filter_stage and "Current Stage" in filtered.columns:
    filtered = filtered[filtered["Current Stage"].isin(filter_stage)]

# Header with attention counter
pending_count = 0
if "Current Stage" in filtered.columns:
    pending_count = int((filtered["Current Stage"].map(lambda s: _tier(str(s))) == "red").sum())
hc1, hc2 = st.columns([3, 1])
hc1.markdown(f"**{len(filtered)} lead(s)**")
if pending_count:
    hc2.markdown(
        f'<p style="color:#FF4D4F;font-weight:700;text-align:right;margin:0;">'
        f'{pending_count} need your action</p>',
        unsafe_allow_html=True,
    )

if filtered.empty:
    st.info("No leads match the current filters.")
    st.stop()

# Sort: action-needed first, then in-progress, then with-client
_TIER_ORDER = {"red": 0, "design_prog": 1, "quote_prog": 2,
               "design_client": 3, "quote_client": 4, "won": 5, "lost": 6}
if "Current Stage" in filtered.columns:
    filtered = filtered.copy()
    filtered["_tier_sort"] = filtered["Current Stage"].map(lambda s: _TIER_ORDER.get(_tier(str(s)), 1))
    filtered = filtered.sort_values("_tier_sort", kind="stable").drop(columns=["_tier_sort"])

# ── Lead cards ────────────────────────────────────────────────────────────────
for idx, row in filtered.iterrows():
    stage      = str(row.get("Current Stage", ""))
    company    = str(row.get("Company Name", "Unknown"))
    exhibition = str(row.get("Exhibition", ""))

    with st.container(border=True):

        # ── Header row: name + pill + inline stage updater ───────────────────
        hl, hr = st.columns([4, 1.3])
        with hl:
            st.markdown(_lead_header(idx + 1, company, exhibition, stage), unsafe_allow_html=True)
        with hr:
            with st.popover("✏️ Update stage", use_container_width=True):
                q_stage = st.selectbox(
                    "New stage", PIPELINE_STAGES,
                    index=PIPELINE_STAGES.index(stage) if stage in PIPELINE_STAGES else 0,
                    key=f"qstage_{idx}",
                )
                q_user = st.selectbox("Updated by", USERS, key=f"quser_{idx}")
                if st.button("✓ Save", key=f"qsave_{idx}", type="primary", use_container_width=True):
                    update_lead_field(idx + 1, "Current Stage", q_stage, q_user)
                    log_stage_change(company, q_stage, q_user, "")
                    st.rerun()

        # ── Details ───────────────────────────────────────────────────────────
        with st.expander("Details, follow-up & history"):

            col_left, col_right = st.columns([3, 2])

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

                # ── Add to Follow-up ──────────────────────────────────────────
                st.markdown("---")
                with st.form(f"followup_{idx}"):
                    st.markdown("**📅 Add to Follow-up**")
                    fa, fb = st.columns(2)
                    with fa:
                        fu_date = st.date_input("Follow-up Date", value=date.today(),
                                                key=f"fu_date_{idx}")
                    with fb:
                        fu_user = st.selectbox("Assign To", USERS, key=f"fu_user_{idx}")
                    fu_notes = st.text_input("Notes", placeholder="e.g. Follow up on quotation",
                                             key=f"fu_notes_{idx}")
                    if st.form_submit_button("Save Follow-up", type="primary"):
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

            # ── Right: full update form ───────────────────────────────────────
            with col_right:
                vendor_q = row.get("Vendor Quote (AED)", "")
                margin   = row.get("Margin (AED)", "")
                client_q = row.get("Client Quote (AED)", "")
                discount = row.get("Discount Given", "No")
                phone    = str(row.get("Contact Phone", "") or "")

                with st.form(f"form_{idx}"):
                    st.markdown("**Update Lead**")

                    new_stage = st.selectbox(
                        "Stage",
                        PIPELINE_STAGES,
                        index=PIPELINE_STAGES.index(stage) if stage in PIPELINE_STAGES else 0,
                    )
                    updated_by = st.selectbox("Updated by", USERS)

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

            # ── Stage history + delete ────────────────────────────────────────
            st.markdown("---")
            history = get_stage_history(company)
            hcol, dcol = st.columns([4, 1])
            with hcol:
                if not history.empty:
                    display_cols = [c for c in ["Stage", "Updated By", "Date/Time", "Notes"] if c in history.columns]
                    st.dataframe(history[display_cols].reset_index(drop=True),
                                 use_container_width=True, hide_index=True)
                else:
                    st.caption("No stage history logged yet.")
            with dcol:
                with st.popover("🗑 Delete", use_container_width=True):
                    st.warning(f"Permanently delete **{company}**? This cannot be undone.")
                    if st.button("Yes, delete this lead", key=f"del_{idx}", type="primary",
                                 use_container_width=True):
                        if delete_lead(idx + 1, company):
                            st.rerun()
                        else:
                            st.error("Delete failed — please refresh the page and try again.")
