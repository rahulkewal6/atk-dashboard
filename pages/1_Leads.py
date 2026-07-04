import streamlit as st
import pandas as pd
from datetime import date, time
from utils.sheets import (
    get_pipeline_df, add_lead, update_lead_field, delete_lead,
    log_stage_change, get_stage_history, add_followup, get_due_count,
)
from utils.constants import PIPELINE_STAGES, STAGE_TIERS, TIER_STYLE, EXHIBITIONS, SOURCES, USERS
from utils.branding import inject_css, show_logo
from utils.ui import time_select, greeting_header, pipeline_bars
from utils.timeutil import time_with_ist
from utils.auth import require_login, show_user_bar, is_admin, can_modify, get_display_name
from utils.notify import notify_followup_assigned

inject_css()
require_login()
show_logo()
show_user_bar()


def _tier(stage: str) -> str:
    return STAGE_TIERS.get(stage, "red")


def _initials(company: str) -> str:
    words = [w for w in str(company).split() if w]
    return (words[0][0] + (words[1][0] if len(words) > 1 else "")).upper() if words else "?"


def _lead_row(lead_no, company, exhibition, source, stage, value, added="") -> str:
    """Compact reference-style lead row: # · avatar · name/meta · pill · value."""
    s = TIER_STYLE[_tier(stage)]
    added_txt = f"Added {added}" if str(added).strip() else ""
    meta = "  ·  ".join([m for m in [exhibition, source, added_txt] if m])
    value_html = (
        f'<span style="font-size:0.8rem;color:#374151;font-variant-numeric:tabular-nums;'
        f'white-space:nowrap;">AED {value}</span>' if str(value).strip() else ""
    )
    return (
        f'<div style="display:flex;align-items:center;gap:12px;padding:2px 0;">'
        f'<span style="color:#9AA0A6;font-size:0.72rem;min-width:24px;">#{lead_no}</span>'
        f'<span style="width:34px;height:34px;border-radius:9px;background:{s["bg"]};color:{s["color"]};'
        f'display:flex;align-items:center;justify-content:center;font-size:0.78rem;font-weight:700;'
        f'flex:none;">{_initials(company)}</span>'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-size:0.93rem;font-weight:600;color:#16181D;">{company}</div>'
        f'<div style="font-size:0.74rem;color:#8A8F98;">{meta}</div></div>'
        f'<span class="atk-pill" style="background:{s["bg"]};color:{s["color"]};'
        f'border:1px solid {s["color"]}40;">● {s["label"]}</span>'
        f'{value_html}'
        f'</div>'
    )


# ── Header: greeting + insight ────────────────────────────────────────────────
_df_head = get_pipeline_df()
_action_n = 0
if not _df_head.empty and "Current Stage" in _df_head.columns:
    _action_n = int((_df_head["Current Stage"].map(lambda s: _tier(str(s))) == "red").sum())
_due = get_due_count()
_insight = f'<b style="color:#D14D00;">{_action_n} lead(s) need your action</b>'
if _due:
    _insight += f' — {_due} follow-up{"s" if _due > 1 else ""} due'
greeting_header(get_display_name() or "there", _insight)

if _due:
    st.sidebar.error(f"🔔 {_due} follow-up{'s' if _due > 1 else ''} due — check Tasks")

