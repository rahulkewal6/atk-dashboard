"""
Scraper utilities for the ATK List Maker page.

Architecture:
  1. Jina.ai Reader API (r.jina.ai) — free, handles JS/React pages, infinite scroll.
     Returns clean markdown from any URL. No API key needed.
  2. Claude API (claude-3-5-haiku) — cheap, fast extraction of structured data from text.
  3. Jina.ai Search (s.jina.ai) — free website URL enrichment.
"""

import re
import json
import httpx
import pandas as pd

# ── Page fetching ─────────────────────────────────────────────────────────────

def fetch_via_jina(url: str, timeout: int = 40) -> tuple:
    """
    Fetch clean text content from any URL via Jina.ai Reader (free, handles JS).
    Returns (content_str, error_str).
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "Accept": "text/plain",
            "X-No-Cache": "true",
            "X-Return-Format": "markdown",
        }
        r = httpx.get(jina_url, headers=headers, timeout=timeout, follow_redirects=True)
        if r.status_code == 200 and r.text.strip():
            return r.text, ""
        return "", f"Jina.ai returned HTTP {r.status_code}"
    except Exception as e:
        return "", f"Fetch error: {e}"


def fetch_page(url: str) -> tuple:
    """
    Primary fetch: tries Jina.ai first, falls back to direct request.
    Returns (content_str, error_str).
    """
    content, err = fetch_via_jina(url)
    if content:
        return content, ""
    # Fallback: direct HTTP
    try:
        r = httpx.get(
            url, timeout=20, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ATK-ListMaker/1.0)"},
        )
        return r.text, ""
    except Exception as e:
        return "", str(e)


# ── URL pagination helper ──────────────────────────────────────────────────────

def paginate_url(base_url: str, page_num: int) -> str:
    """
    Given a base URL and page number > 1, return a paginated URL.
    Tries common patterns: ?page=N, &page=N, /page/N, /page-N
    """
    if page_num == 1:
        return base_url
    if "?" in base_url:
        # Remove existing page param if any
        cleaned = re.sub(r'[&?]page=\d+', '', base_url).rstrip("&")
        return f"{cleaned}&page={page_num}"
    return f"{base_url.rstrip('/')}/page/{page_num}"


# ── Claude extraction ──────────────────────────────────────────────────────────

_EXTRACTION_SYSTEM = """You are a data extraction assistant. Extract exhibitor data from exhibition/trade-show webpage content. Return ONLY a valid JSON array — no explanation, no markdown fences, no extra text. Just the raw JSON array."""

_EXTRACTION_PROMPT = """URL scraped: {url}

User notes about this page:
{instructions}

Extract every exhibitor/company listed. For each, extract all of:
- company_name  (required — use "" if truly absent)
- country       (country of origin, or "")
- email         (email address, or "")
- phone         (phone/mobile number, or "")
- website       (company website URL, or "")
- stand_number  (booth/stand number, or "")
- hall          (hall, pavilion, zone, or "")

Rules:
- Include ALL companies found, even if only the name is available.
- Do not skip companies just because they have no contact info.
- If you see pagination links or "Load more" text, note it in a final object: {{"_meta": "has_more_pages"}}
- Return ONLY the JSON array. No markdown, no commentary.

PAGE CONTENT (truncated to first 60 000 chars):
{content}"""


def extract_exhibitors(content: str, url: str, instructions: str, api_key: str) -> tuple:
    """
    Use Claude Haiku to extract structured exhibitor data from page text.
    Returns (list_of_dicts, error_str, has_more_pages_hint).
    """
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        prompt = _EXTRACTION_PROMPT.format(
            url=url,
            instructions=instructions.strip() if instructions else "None provided.",
            content=content[:60_000],
        )
        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=8192,
            system=_EXTRACTION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()

        # Extract JSON array from response
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return [], f"Claude returned unexpected format: {raw[:300]}", False

        data = json.loads(match.group())

        # Check for has-more hint
        has_more = False
        clean = []
        for row in data:
            if "_meta" in row:
                if "has_more" in str(row.get("_meta", "")):
                    has_more = True
            else:
                clean.append(row)
        return clean, "", has_more

    except Exception as e:
        return [], str(e), False


# ── Website enrichment via Jina.ai search ────────────────────────────────────

def enrich_missing_websites(rows: list, progress_callback=None) -> list:
    """
    For rows where website == "", search Jina.ai to find the company's official website.
    progress_callback(company_name) is called before each search if provided.
    """
    _SKIP_DOMAINS = {
        "facebook.com", "twitter.com", "linkedin.com", "instagram.com",
        "youtube.com", "wikipedia.org", "google.com", "jina.ai",
        "bloomberg.com", "crunchbase.com", "trustpilot.com",
    }

    enriched = []
    for row in rows:
        name = row.get("company_name", "").strip()
        if not row.get("website") and name:
            if progress_callback:
                progress_callback(name)
            try:
                q = f"{name} official website"
                r = httpx.get(
                    f"https://s.jina.ai/{httpx.URL(q)}",
                    timeout=15,
                    headers={"Accept": "text/plain"},
                )
                if r.status_code == 200:
                    urls = re.findall(r'https?://[^\s\)\"\'\]]+', r.text)
                    for found in urls:
                        domain = re.search(r'https?://([^/]+)', found)
                        if domain:
                            d = domain.group(1).lstrip("www.")
                            if not any(skip in d for skip in _SKIP_DOMAINS):
                                row = dict(row)
                                row["website"] = found.rstrip(".,;)")
                                break
            except Exception:
                pass
        enriched.append(row)
    return enriched


# ── DataFrame helper ──────────────────────────────────────────────────────────

_COL_RENAME = {
    "company_name": "Company Name",
    "country":      "Country",
    "email":        "Email",
    "phone":        "Phone",
    "website":      "Website",
    "stand_number": "Stand Number",
    "hall":         "Hall / Pavilion",
}

_COL_ORDER = ["Company Name", "Country", "Email", "Phone", "Website", "Stand Number", "Hall / Pavilion"]


def rows_to_df(rows: list) -> pd.DataFrame:
    """Convert extracted row dicts to a clean, consistently-ordered DataFrame."""
    if not rows:
        return pd.DataFrame(columns=list(_COL_RENAME.values()))
    df = pd.DataFrame(rows)
    df = df.rename(columns={k: v for k, v in _COL_RENAME.items() if k in df.columns})
    ordered = [c for c in _COL_ORDER if c in df.columns]
    # Keep any unexpected extra columns at the end
    extra = [c for c in df.columns if c not in ordered]
    df = df[ordered + extra]
    # Clean up: replace NaN with ""
    df = df.fillna("").astype(str).replace("nan", "").replace("None", "")
    return df


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Return Excel file bytes for a DataFrame."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Exhibitors"

    # Header styling
    header_fill = PatternFill("solid", fgColor="FF6600")
    header_font = Font(bold=True, color="FFFFFF")

    for col_idx, col_name in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Data rows
    for row_idx, row in enumerate(df.itertuples(index=False), 2):
        for col_idx, value in enumerate(row, 1):
            ws.cell(row=row_idx, column=col_idx, value=str(value) if value else "")

    # Auto-fit column widths
    for col_idx, col_name in enumerate(df.columns, 1):
        max_len = max(len(str(col_name)),
                      max((len(str(v)) for v in df.iloc[:, col_idx - 1]), default=0))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 50)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
