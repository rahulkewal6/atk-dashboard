"""Lead detail dialog — reference-style panel: header, contact info,
stage progress, and quick 'next actions' (Call, Email, Add to Follow-up, Add to Task)."""
import streamlit as st
from datetime import date
from utils.constants import (
    PIPELINE_STAGES, STAGE_TIERS, TIER_STYLE, USERS, TASK_PRIORITIES,
)
from utils.sheets import (
    update_lead_field, log_stage_change, add_followup, add_task,
    get_due_count, get_stage_history, delete_lead,
)
from utils.ui import time_select
from utils.timeutil import time_with_ist
from utils.auth import get_display_name, is_admin, can_modify
from utils.notify import notify_followup_assigned, notify_task_assigned

_FUNNEL = ["red", "design_prog", "quote_prog", "design_client", "quote_client", "won"]


def _tier(stage: str) -> str:
    return STAGE_TIERS.get(stage, "red")


def _initials(company: str) -> str:
    words = [w for w in str(company).split() if w]
    return (words[0][0] + (words[1][0] if len(words) > 1 else "")).upper() if words else "?"


def _stage_progress(stage: str):
    cur = _tier(stage)
    cur_i = _FUNNEL.index(cur) if cur in _FUNNEL else -1
    segs, labels = [], []
    for i, t in enumerate(_FUNNEL):
        s = TIER_STYLE[t]
        active = i <= cur_i
        color = s["color"] if active else "#E6E8EC"
        segs.append(f'<div style="flex:1;height:6px;border-radius:3px;background:{color};"></div>')
        lab_color = "#16181D" if i == cur_i else "#9AA0A6"
        lab_weight = "700" if i == cur_i else "500"
        labels.append(f'<span style="flex:1;text-align:center;font-size:0.68rem;'
                      f'color:{lab_color};font-weight:{lab_weight};">{s["label"]}</span>')
    st.markdown(
        f'<div style="display:flex;gap:4px;margin-bottom:4px;">{"".join(segs)}</div>'
        f'<div style="display:flex;gap:4px;">{"".join(labels)}</div>',
        unsafe_allow_html=True,
    )