# ── Add New Lead ──────────────────────────────────────────────────────────────
with st.expander("➕ Add New Lead"):
    with st.form("add_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            company       = st.text_input("Company Name *")
            exhibition    = st.selectbox("Exhibition *", EXHIBITIONS)
            stand_size    = st.text_input("Stand Size", placeholder="e.g. 10x10")
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
                    "stand_size": stand_size,
                    "source": actual_source, "contact_email": contact_email,
                    "contact_name": contact_name, "contact_phone": contact_phone,
                    "current_stage": default_stage, "notes": notes,
                    "added_by": added_by, "updated_by": added_by,
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

# ── Pipeline by stage (reference-style bars) ──────────────────────────────────
_CARD_TIERS = ["red", "design_prog", "quote_prog", "design_client", "quote_client", "won"]
if "Current Stage" in df.columns:
    tiers = df["Current Stage"].map(lambda s: _tier(str(s)))
    counts = {t: int((tiers == t).sum()) for t in _CARD_TIERS}
    pipeline_bars(counts, TIER_STYLE)

# ── Filter chips ──────────────────────────────────────────────────────────────
_TIER_LABELS = {t: TIER_STYLE[t]["label"] for t in _CARD_TIERS + ["lost"]}
chip = st.pills(
    "Filter", ["All"] + [_TIER_LABELS[t] for t in _CARD_TIERS + ["lost"]],
    selection_mode="single", default="All", label_visibility="collapsed",
)
_LABEL_TO_TIER = {v: k for k, v in _TIER_LABELS.items()}

with st.expander("More filters"):
    c2, c3, c4 = st.columns(3)
    with c2:
        filter_exhibition = st.multiselect("Exhibition", ["All"] + EXHIBITIONS, default=["All"])
    with c3:
        filter_source = st.multiselect("Source", ["All"] + SOURCES, default=["All"])
    with c4:
        filter_stage = st.multiselect("Stage", ["All"] + PIPELINE_STAGES, default=["All"])

filtered = df.copy()
if chip and chip != "All" and "Current Stage" in filtered.columns:
    want = _LABEL_TO_TIER[chip]
    filtered = filtered[filtered["Current Stage"].map(lambda s: _tier(str(s))) == want]
if "All" not in filter_exhibition and "Exhibition" in filtered.columns:
    filtered = filtered[filtered["Exhibition"].isin(filter_exhibition)]
if "All" not in filter_source and "Source" in filtered.columns:
    filtered = filtered[filtered["Source"].isin(filter_source)]
if "All" not in filter_stage and "Current Stage" in filtered.columns:
    filtered = filtered[filtered["Current Stage"].isin(filter_stage)]

st.caption(f"{len(filtered)} lead(s)")

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

    with st.container(border=True, key=f"lead_{idx}"):

        # ── Header row: compact lead row + inline stage updater + ⋮ menu ─────
        # Owner = whoever added the lead (older rows fall back to last updater)
        owner = str(row.get("Added By", "") or row.get("Last Updated By", ""))
        hl, hr, hm = st.columns([5, 1.4, 0.7])
        with hl:
            st.markdown(
                _lead_row(idx + 1, company, exhibition,
                          str(row.get("Source", "") or ""), stage,
                          str(row.get("Client Quote (AED)", "") or ""),
                          added=str(row.get("Date Added", "") or "")),
                unsafe_allow_html=True,
            )
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
        with hm:
            with st.popover("⋮", use_container_width=True):
                if st.button("📐 Send Design Brief", key=f"brief_{idx}", use_container_width=True):
                    st.session_state["brief_prefill"] = {
                        "company": company, "exhibition": exhibition,
                        "size": str(row.get("Stand Size", "") or ""), "row_number": idx + 1,
                    }
                    st.switch_page("pages/10_Design_Brief.py")
                st.divider()
                if can_modify(owner):
                    st.caption("Edit all fields in the **Details** section below.")
                    st.divider()
                    if not st.session_state.get(f"confirm_dellead_{idx}"):
                        if st.button("🗑 Delete lead", key=f"dellead_{idx}", use_container_width=True):
                            st.session_state[f"confirm_dellead_{idx}"] = True
                            st.rerun()
                    else:
                        st.warning(f"Permanently delete **{company}**?")
                        if st.button("Yes, delete", key=f"yesdellead_{idx}", type="primary", use_container_width=True):
                            if delete_lead(idx + 1, company):
                                st.session_state.pop(f"confirm_dellead_{idx}", None)
                                st.rerun()
                            else:
                                st.error("Delete failed — refresh and try again.")
                        if st.button("Cancel", key=f"nodellead_{idx}", use_container_width=True):
                            st.session_state.pop(f"confirm_dellead_{idx}", None)
                            st.rerun()
                else:
                    st.caption(f"Only {owner or 'the owner'} or an admin can delete this lead.")

        # ── Details ───────────────────────────────────────────────────────────
        with st.expander("Details, follow-up & history"):

            col_left, col_right = st.columns([3, 2])

            with col_left:
                src          = row.get("Source", "")
                date_added   = row.get("Date Added", "")
                last_updated = row.get("Last Updated By", "")
                added_by_val = row.get("Added By", "")
                _added = f"Added {date_added}" + (f" by {added_by_val}" if added_by_val else "")
                st.caption(f"📋 {src}  ·  {_added}  ·  Updated by {last_updated}")

                phone = str(row.get("Contact Phone", "") or "")
                email = str(row.get("Contact Email", "") or "")
                name  = str(row.get("Contact Name",  "") or "")
                parts = [p for p in [name, email, phone] if p]
                st.markdown(f"**Contact:** {'  ·  '.join(parts) if parts else '—'}")

                stand_sz = str(row.get("Stand Size", "") or "")
                if stand_sz:
                    st.markdown(f"**Stand Size:** {stand_sz}")

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
                    fa, fb, fc = st.columns(3)
                    with fa:
                        fu_date = st.date_input("Follow-up Date", value=date.today(),
                                                key=f"fu_date_{idx}")
                    with fb:
                        fu_time = time_select("Time (UAE)", default="10:00 AM",
                                              key=f"fu_time_{idx}")
                    with fc:
                        fu_user = st.selectbox("Assign To", USERS, key=f"fu_user_{idx}")
                    fu_notes = st.text_input("Notes", placeholder="e.g. Follow up on quotation",
                                             key=f"fu_notes_{idx}")
                    if st.form_submit_button("Save Follow-up", type="primary"):
                        fu_date_str = fu_date.strftime("%d-%b-%Y")
                        fu_time_str = fu_time
                        ok = add_followup({
                            "company_name":  company,
                            "exhibition":    exhibition,
                            "stage_at_time": stage,
                            "followup_date": fu_date_str,
                            "followup_time": fu_time_str,
                            "assigned_to":   fu_user,
                            "notes":         fu_notes,
                            "created_by":    get_display_name(),
                        })
                        if ok:
                            notify_followup_assigned(
                                assigned_to=fu_user, assigned_by=get_display_name(),
                                company=company, exhibition=exhibition,
                                fu_date=f"{fu_date_str} · {time_with_ist(fu_time_str)}",
                                notes=fu_notes,
                                contact_name=str(row.get("Contact Name", "") or ""),
                                contact_phone=str(row.get("Contact Phone", "") or ""),
                                contact_email=str(row.get("Contact Email", "") or ""),
                            )
                            st.success(f"✅ Follow-up set for {fu_date.strftime('%d %b %Y')} {fu_time_str} — will appear in Tasks when due.")
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

            # ── Stage history ─────────────────────────────────────────────────
            st.markdown("---")
            history = get_stage_history(company)
            if not history.empty:
                display_cols = [c for c in ["Stage", "Updated By", "Date/Time", "Notes"] if c in history.columns]
                st.dataframe(history[display_cols].reset_index(drop=True),
                             use_container_width=True, hide_index=True)
            else:
                st.caption("No stage history logged yet.")
