"""The Design Brief composer — form + AI intake + live preview + send.
Shared by the standalone Design Brief page and (via prefill) the lead button."""
import streamlit as st
from datetime import date
from utils.constants import (
    LAYOUTS, MEETING_ROOMS, BRIEF_FEATURES,
    DESIGNER_EMAIL, BRIEF_CC, BRIEF_REPLY_TO,
)
from utils.design_brief import build_subject, build_brief_html
from utils.email_util import send_email_with_attachments, compress_image
from utils.ai_intake import have_openai, transcribe, extract_brief
from utils.sheets import update_lead_field, log_stage_change, add_design_brief
from utils.auth import get_display_name

_MAX_BYTES = 24 * 1024 * 1024  # keep under Gmail's 25 MB


def _init(prefill):
    marker = f"{prefill.get('company','')}|{prefill.get('row_number','')}"
    if st.session_state.get("brief_loaded_for") == marker:
        return
    st.session_state["brief_loaded_for"] = marker
    st.session_state["b_company"]    = prefill.get("company", "")
    st.session_state["b_exhibition"] = prefill.get("exhibition", "")
    st.session_state["b_size"]       = prefill.get("size", "")
    st.session_state["b_location"]   = ""
    st.session_state["b_layout"]     = LAYOUTS[0]
    st.session_state["b_direction"]  = ""
    st.session_state["b_colours"]    = ""
    st.session_state["b_meeting"]    = "None"
    st.session_state["b_av"]         = ""
    st.session_state["b_products"]   = ""
    st.session_state["b_notes"]      = ""
    st.session_state["b_deadline"]   = date.today()
    for f in BRIEF_FEATURES:
        st.session_state[f"b_feat_{f}"] = False


def _apply_ai(res):
    m = {"b_size": "size", "b_location": "location", "b_layout": "layout",
         "b_direction": "design_direction", "b_colours": "brand_colours",
         "b_meeting": "meeting_room", "b_av": "av", "b_products": "products",
         "b_notes": "notes"}
    for key, field in m.items():
        val = res.get(field, "")
        if val:
            st.session_state[key] = val
    for f in BRIEF_FEATURES:
        if f in (res.get("features") or []):
            st.session_state[f"b_feat_{f}"] = True


def _collect():
    dl = st.session_state.get("b_deadline")
    return {
        "company":          st.session_state.get("b_company", ""),
        "exhibition":       st.session_state.get("b_exhibition", ""),
        "size":             st.session_state.get("b_size", ""),
        "location":         st.session_state.get("b_location", ""),
        "layout":           st.session_state.get("b_layout", ""),
        "design_direction": st.session_state.get("b_direction", ""),
        "brand_colours":    st.session_state.get("b_colours", ""),
        "meeting_room":     st.session_state.get("b_meeting", ""),
        "features":         [f for f in BRIEF_FEATURES if st.session_state.get(f"b_feat_{f}")],
        "av":               st.session_state.get("b_av", ""),
        "products":         st.session_state.get("b_products", ""),
        "notes":            st.session_state.get("b_notes", ""),
        "deadline":         dl.strftime("%d %b %Y") if dl else "",
        "sender":           get_display_name(),
    }


