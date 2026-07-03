"""
Pure email sending + HTML builders — NO Streamlit dependency, so this can be
imported by both the Streamlit app (instant emails) and the GitHub Action
digest script (scheduled emails).
"""
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from email import encoders

_ORANGE = "#FF6600"
_DARK = "#1A1A1A"


def send_email(to_addr, subject, html_body, from_addr, app_password,
               from_name="ATK Dashboard"):
    """Send one HTML email via Gmail SMTP. Returns True on success, never raises."""
    if not (to_addr and from_addr and app_password):
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((from_name, from_addr))
        msg["To"] = to_addr
        msg.attach(MIMEText(html_body, "html"))
        # timeout so a slow/blocked SMTP connection can never hang for minutes
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(from_addr, app_password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        return True
    except Exception:
        return False


def compress_image(name, data, max_bytes=1_800_000, max_dim=1800):
    """Shrink a large image so email attachments stay under Gmail's 25 MB cap.
    Returns (new_name, new_bytes, mime). Non-images or failures pass through."""
    lower = name.lower()
    is_img = lower.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"))
    if not is_img or len(data) <= max_bytes:
        mime = "image/png" if lower.endswith(".png") else "image/jpeg"
        return name, data, (mime if is_img else "application/octet-stream")
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        w, h = img.size
        scale = min(1.0, max_dim / max(w, h))
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=80, optimize=True)
        new = out.getvalue()
        base = name.rsplit(".", 1)[0]
        return f"{base}.jpg", new, "image/jpeg"
    except Exception:
        return name, data, "application/octet-stream"


def send_email_with_attachments(to_addrs, subject, html_body, from_addr, app_password,
                                attachments=None, cc_addrs=None, reply_to=None,
                                from_name="ATK Exhibitions"):
    """Send an HTML email with file attachments. attachments = list of (filename, bytes, mimetype).
    Returns True on success, never raises."""
    to_addrs = [a for a in (to_addrs or []) if a]
    cc_addrs = [a for a in (cc_addrs or []) if a]
    if not (to_addrs and from_addr and app_password):
        return False
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = formataddr((from_name, from_addr))
        msg["To"] = ", ".join(to_addrs)
        if cc_addrs:
            msg["Cc"] = ", ".join(cc_addrs)
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(html_body, "html"))
        for fname, fbytes, fmime in (attachments or []):
            maintype, _, subtype = (fmime or "application/octet-stream").partition("/")
            part = MIMEBase(maintype or "application", subtype or "octet-stream")
            part.set_payload(fbytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=fname)
            msg.attach(part)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(from_addr, app_password)
            server.sendmail(from_addr, to_addrs + cc_addrs, msg.as_string())
        return True
    except Exception:
        return False


def wrap_html(title, inner, link=""):
    """Wrap inner HTML in the branded ATK email shell."""
    btn = ""
    if link:
        btn = (
            f'<a href="{link}" style="display:inline-block;margin-top:18px;'
            f'background:{_ORANGE};color:#fff;text-decoration:none;'
            f'padding:10px 20px;border-radius:6px;font-weight:600;">Open the ATK Dashboard</a>'
        )
    return f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;
            background:#ffffff;border:1px solid #eee;border-radius:10px;overflow:hidden;">
  <div style="background:{_DARK};padding:16px 22px;">
    <span style="color:{_ORANGE};font-size:1.2rem;font-weight:800;">ATK</span>
    <span style="color:#fff;font-size:1.2rem;"> Exhibitions</span>
  </div>
  <div style="padding:22px;color:#222;">
    <h2 style="margin:0 0 14px;color:{_DARK};font-size:1.15rem;">{title}</h2>
    {inner}
    {btn}
  </div>
  <div style="padding:14px 22px;background:#fafafa;color:#999;font-size:0.78rem;">
    ATK Exhibitions Sales Dashboard — automated message, please do not reply.
  </div>
</div>"""


def _row(label, value):
    if not value:
        return ""
    return (
        f'<tr><td style="padding:3px 10px 3px 0;color:#888;">{label}</td>'
        f'<td style="padding:3px 0;color:#222;font-weight:600;">{value}</td></tr>'
    )


def task_assigned_html(title, assigned_by, priority, due, notes, link=""):
    inner = (
        f'<p style="margin:0 0 12px;">{assigned_by} assigned you a task:</p>'
        f'<p style="font-size:1.05rem;font-weight:700;margin:0 0 12px;">{title}</p>'
        f'<table style="border-collapse:collapse;">'
        + _row("Priority", priority) + _row("Due", due) + _row("Notes", notes)
        + "</table>"
    )
    return wrap_html("📋 New task for you", inner, link)


def task_due_html(title, due_when, priority, notes, link=""):
    inner = (
        '<p style="margin:0 0 12px;">Heads-up — this task is due in about an hour '
        'and isn\'t marked done yet:</p>'
        f'<p style="font-size:1.05rem;font-weight:700;margin:0 0 12px;">{title}</p>'
        '<table style="border-collapse:collapse;">'
        + _row("Due", due_when) + _row("Priority", priority) + _row("Notes", notes)
        + "</table>"
    )
    return wrap_html("⏰ Task due soon", inner, link)


def followup_due_html(company, due_when, exhibition, notes, link=""):
    inner = (
        '<p style="margin:0 0 12px;">Heads-up — this follow-up is due in about an hour:</p>'
        f'<p style="font-size:1.05rem;font-weight:700;margin:0 0 12px;">{company}</p>'
        '<table style="border-collapse:collapse;">'
        + _row("When", due_when) + _row("Exhibition", exhibition) + _row("Notes", notes)
        + "</table>"
    )
    return wrap_html("⏰ Follow-up due soon", inner, link)


def followup_assigned_html(assigned_by, company, exhibition, fu_date, notes,
                           contact_name, contact_phone, contact_email, link=""):
    contact_rows = _row("Name", contact_name) + _row("Phone", contact_phone) + _row("Email", contact_email)
    contact_block = ""
    if contact_rows:
        contact_block = (
            '<div style="margin-top:14px;padding:12px;background:#fff7f0;border-radius:8px;">'
            '<div style="color:#888;font-size:0.8rem;margin-bottom:4px;">📞 Customer contact</div>'
            f'<table style="border-collapse:collapse;">{contact_rows}</table></div>'
        )
    inner = (
        f'<p style="margin:0 0 12px;">{assigned_by} assigned you a follow-up:</p>'
        '<table style="border-collapse:collapse;">'
        + _row("Client", company) + _row("Exhibition", exhibition)
        + _row("Follow-up date", fu_date) + _row("Notes", notes)
        + "</table>" + contact_block
    )
    return wrap_html("📅 New follow-up for you", inner, link)