@st.dialog("Lead details", width="large")
def show_lead_dialog(idx, row):
    company    = str(row.get("Company Name", "Unknown"))
    exhibition = str(row.get("Exhibition", "") or "")
    stage      = str(row.get("Current Stage", "") or "")
    phone      = str(row.get("Contact Phone", "") or "")
    email      = str(row.get("Contact Email", "") or "")
    cname      = str(row.get("Contact Name", "") or "")
    source     = str(row.get("Source", "") or "")
    added      = str(row.get("Date Added", "") or "")
    owner      = str(row.get("Added By", "") or row.get("Last Updated By", "") or "")
    value      = str(row.get("Client Quote (AED)", "") or "")
    stand_sz   = str(row.get("Stand Size", "") or "")
    s = TIER_STYLE[_tier(stage)]
    row_number = idx + 1

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:10px;">'
        f'<span style="width:52px;height:52px;border-radius:14px;background:{s["bg"]};color:{s["color"]};'
        f'display:flex;align-items:center;justify-content:center;font-size:1.05rem;font-weight:700;'
        f'flex:none;">{_initials(company)}</span>'
        f'<div style="min-width:0;">'
        f'<div style="font-size:1.1rem;font-weight:700;color:#16181D;">{company}</div>'
        f'<div style="font-size:0.8rem;color:#8A8F98;">{exhibition}'
        + (f' &middot; {stand_sz}' if stand_sz else '') + f' &middot; #{row_number}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span class="atk-pill" style="background:{s["bg"]};color:{s["color"]};'
        f'border:1px solid {s["color"]}40;">● {s["label"]}</span>'
        + (f'&nbsp;&nbsp;<span style="font-size:0.85rem;color:#374151;">💰 AED {value}</span>' if value else ""),
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Contact info (click the copy icon on any line) ───────────────────────
    st.caption("CONTACT INFO — hover a line and click 📋 to copy")
    if cname:
        st.markdown(f"👤 {cname}")
    if email:
        st.code(email, language=None)
    if phone:
        st.code(phone, language=None)
    if not (cname or email or phone):
        st.caption("No contact details on file yet.")
    added_line = f"{source or '—'}" + (f" · added {added}" if added else "") + (f" by {owner}" if owner else "")
    st.caption(added_line)

    st.markdown("---")

    # ── Stage progress ───────────────────────────────────────────────────────
    sp1, sp2 = st.columns([5, 1.4])
    with sp1:
        st.caption("CURRENT STAGE")
    with sp2:
        pass
    _stage_progress(stage)
    with st.popover("Change stage", use_container_width=True):
        new_stage = st.selectbox("New stage", PIPELINE_STAGES,
                                 index=PIPELINE_STAGES.index(stage) if stage in PIPELINE_STAGES else 0,
                                 key=f"dlg_stage_{idx}")
        who = st.selectbox("Updated by", USERS, key=f"dlg_stageuser_{idx}")
        if st.button("✓ Save", key=f"dlg_stagesave_{idx}", type="primary", use_container_width=True):
            update_lead_field(row_number, "Current Stage", new_stage, who)
            log_stage_change(company, new_stage, who, "")
            st.rerun()

    st.markdown("---")

    # ── Next actions ─────────────────────────────────────────────────────────
    st.caption("NEXT ACTIONS")
    na1, na2 = st.columns(2)
    with na1:
        if st.button("📅 Add to Follow-up", key=f"dlg_showfu_{idx}", use_container_width=True):
            st.session_state[f"dlg_fu_open_{idx}"] = True
    with na2:
        if st.button("📋 Add to Task", key=f"dlg_showtask_{idx}", use_container_width=True):
            st.session_state[f"dlg_task_open_{idx}"] = True

    if st.session_state.get(f"dlg_fu_open_{idx}"):
        with st.form(f"dlg_fu_form_{idx}"):
            st.markdown("**📅 New follow-up**")
            fa, fb, fc = st.columns(3)
            with fa:
                fu_date = st.date_input("Date", value=date.today(), key=f"dlg_fu_date_{idx}")
            with fb:
                fu_time = time_select("Time (UAE)", default="10:00 AM", key=f"dlg_fu_time_{idx}")
            with fc:
                fu_user = st.selectbox("Assign to", USERS, key=f"dlg_fu_user_{idx}")
            fu_notes = st.text_input("Notes", key=f"dlg_fu_notes_{idx}",
                                     placeholder="e.g. Follow up on quotation")
            sc1, sc2 = st.columns(2)
            save = sc1.form_submit_button("Save", type="primary", use_container_width=True)
            cancel = sc2.form_submit_button("Cancel", use_container_width=True)
            if save:
                fu_date_str = fu_date.strftime("%d-%b-%Y")
                ok = add_followup({
                    "company_name": company, "exhibition": exhibition,
                    "stage_at_time": stage, "followup_date": fu_date_str,
                    "followup_time": fu_time, "assigned_to": fu_user,
                    "notes": fu_notes, "created_by": get_display_name(),
                })
                if ok:
                    notify_followup_assigned(
                        assigned_to=fu_user, assigned_by=get_display_name(),
                        company=company, exhibition=exhibition,
                        fu_date=f"{fu_date_str} · {time_with_ist(fu_time)}", notes=fu_notes,
                        contact_name=cname, contact_phone=phone, contact_email=email,
                    )
                    get_due_count.clear()
                    st.session_state.pop(f"dlg_fu_open_{idx}", None)
                    st.success("✅ Follow-up saved.")
                    st.rerun()
                else:
                    st.error("Could not save. Check Google Sheets connection.")
            if cancel:
                st.session_state.pop(f"dlg_fu_open_{idx}", None)
                st.rerun()

    if st.session_state.get(f"dlg_task_open_{idx}"):
        with st.form(f"dlg_task_form_{idx}"):
            st.markdown("**📋 New task**")
            t_title = st.text_input("Task", key=f"dlg_task_title_{idx}",
                                    placeholder=f"e.g. Prepare quotation for {company}")
            ta, tb, tc = st.columns(3)
            with ta:
                t_user = st.selectbox("Assign to", USERS, key=f"dlg_task_user_{idx}")
            with tb:
                t_prio = st.selectbox("Priority", TASK_PRIORITIES, key=f"dlg_task_prio_{idx}")
            with tc:
                t_date = st.date_input("Due date", value=date.today(), key=f"dlg_task_date_{idx}")
            t_time = time_select("Due time (UAE)", default="6:00 PM", key=f"dlg_task_time_{idx}")
            t_notes = st.text_input("Notes", key=f"dlg_task_notes_{idx}")
            sc1, sc2 = st.columns(2)
            save = sc1.form_submit_button("Save", type="primary", use_container_width=True)
            cancel = sc2.form_submit_button("Cancel", use_container_width=True)
            if save:
                if not t_title.strip():
                    st.error("Task title is required.")
                else:
                    due_str = t_date.strftime("%d-%b-%Y")
                    ok = add_task({
                        "title": t_title.strip(), "assigned_to": t_user, "priority": t_prio,
                        "due_date": due_str, "due_time": t_time, "notes": t_notes,
                        "created_by": get_display_name(), "source": "Leads",
                        "source_company": company,
                    })
                    if ok:
                        notify_task_assigned(t_title.strip(), t_user, get_display_name(), t_prio,
                                             f"{due_str} · {time_with_ist(t_time)}", t_notes)
                        st.session_state.pop(f"dlg_task_open_{idx}", None)
                        st.success("✅ Task saved.")
                        st.rerun()
                    else:
                        st.error("Could not save. Check Google Sheets connection.")
            if cancel:
                st.session_state.pop(f"dlg_task_open_{idx}", None)
                st.rerun()

    # ── More: full edit, history, delete ────────────────────────────────────
    with st.expander("More — full edit, history, delete"):
        vendor_q = row.get("Vendor Quote (AED)", "")
        margin   = row.get("Margin (AED)", "")
        client_q = row.get("Client Quote (AED)", "")
        discount = row.get("Discount Given", "No")

        with st.form(f"dlg_edit_{idx}"):
            st.markdown("**Update lead**")
            e_stage = st.selectbox("Stage", PIPELINE_STAGES,
                                   index=PIPELINE_STAGES.index(stage) if stage in PIPELINE_STAGES else 0,
                                   key=f"dlg_estage_{idx}")
            e_by = st.selectbox("Updated by", USERS, key=f"dlg_eby_{idx}")
            ec1, ec2 = st.columns(2)
            with ec1:
                brief_ver = st.selectbox("Brief v.", [1, 2, 3],
                                         index=max(0, int(row.get("Brief Version", 1) or 1) - 1),
                                         key=f"dlg_briefver_{idx}")
            with ec2:
                design_opts = st.selectbox("Designs sent", [0, 1, 2, 3],
                                           index=min(3, max(0, int(row.get("Design Options Sent", 0) or 0))),
                                           key=f"dlg_designopts_{idx}")
            show_quote = any(k in e_stage for k in ["Vendor", "Quotation", "Quote", "Discount"])
            new_vendor_q, new_margin = str(vendor_q), str(margin)
            if show_quote:
                st.caption("Quotation")
                if is_admin():
                    new_vendor_q = st.text_input("Vendor Quote (AED)", value=str(vendor_q), key=f"dlg_vq_{idx}")
                    new_margin   = st.text_input("Margin (AED)", value=str(margin), key=f"dlg_mg_{idx}")
                new_client_q = st.text_input("Client Quote (AED)", value=str(client_q), key=f"dlg_cq_{idx}")
                new_discount = st.selectbox("Discount Given", ["No", "Yes"],
                                            index=0 if discount != "Yes" else 1, key=f"dlg_disc_{idx}")
            else:
                new_client_q, new_discount = str(client_q), str(discount)
            new_phone = st.text_input("Contact Phone", value=phone, key=f"dlg_phone_{idx}")
            new_notes = st.text_area("Notes", value=str(row.get("Notes", "")), height=80, key=f"dlg_notes_{idx}")

            if st.form_submit_button("💾 Save changes", type="primary", use_container_width=True):
                update_lead_field(row_number, "Current Stage", e_stage, e_by)
                update_lead_field(row_number, "Brief Version", brief_ver, e_by)
                update_lead_field(row_number, "Design Options Sent", design_opts, e_by)
                update_lead_field(row_number, "Contact Phone", new_phone, e_by)
                update_lead_field(row_number, "Notes", new_notes, e_by)
                if show_quote:
                    update_lead_field(row_number, "Vendor Quote (AED)", new_vendor_q, e_by)
                    update_lead_field(row_number, "Margin (AED)", new_margin, e_by)
                    update_lead_field(row_number, "Client Quote (AED)", new_client_q, e_by)
                    update_lead_field(row_number, "Discount Given", new_discount, e_by)
                log_stage_change(company, e_stage, e_by, new_notes)
                st.success("Saved!")
                st.rerun()

        st.markdown("---")
        history = get_stage_history(company)
        if not history.empty:
            cols = [c for c in ["Stage", "Updated By", "Date/Time", "Notes"] if c in history.columns]
            st.dataframe(history[cols].reset_index(drop=True), use_container_width=True, hide_index=True)
        else:
            st.caption("No stage history logged yet.")

        st.markdown("---")
        if can_modify(owner):
            if not st.session_state.get(f"dlg_confirmdel_{idx}"):
                if st.button("🗑 Delete lead", key=f"dlg_del_{idx}", use_container_width=True):
                    st.session_state[f"dlg_confirmdel_{idx}"] = True
                    st.rerun()
            else:
                st.warning(f"Permanently delete **{company}**?")
                dc1, dc2 = st.columns(2)
                if dc1.button("Yes, delete", key=f"dlg_yesdel_{idx}", type="primary", use_container_width=True):
                    if delete_lead(row_number, company):
                        st.session_state.pop(f"dlg_confirmdel_{idx}", None)
                        st.rerun()
                    else:
                        st.error("Delete failed — refresh and try again.")
                if dc2.button("Cancel", key=f"dlg_nodel_{idx}", use_container_width=True):
                    st.session_state.pop(f"dlg_confirmdel_{idx}", None)
                    st.rerun()
        else:
            st.caption(f"Only {owner or 'the owner'} or an admin can delete this lead.")
