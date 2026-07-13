import streamlit as st
import pandas as pd
from utils.sheets import (
    get_pipeline_df, add_lead, update_lead_field, delete_lead,
    log_stage_change, get_due_count,
)
from utils.constants import PIPELINE_STAGES, STAGE_TIERS, TIER_STYLE, EXHIBITIONS, SOURCES, USERS
from utils.branding import inject_css, show_logo
from utils.ui import greeting_header, pipeline_bars
from utils.auth import require_login, show_user_bar, can_modify, get_display_name
from utils.lead_detail import show_lead_dialog

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

# ── Add New Lead (dialog, opened from the header button) ─────────────────────
@st.dialog("➕ Add new lead", width="large")
def add_lead_dialog():
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
        if st.form_submit_button("Add Lead", type="primary", use_container_width=True):
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
                    st.session_state["_lead_added_msg"] = f"✅ Lead added: {company}"
                    st.rerun()
                else:
                    st.error("Could not save. Check Google Sheets connection.")


_msg = st.session_state.pop("_lead_added_msg", None)
if _msg:
    st.success(_msg)

# ── Header bar: search + New lead (reference style) ──────────────────────────
hs, hb = st.columns([4.2, 1.1])
with hs:
    search = st.text_input("Search", key="lead_search",
                           placeholder="🔍  Search leads, companies, contacts…",
                           label_visibility="collapsed")
with hb:
    if st.button("＋ New lead", type="primary", use_container_width=True):
        add_lead_dialog()

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

# ── Filter chips (by stage) ──────────────────────────────────────────────────
_TIER_LABELS = {t: TIER_STYLE[t]["label"] for t in _CARD_TIERS + ["lost"]}
chip = st.pills(
    "Filter", ["All"] + [_TIER_LABELS[t] for t in _CARD_TIERS + ["lost"]],
    selection_mode="single", default="All", label_visibility="collapsed",
)
_LABEL_TO_TIER = {v: k for k, v in _TIER_LABELS.items()}

# ── Exhibition view (click an event → see only its leads) ────────────────────
exh_pick = "All"
if "Exhibition" in df.columns:
    _exh_series = df["Exhibition"].astype(str).str.strip()
    _exh_counts = _exh_series[_exh_series.ne("") & _exh_series.str.lower().ne("nan")].value_counts()
    _exh_map = {f"{e}  ({n})": e for e, n in _exh_counts.items()}
    _exh_choice = st.pills(
        "Exhibition", ["🎪 All events"] + list(_exh_map.keys()),
        selection_mode="single", default="🎪 All events", label_visibility="collapsed",
    )
    if _exh_choice and _exh_choice != "🎪 All events":
        exh_pick = _exh_map.get(_exh_choice, "All")

with st.expander("More filters"):
    c3, c4 = st.columns(2)
    with c3:
        filter_source = st.multiselect("Source", ["All"] + SOURCES, default=["All"])
    with c4:
        filter_stage = st.multiselect("Stage", ["All"] + PIPELINE_STAGES, default=["All"])

filtered = df.copy()
if chip and chip != "All" and "Current Stage" in filtered.columns:
    want = _LABEL_TO_TIER[chip]
    filtered = filtered[filtered["Current Stage"].map(lambda s: _tier(str(s))) == want]
if exh_pick != "All" and "Exhibition" in filtered.columns:
    filtered = filtered[filtered["Exhibition"].astype(str).str.strip() == exh_pick]
if "All" not in filter_source and "Source" in filtered.columns:
    filtered = filtered[filtered["Source"].isin(filter_source)]
if "All" not in filter_stage and "Current Stage" in filtered.columns:
    filtered = filtered[filtered["Current Stage"].isin(filter_stage)]

# Live search across company, contact, email, phone, exhibition, source, notes
if search and search.strip():
    q = search.strip().lower()
    _search_cols = ["Company Name", "Contact Name", "Contact Email", "Contact Phone",
                    "Exhibition", "Source", "Notes"]
    mask = pd.Series(False, index=filtered.index)
    for c in _search_cols:
        if c in filtered.columns:
            mask |= filtered[c].astype(str).str.lower().str.contains(q, na=False, regex=False)
    filtered = filtered[mask]

# ── Count + sort control ─────────────────────────────────────────────────────
rc1, rc2 = st.columns([3, 1.5])
rc1.caption(f"{len(filtered)} lead(s)"
            + (f"  ·  {exh_pick}" if exh_pick != "All" else ""))
with rc2:
    sort_by = st.selectbox(
        "Sort", ["Needs action first", "Newest added", "Oldest added", "Value: high → low"],
        label_visibility="collapsed", key="lead_sort",
    )

if filtered.empty:
    st.info("No leads match the current filters.")
    st.stop()

filtered = filtered.copy()
if sort_by in ("Newest added", "Oldest added"):
    filtered["_d"] = pd.to_datetime(filtered.get("Date Added", ""),
                                    format="%d-%b-%Y", errors="coerce")
    filtered = filtered.sort_values(
        "_d", ascending=(sort_by == "Oldest added"), na_position="last"
    ).drop(columns=["_d"])
elif sort_by == "Value: high → low":
    filtered["_v"] = pd.to_numeric(filtered.get("Client Quote (AED)", ""), errors="coerce")
    filtered = filtered.sort_values("_v", ascending=False, na_position="last").drop(columns=["_v"])
else:
    _TIER_ORDER = {"red": 0, "design_prog": 1, "quote_prog": 2,
                   "design_client": 3, "quote_client": 4, "won": 5, "lost": 6}
    filtered["_t"] = filtered["Current Stage"].map(lambda s: _TIER_ORDER.get(_tier(str(s)), 1))
    filtered = filtered.sort_values("_t", kind="stable").drop(columns=["_t"])

# ── Lead cards ────────────────────────────────────────────────────────────────
for idx, row in filtered.iterrows():
    stage      = str(row.get("Current Stage", ""))
    company    = str(row.get("Company Name", "Unknown"))
    exhibition = str(row.get("Exhibition", ""))

    with st.container(border=True, key=f"lead_{idx}"):

        # ── Header row: compact lead row + View + inline stage updater + ⋮ menu ─
        # Owner = whoever added the lead (older rows fall back to last updater)
        owner = str(row.get("Added By", "") or row.get("Last Updated By", ""))
        hl, hv, hr, hm = st.columns([4.6, 1.0, 1.4, 0.7])
        with hl:
            st.markdown(
                _lead_row(idx + 1, company, exhibition,
                          str(row.get("Source", "") or ""), stage,
                          str(row.get("Client Quote (AED)", "") or ""),
                          added=str(row.get("Date Added", "") or "")),
                unsafe_allow_html=True,
            )
        with hv:
            if st.button("View →", key=f"viewlead_{idx}", use_container_width=True):
                show_lead_dialog(idx, row)
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
                    st.caption("Click **View →** for full edit, follow-up, task and history options.")
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
