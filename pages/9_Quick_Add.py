import streamlit as st
from datetime import date
from utils.sheets import (
    get_pipeline_df, add_lead, update_lead_field, log_stage_change,
)
from utils.constants import EXHIBITIONS, SOURCES, USERS, PIPELINE_STAGES
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar, get_display_name
from utils import ai_intake

inject_css()
require_login()
show_logo()
show_user_bar()

st.title("✨ Quick Add")
st.caption("Speak it or screenshot it — the AI fills the lead for you. You just confirm.")

if st.session_state.pop("_qa_saved", None):
    st.success(st.session_state.pop("_qa_saved_msg", "✅ Saved."))

if not ai_intake.have_openai():
    st.warning("AI intake needs the OpenAI key. Add `OPENAI_API_KEY` to your Streamlit secrets to enable this page.")
    st.stop()


def _best_match(name, options):
    nl = str(name).lower().strip()
    if not options:
        return None
    if nl:
        for o in options:
            if str(o).lower().strip() == nl:
                return o
        for o in options:
            if nl in str(o).lower():
                return o
        for o in options:
            if str(o).lower() in nl:
                return o
    return options[0]


# ── Input card ────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("##### 1 · Give me the lead")
    ic1, ic2 = st.columns(2)
    with ic1:
        audio = st.audio_input("🎤 Record a voice note")
    with ic2:
        image = st.file_uploader("📸 Email screenshot", type=["png", "jpg", "jpeg", "webp"])
    extra = st.text_input("✏️ Or type / add extra detail (optional)",
                          placeholder="e.g. Company XYZ, 10x10, GITEX, brief received")

    if st.button("✨ Analyze", type="primary", use_container_width=True):
        with st.spinner("Reading your input…"):
            text = extra.strip()
            if audio is not None:
                t = ai_intake.transcribe(audio.getvalue())
                if t:
                    text = (text + "\n" + t).strip() if text else t
            img_bytes = image.getvalue() if image is not None else None
            img_mime = image.type if image is not None else "image/png"
            result = ai_intake.extract(text=text, image_bytes=img_bytes, image_mime=img_mime)
            result["_transcript"] = text
            st.session_state["qa_result"] = result
        st.rerun()

# ── Review & confirm ──────────────────────────────────────────────────────────
res = st.session_state.get("qa_result")
if res:
    st.markdown("##### 2 · Check & confirm")
    if res.get("_transcript"):
        st.caption(f"🗣️ Heard: _{res['_transcript']}_")

    intent_label = st.radio(
        "This is a…", ["➕ New lead", "🔄 Stage update"],
        index=0 if res.get("intent") != "stage_update" else 1,
        horizontal=True,
    )

    # ── NEW LEAD ──────────────────────────────────────────────────────────────
    if intent_label == "➕ New lead":
        with st.form("qa_new_lead"):
            c1, c2 = st.columns(2)
            with c1:
                company = st.text_input("Company Name *", value=res.get("company_name", ""))
                exh_default = res.get("exhibition") if res.get("exhibition") in EXHIBITIONS else "Other"
                exhibition = st.selectbox("Exhibition", EXHIBITIONS,
                                          index=EXHIBITIONS.index(exh_default))
                stand = st.text_input("Stand Size", value=res.get("stand_size", ""))
                stg_default = res.get("stage") if res.get("stage") in PIPELINE_STAGES else "Hot Lead (Inbound)"
                stage = st.selectbox("Stage", PIPELINE_STAGES,
                                     index=PIPELINE_STAGES.index(stg_default))
            with c2:
                contact_name  = st.text_input("Contact Name", value=res.get("contact_name", ""))
                contact_email = st.text_input("Contact Email", value=res.get("contact_email", ""))
                contact_phone = st.text_input("Contact Phone", value=res.get("contact_phone", ""))
                src_default = "Client Reached Out"
                source = st.selectbox("Source", SOURCES,
                                      index=SOURCES.index(src_default) if src_default in SOURCES else 0)
            notes = st.text_area("Notes", value=res.get("notes", ""))
            who = get_display_name()
            added_by = st.selectbox("Added by", USERS,
                                    index=USERS.index(who) if who in USERS else 0)

            sc1, sc2 = st.columns(2)
            save = sc1.form_submit_button("✅ Save lead", type="primary", use_container_width=True)
            discard = sc2.form_submit_button("Discard", use_container_width=True)
            if save:
                if not company.strip():
                    st.error("Company name is required.")
                else:
                    ok = add_lead({
                        "company_name": company.strip(), "exhibition": exhibition,
                        "stand_size": stand, "source": source,
                        "contact_email": contact_email, "contact_name": contact_name,
                        "contact_phone": contact_phone, "current_stage": stage,
                        "notes": notes, "added_by": added_by, "updated_by": added_by,
                    })
                    if ok:
                        log_stage_change(company.strip(), stage, added_by, "Added via Quick Add")
                        st.session_state.pop("qa_result", None)
                        st.session_state["_qa_saved"] = True
                        st.session_state["_qa_saved_msg"] = f"✅ Lead added: {company.strip()}"
                        st.rerun()
                    else:
                        st.error("Could not save. Check Google Sheets connection.")
            if discard:
                st.session_state.pop("qa_result", None)
                st.rerun()

    # ── STAGE UPDATE ──────────────────────────────────────────────────────────
    else:
        df = get_pipeline_df()
        if df.empty or "Company Name" not in df.columns:
            st.info("No existing leads to update yet.")
        else:
            companies = df["Company Name"].astype(str).tolist()
            match = _best_match(res.get("company_name", ""), companies)
            with st.form("qa_stage_update"):
                st.caption(f"AI heard company: **{res.get('company_name','—')}** → matched below. Fix if wrong.")
                pick = st.selectbox("Lead to update", companies,
                                    index=companies.index(match) if match in companies else 0)
                stg_default = res.get("stage") if res.get("stage") in PIPELINE_STAGES else "Brief Sent to Designer"
                new_stage = st.selectbox("New stage", PIPELINE_STAGES,
                                         index=PIPELINE_STAGES.index(stg_default))
                who = get_display_name()
                upd_by = st.selectbox("Updated by", USERS,
                                      index=USERS.index(who) if who in USERS else 0)
                note = st.text_input("Note (optional)", value=res.get("notes", ""))

                sc1, sc2 = st.columns(2)
                save = sc1.form_submit_button("✅ Update stage", type="primary", use_container_width=True)
                discard = sc2.form_submit_button("Discard", use_container_width=True)
                if save:
                    matches = df[df["Company Name"].astype(str) == pick]
                    if matches.empty:
                        st.error("Could not find that lead — please refresh.")
                    else:
                        row_idx = matches.index[0]
                        update_lead_field(row_idx + 1, "Current Stage", new_stage, upd_by)
                        log_stage_change(pick, new_stage, upd_by, note or "Updated via Quick Add")
                        st.session_state.pop("qa_result", None)
                        st.session_state["_qa_saved"] = True
                        st.session_state["_qa_saved_msg"] = f"✅ {pick} → {new_stage}"
                        st.rerun()
                if discard:
                    st.session_state.pop("qa_result", None)
                    st.rerun()
