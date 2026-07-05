"""
Pure builders for the design-brief email — no Streamlit, so the on-screen
preview and the actually-sent email are byte-for-byte the same.
"""
import re

_ORANGE = "#FF6600"
_DARK = "#16181D"


def _fmt(s):
    """Inline formatting: **bold** and ==highlight== → HTML."""
    s = str(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"==(.+?)==",
               r'<mark style="background:#FFF3C4;padding:0 2px;border-radius:2px;">\1</mark>', s)
    return s


def build_subject(data):
    bits = [data.get("company", ""), data.get("exhibition", ""), data.get("size", "")]
    bits = [b for b in bits if str(b).strip()]
    return "Design brief — " + " — ".join(bits) if bits else "Design brief"


def _section(title, lines):
    lines = [l for l in lines if str(l).strip()]
    if not lines:
        return ""
    lis = "".join(f'<li style="margin:2px 0;">{_fmt(l)}</li>' for l in lines)
    return (
        f'<div style="font-size:12px;font-weight:600;color:{_ORANGE};'
        f'text-transform:uppercase;letter-spacing:0.04em;margin:14px 0 4px;">{title}</div>'
        f'<ul style="margin:0;padding-left:18px;color:#222;">{lis}</ul>'
    )


def build_brief_html(data, attachment_names=None):
    """Build the email body HTML from the brief fields."""
    company    = data.get("company", "")
    exhibition = data.get("exhibition", "")
    size       = data.get("size", "")
    location   = data.get("location", "")
    layout     = data.get("layout", "")
    direction  = data.get("design_direction", "")
    colours    = data.get("brand_colours", "")
    meeting    = data.get("meeting_room", "")
    features   = data.get("features", []) or []
    av         = data.get("av", "")
    products   = data.get("products", "")
    notes      = data.get("notes", "")
    deadline   = data.get("deadline", "")
    sender     = data.get("sender", "")

    stand = _section("Stand", [
        f"Size: {size}" if size else "",
        f"Location: {location}" if location else "",
        f"Layout: {layout}" if layout else "",
    ])
    design = _section("Design direction", [
        *[l.strip() for l in str(direction).splitlines() if l.strip()],
        (f"Brand colours: {colours}" + (" (logo and guidelines attached)" if colours else "")) if colours else "",
    ])
    func_lines = []
    if meeting and meeting != "None":
        func_lines.append(f"Meeting room: {meeting.lower()}")
    elif meeting == "None":
        func_lines.append("Meeting room: none")
    if features:
        func_lines.append(", ".join(features))
    functional = _section("Functional", func_lines)
    av_s       = _section("AV / digital", [av])
    prod_s     = _section("Products to highlight", [products])
    notes_s    = _section("Notes", [l.strip() for l in str(notes).splitlines() if l.strip()])

    deadline_html = ""
    if str(deadline).strip():
        deadline_html = (
            f'<p style="margin:14px 0;padding:8px 12px;background:#FAEEDA;color:#854F0B;'
            f'border-radius:8px;font-weight:600;">First concept needed by: {deadline}</p>'
        )

    att_html = ""
    if attachment_names:
        chips = "".join(
            f'<span style="font-size:12px;border:1px solid #E6E8EC;border-radius:999px;'
            f'padding:3px 10px;margin:2px 4px 2px 0;display:inline-block;">{n}</span>'
            for n in attachment_names
        )
        att_html = (
            f'<div style="border-top:1px solid #E6E8EC;margin-top:14px;padding-top:10px;">'
            f'<div style="font-size:12px;color:#888;margin-bottom:6px;">'
            f'{len(attachment_names)} attachment(s)</div>{chips}</div>'
        )

    return f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;
            background:#fff;border:1px solid #E6E8EC;border-radius:10px;overflow:hidden;">
  <div style="background:{_DARK};padding:14px 20px;">
    <span style="color:{_ORANGE};font-size:1.1rem;font-weight:700;">ATK</span>
    <span style="color:#fff;font-size:1.1rem;"> Exhibitions</span>
  </div>
  <div style="padding:20px;color:#222;font-size:13.5px;line-height:1.6;">
    <p style="margin:0 0 12px;">Dear Imran,</p>
    <p style="margin:0 0 6px;">Please find the design brief for
       <strong>{company or "the client"}</strong>{f" at {exhibition}" if exhibition else ""} below.</p>
    {stand}{design}{functional}{av_s}{prod_s}{notes_s}
    {deadline_html}
    <p style="margin:14px 0 2px;">Thanks,</p>
    <p style="margin:0;">{sender or "ATK Exhibitions"} — ATK Exhibitions</p>
    {att_html}
  </div>
</div>"""
