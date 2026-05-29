"""
Scraper utilities for the ATK List Maker page.

Architecture:
  1. Jina.ai Reader API (r.jina.ai) — free, handles JS/React pages, infinite scroll.
     Returns clean markdown from any URL. No API key needed.
  2. Gemini 1.5 Flash (FREE via Google AI Studio) — extracts structured data from text.
     1M token context window — handles even the largest exhibitor lists.
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


# ── Gemini client (shared) ────────────────────────────────────────────────────

def _gemini_model(api_key: str, system: str = ""):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name="gemini-1.5-flash",
                                 system_instruction=system or "You are a helpful assistant.")


# ── Smart pagination: Gemini finds the REAL next-page URL ─────────────────────

_NEXT_PAGE_SYSTEM = "You are a web scraping assistant. Analyse webpage content and return only what is asked — no explanation."

_NEXT_PAGE_PROMPT = """Current page URL: {current_url}
Base / start URL: {base_url}

Look at the page content below and find the URL of the NEXT page of results.
Look for: "Next", ">", "›", pagination numbers, or any link labelled with the next page number.

Rules:
- If you find a next-page URL, return it as a single line with no other text.
- If it is a relative URL (e.g. /exhibitors?page=2), prepend the domain to make it absolute.
- If there is NO next page (last page or only one page), return exactly: NO_MORE_PAGES
- Return NOTHING else — just the URL or NO_MORE_PAGES.

PAGE CONTENT (first 30 000 chars):
{content}"""


def find_next_page_url(content: str, current_url: str, base_url: str, api_key: str) -> str:
    """
    Ask Gemini to find the real next-page URL from the page content.
    Returns the next URL string, or "" if no more pages.
    """
    try:
        model = _gemini_model(api_key, _NEXT_PAGE_SYSTEM)
        prompt = _NEXT_PAGE_PROMPT.format(
            current_url=current_url,
            base_url=base_url,
            content=content[:30_000],
        )
        response = model.generate_content(prompt)
        result = response.text.strip()
        if not result or "NO_MORE_PAGES" in result.upper():
            return ""
        # Basic sanity check — must look like a URL
        if result.startswith("http"):
            return result
        # Try to make relative URL absolute
        from urllib.parse import urljoin
        return urljoin(base_url, result)
    except Exception:
        return ""


# ── Extraction ────────────────────────────────────────────────────────────────

_EXTRACTION_SYSTEM = (
    "You are a precise data extraction assistant. "
    "Extract exhibitor data from exhibition/trade-show webpage content. "
    "Return ONLY a valid JSON array — no explanation, no markdown fences, no extra text."
)

_EXTRACTION_PROMPT = """URL scraped: {url}

User notes about this page:
{instructions}

Extract EVERY exhibitor/company listed on this page. For each one, extract:
- company_name  (required — use "" only if truly absent)
- country       (country of origin, or "")
- email         (email address, or "")
- phone         (phone/mobile number, or "")
- website       (company website URL, or "")
- stand_number  (booth/stand number, or "")
- hall          (hall, pavilion, zone, or "")

Critical rules:
- Include EVERY company found — do not skip any, even if they have no contact info.
- Do not summarise, do not say "and X more" — list every single one.
- If you see a "Next" / pagination link in the content, add one final object: {{"_meta": "has_more_pages"}}
- Return ONLY the JSON array. No markdown, no commentary.

PAGE CONTENT:
{content}"""


def extract_exhibitors(content: str, url: str, instructions: str, api_key: str) -> tuple:
    """
    Use Gemini 1.5 Flash (free, 1M context) to extract all exhibitors from page text.
    Returns (list_of_dicts, error_str, has_more_pages_hint).
    """
    try:
        model = _gemini_model(api_key, _EXTRACTION_SYSTEM)
        prompt = _EXTRACTION_PROMPT.format(
            url=url,
            instructions=instructions.strip() if instructions else "None provided.",
            content=content[:800_000],   # Gemini Flash: 1M token window
        )
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown fences if Gemini added them
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return [], f"Unexpected response format: {raw[:300]}", False

        data = json.loads(match.group())

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
