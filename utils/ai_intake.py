"""
AI lead intake — turn a voice note or an email screenshot into structured lead
data, using OpenAI (the same key as List Maker).

Everything here is best-effort and returns safe defaults on any failure, so the
Quick Add page never crashes if the AI is unavailable.
"""
import io
import json
import base64
import streamlit as st
from utils.constants import EXHIBITIONS, PIPELINE_STAGES, LAYOUTS, MEETING_ROOMS, BRIEF_FEATURES


def have_openai():
    key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    return key.startswith("sk-")


def _client():
    key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    if not key.startswith("sk-"):
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None


def transcribe(audio_bytes, filename="note.wav"):
    """Voice note → text via Whisper."""
    client = _client()
    if not client or not audio_bytes:
        return ""
    try:
        f = io.BytesIO(audio_bytes)
        f.name = filename
        resp = client.audio.transcriptions.create(model="whisper-1", file=f)
        return (resp.text or "").strip()
    except Exception:
        return ""


_SYSTEM = (
    "You are an assistant for a UAE exhibition stand-design company (ATK). "
    "You read a short voice transcript and/or an email screenshot about a sales lead, "
    "and return STRICT JSON describing it. Never invent details that aren't present."
)


def _build_prompt():
    return (
        "Extract the lead details and return ONLY a JSON object with these keys:\n"
        '{\n'
        '  "intent": "new_lead" or "stage_update",\n'
        '  "company_name": string,\n'
        '  "exhibition": one of ' + json.dumps(EXHIBITIONS) + ' (closest match, else "Other"),\n'
        '  "stand_size": string (e.g. "10x10"),\n'
        '  "stage": one of ' + json.dumps(PIPELINE_STAGES) + ' (closest match, else ""),\n'
        '  "contact_name": string,\n'
        '  "contact_email": string,\n'
        '  "contact_phone": string,\n'
        '  "notes": string\n'
        '}\n'
        'Rules: Use "stage_update" intent ONLY when the message is about changing an existing '
        'lead\'s stage (e.g. "X brief sent to designer"). Otherwise use "new_lead". '
        'Map spoken stages to the closest allowed value (e.g. "brief received" -> "Brief Received (v1)", '
        '"brief sent to designer" -> "Brief Sent to Designer"). '
        'Leave any unknown field as an empty string. Return JSON only, no prose.'
    )


def _empty():
    return {
        "intent": "new_lead", "company_name": "", "exhibition": "", "stand_size": "",
        "stage": "", "contact_name": "", "contact_email": "", "contact_phone": "", "notes": "",
    }


def extract(text="", image_bytes=None, image_mime="image/png"):
    """
    Send transcript text and/or an image to the model and return a normalized dict.
    """
    client = _client()
    if not client:
        return _empty()

    user_content = [{"type": "text", "text": _build_prompt()}]
    if text:
        user_content.append({"type": "text", "text": f"Voice transcript / notes:\n{text}"})
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{image_mime};base64,{b64}"},
        })

    # Model is configurable via secrets — default to the cheap, fast, vision-capable one.
    # Set OPENAI_LEAD_MODEL = "gpt-4o" (or another) in secrets to upgrade, no code change.
    model = str(st.secrets.get("OPENAI_LEAD_MODEL", "gpt-4o-mini")).strip() or "gpt-4o-mini"
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception:
        return _empty()

    out = _empty()
    for k in out:
        if k in data and data[k] is not None:
            out[k] = str(data[k]).strip() if k != "intent" else str(data[k]).strip()
    if out["intent"] not in ("new_lead", "stage_update"):
        out["intent"] = "new_lead"
    if out["exhibition"] not in EXHIBITIONS:
        out["exhibition"] = "Other" if out["exhibition"] else ""
    if out["stage"] not in PIPELINE_STAGES:
        out["stage"] = ""
    return out


def _empty_brief():
    return {
        "size": "", "location": "", "layout": "", "design_direction": "",
        "brand_colours": "", "meeting_room": "", "features": [], "av": "",
        "products": "", "notes": "",
    }


def extract_brief(text="", image_bytes=None, image_mime="image/png"):
    """Read a client brief (pasted text / screenshot / voice) into design-brief fields."""
    client = _client()
    if not client:
        return _empty_brief()

    prompt = (
        "Extract an exhibition-stand design brief from the input and return ONLY JSON with keys:\n"
        '{ "size": string (e.g. "8m x 10m (80 sqm)"),\n'
        '  "location": string (hall / booth),\n'
        '  "layout": one of ' + json.dumps(LAYOUTS) + ',\n'
        '  "design_direction": string,\n'
        '  "brand_colours": string,\n'
        '  "meeting_room": one of ' + json.dumps(MEETING_ROOMS) + ',\n'
        '  "features": array containing any of ' + json.dumps(BRIEF_FEATURES) + ',\n'
        '  "av": string (screens/AV),\n'
        '  "products": string,\n'
        '  "notes": string }\n'
        "Only include what is present. Empty string / empty array if unknown. JSON only."
    )
    user_content = [{"type": "text", "text": prompt}]
    if text:
        user_content.append({"type": "text", "text": f"Client brief / notes:\n{text}"})
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        user_content.append({"type": "image_url",
                             "image_url": {"url": f"data:{image_mime};base64,{b64}"}})

    model = str(st.secrets.get("OPENAI_LEAD_MODEL", "gpt-4o-mini")).strip() or "gpt-4o-mini"
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": _SYSTEM},
                      {"role": "user", "content": user_content}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception:
        return _empty_brief()

    out = _empty_brief()
    for k in out:
        if k not in data or data[k] is None:
            continue
        if k == "features":
            out[k] = [f for f in data[k] if f in BRIEF_FEATURES] if isinstance(data[k], list) else []
        else:
            out[k] = str(data[k]).strip()
    if out["layout"] not in LAYOUTS:
        out["layout"] = ""
    if out["meeting_room"] not in MEETING_ROOMS:
        out["meeting_room"] = ""
    return out
