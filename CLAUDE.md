# ATK Dashboard — Claude Code Project Instructions

## What this project is
Streamlit multi-page dashboard for **ATK Exhibition Organizers LLC, Dubai** (stand design & build company).
Owner: Rahul Kewal (rahulkewal6@gmail.com). Team: Bhavika (editor), Deepak (editor).

Deployed on **Streamlit Cloud**, code on GitHub repo `atk-dashboard`.

---

## Two-directory workflow — CRITICAL
There are TWO local directories. Always work in "Dashboard build", then rsync to the git repo:

```
Working dir:  /Users/deepakkewal/Desktop/Dashboard build/   ← edit here
Git repo:     /Users/deepakkewal/Desktop/atk-dashboard/     ← rsync here, then push
```

**Sync command (run after every set of changes):**
```bash
rsync -av \
  --exclude='.streamlit/secrets.toml' \
  --exclude='.claude/' \
  --exclude='SETUP.md' \
  --exclude='RULES.md' \
  --exclude='STRATEGY.md' \
  "/Users/deepakkewal/Desktop/Dashboard build/" \
  "/Users/deepakkewal/Desktop/atk-dashboard/"
```

**Push:** Rahul uses GitHub Desktop (terminal push fails — needs stored credentials).

---

## NEVER do these things
- **NEVER commit `.streamlit/secrets.toml`** — contains all API keys, passwords, service account
- **NEVER commit `.claude/`, `SETUP.md`, `RULES.md`, `STRATEGY.md`** — internal only
- **NEVER use `google-generativeai`** — wrong SDK. Use `google-genai>=1.0.0`
- **NEVER create new standalone Google Spreadsheets** — service account has 0 GB Drive quota (gets 403)
- **NEVER use Python 3.10+ type syntax** (`str | None`) — Streamlit Cloud runs Python 3.9. Use `Optional[str]` or `str = None`
- **NEVER use nested `@st.cache_data` decorators** — causes ImportError on Streamlit Cloud
- **NEVER push `--force` or skip hooks**

---

## App pages (sidebar order)
| File | Page | Notes |
|------|------|-------|
| `pages/0_Tasks.py` | 📋 Tasks | Manual tasks + due follow-up notifications |
| `pages/1_Leads.py` | 🔴 Leads | Pipeline with stage management + follow-up button |
| `pages/1b_Follow_Ups.py` | 📅 Follow Ups | Scheduled follow-ups from leads |
| `pages/2_Sequences.py` | Sequences | Apollo email sequences |
| `pages/3_Reports.py` | Reports | Dashboard metrics |
| `pages/4_Calendar.py` | Calendar | Exhibition event calendar |
| `pages/5_Database.py` | Database | Exhibitor database (upload + call tracking) |
| `pages/6_List_Maker.py` | 🕷️ List Maker | AI web scraper → Excel download |

---

## Google Sheets architecture
**Main ATK Dashboard spreadsheet** (`GOOGLE_SHEET_ID` in secrets):
- `Pipeline` tab — leads data
- `Stage History` tab — lead stage change log
- `Event Calendar` tab — exhibitions calendar
- `DB Registry` tab — index of exhibitor database events
- `ATK Tasks` tab — tasks (auto-created by 0_Tasks.py)
- `ATK Followups` tab — follow-ups (auto-created by 1b_Follow_Ups.py)

**ATK Exhibitor Database spreadsheet** (`EXHIBITOR_SHEET_ID` in secrets):
- One tab per event (e.g. "ADIPEC 2025", "BeautyWorld Dubai 2026")
- Owned by Rahul's Google account, service account has Editor access
- This is the ONLY way to store exhibitor data — service account cannot create files

**Service account:** `atk-dashboard@atk-dashboard-497500.iam.gserviceaccount.com`
- Has access to both spreadsheets above
- Has 0 GB Drive quota — CANNOT create new spreadsheets, only write to shared ones

---

## Key technical decisions

### AI / LLM
- **List Maker uses OpenAI** (primary) or Gemini (fallback)
- Auto-detected by API key prefix: `sk-` → OpenAI GPT-4o-mini, everything else → Gemini 2.0 Flash
- Gemini `AQ.` format keys require `google-genai` package (NOT `google-generativeai`)
- Gemini 2.0 Flash free tier has `limit: 0` with AQ. keys in some regions — OpenAI is more reliable

### Scraper (List Maker)
- Jina.ai Reader (`r.jina.ai/{url}`) — free, handles JS/React/infinite scroll, no API key
- Gemini/GPT extracts structured JSON from Jina markdown
- Smart pagination: AI reads page content to find real "Next" URL
- Detail page enrichment: 15 concurrent threads, regex-first then AI fallback
- `detail_url` field extracted from listings → enriches email/phone/website/country

### Google Sheets client
```python
gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
```
- Use `@st.cache_resource` for the gspread client
- Use `@st.cache_data(ttl=60)` for data reads (never nested)

### Streamlit Cloud secrets
- Long values (IDs, API keys) must be on ONE line — editor wraps visually but adds real newlines
- Hardcoded fallback for `EXHIBITOR_SHEET_ID` in sheets.py in case secret is malformed

---

## Pipeline stages (leads)
Defined in `utils/constants.py` → `PIPELINE_STAGES`

**Red (pending/needs action):** Hot Lead (all types), Info Request Replied, Waiting for Design Feedback, Waiting for Final Approval, No Response — Follow Up Later, Client Requested Discount, Additional Changes Requested

**Green (active progress):** Brief Received, Brief Sent to Designer, Design Options Sent, Quotation stages (sent/prepared)

**Special:** Won ✅, Lost ❌

---

## Shared utilities
- `utils/sheets.py` — all Google Sheets read/write functions
- `utils/constants.py` — PIPELINE_STAGES, STAGE_COLORS, EXHIBITIONS, SOURCES, USERS, headers
- `utils/branding.py` — `inject_css()`, `show_logo()` — called on every page
- `utils/auth.py` — `require_login()`, `show_user_bar()`, `is_admin()`
- `utils/scraper.py` — Jina.ai + AI scraping functions for List Maker

---

## Secrets structure (never commit — reference only)
```toml
APOLLO_API_KEY = "..."
GEMINI_API_KEY = "AQ...."        # Google AI Studio
OPENAI_API_KEY = "sk-..."        # OpenAI (primary for List Maker)
GOOGLE_SHEET_ID = "..."          # Main ATK Dashboard spreadsheet
EXHIBITOR_SHEET_ID = "..."       # ATK Exhibitor Database spreadsheet

[users.rahul]   # admin
[users.bhavika] # editor
[users.deepak]  # editor

[gcp_service_account]  # full service account JSON
```

---

## Coding standards for this project
- No comments unless the WHY is non-obvious
- Python 3.9 compatible syntax only
- Streamlit 1.32+ features OK (`st.container(border=True)`, etc.)
- Keep all business logic in `utils/` — pages are thin UI layers
- `st.rerun()` after any Google Sheets write to refresh state
- Use `st.cache_data(ttl=60)` on public read functions, never on private helpers