def render_brief_composer(prefill):
    """prefill: {company, exhibition, size, row_number(optional)}"""
    _init(prefill)

    if st.session_state.pop("_brief_sent", None):
        st.success(st.session_state.pop("_brief_sent_msg", "✅ Brief sent."))

    # ── 1) Smart intake (paste / voice / screenshot) ─────────────────────────
    if have_openai():
        with st.expander("✨ Auto-fill from a client email, screenshot, or voice note"):
            paste = st.text_area("Paste the client's brief / your notes", key="b_paste",
                                 placeholder="Paste the client email text, or type quick notes…")
            ca, cb = st.columns(2)
            with ca:
                shot = st.file_uploader("📸 Screenshot of the email", type=["png", "jpg", "jpeg", "webp"],
                                        key="b_shot")
            with cb:
                voice = st.audio_input("🎤 Or dictate the brief", key="b_voice")
            if st.button("✨ Draft brief from this", use_container_width=True):
                with st.spinner("Reading…"):
                    text = (paste or "").strip()
                    if voice is not None:
                        t = transcribe(voice.getvalue())
                        text = (text + "\n" + t).strip() if text else t
                    img = shot.getvalue() if shot is not None else None
                    mime = shot.type if shot is not None else "image/png"
                    res = extract_brief(text=text, image_bytes=img, image_mime=mime)
                    _apply_ai(res)
                st.rerun()

    st.markdown("##### Brief details")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Client", key="b_company")
    with c2:
        st.text_input("Exhibition", key="b_exhibition")
    with c3:
        st.text_input("Stand size", key="b_size", placeholder="8m x 10m (80 sqm)")

    c4, c5 = st.columns(2)
    with c4:
        st.text_input("Location (hall / booth)", key="b_location", placeholder="Hall 2, Booth 230")
    with c5:
        st.selectbox("Layout", LAYOUTS, key="b_layout")

    st.text_input("Design direction", key="b_direction", placeholder="Modern, premium, backlit walls…")
    st.text_input("Brand colours", key="b_colours", placeholder="white, red, blue")

    st.selectbox("Meeting room", MEETING_ROOMS, key="b_meeting")
    st.markdown("**Features**")
    fcols = st.columns(3)
    for i, f in enumerate(BRIEF_FEATURES):
        with fcols[i % 3]:
            st.checkbox(f, key=f"b_feat_{f}")

    st.text_input("AV / digital", key="b_av", placeholder="LED back wall, 1 touchscreen…")
    st.text_input("Products to highlight", key="b_products")
    st.text_area("Notes", key="b_notes", height=70,
                 placeholder="e.g. client wants something different from last year")
    st.date_input("First concept needed by", key="b_deadline")

    # ── Attachments ──────────────────────────────────────────────────────────
    st.markdown("##### Attachments")
    files = st.file_uploader("Floor plan, logo, brand guidelines, reference images/PDFs — any type, multiple",
                             accept_multiple_files=True, key="b_files")
    files = files or []
    raw_total = sum(len(f.getvalue()) for f in files)
    if files:
        mb = raw_total / 1_000_000
        st.caption(f"📎 {len(files)} file(s) · {mb:.1f} MB "
                   + ("· large images will be auto-compressed on send" if mb > 20 else ""))
        if mb > 24:
            st.warning("Over ~24 MB — images will be compressed on send; if it's still too big, remove a file.")

    # ── Live preview ─────────────────────────────────────────────────────────
    st.markdown("##### 📧 Live preview — exactly what Imran will receive")
    data = _collect()
    att_names = [f.name for f in files]
    st.caption(f"To: {DESIGNER_EMAIL}  ·  Cc: {', '.join(BRIEF_CC)}  ·  Reply-to: {BRIEF_REPLY_TO}")
    st.caption(f"Subject: {build_subject(data)}")
    st.markdown(build_brief_html(data, attachment_names=att_names), unsafe_allow_html=True)

    st.write("")
    if st.button("📤 Send brief to Imran", type="primary", use_container_width=True):
        if not data["company"].strip():
            st.error("Client name is required.")
            return
        addr = str(st.secrets.get("GMAIL_ADDRESS", "")).strip()
        pwd  = str(st.secrets.get("GMAIL_APP_PASSWORD", "")).strip()
        if not (addr and pwd):
            st.error("Email isn't configured — add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to secrets.")
            return
        with st.spinner("Sending…"):
            attachments, total = [], 0
            for f in files:
                n, b, m = compress_image(f.name, f.getvalue())
                attachments.append((n, b, m))
                total += len(b)
            if total > _MAX_BYTES:
                st.error(f"Attachments are {total/1_000_000:.0f} MB even after compression — "
                         "remove a file or two (Gmail limit is 25 MB).")
                return
            ok = send_email_with_attachments(
                to_addrs=[DESIGNER_EMAIL], subject=build_subject(data),
                html_body=build_brief_html(data, attachment_names=att_names),
                from_addr=addr, app_password=pwd, attachments=attachments,
                cc_addrs=BRIEF_CC, reply_to=BRIEF_REPLY_TO, from_name="ATK Exhibitions",
            )
        if not ok:
            st.error("Could not send. Check the email settings and try again.")
            return

        # Record + flip the lead stage → Design Tracker
        sender = get_display_name()
        add_design_brief({**data, "attachments": ", ".join(att_names),
                          "sent_to": DESIGNER_EMAIL, "sent_by": sender})
        row = prefill.get("row_number")
        if row:
            update_lead_field(row, "Current Stage", "Brief Sent to Designer", sender)
            log_stage_change(data["company"], "Brief Sent to Designer", sender,
                             "Design brief sent to Imran via dashboard")
        # reset for next time
        for k in list(st.session_state.keys()):
            if k.startswith("b_"):
                st.session_state.pop(k, None)
        st.session_state.pop("brief_loaded_for", None)
        st.session_state["_brief_sent"] = True
        st.session_state["_brief_sent_msg"] = (
            f"✅ Brief sent to Imran for {data['company']}"
            + (" · lead moved to 'Brief Sent to Designer'" if row else "")
        )
        st.rerun()
