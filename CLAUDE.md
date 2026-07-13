# ATK Dashboard — Claude Code Project Instructions

## What this project is
Streamlit multi-page dashboard for **ATK Exhibition Organizers LLC, Dubai** (stand design & build company).
Owner: Rahul Kewal (rahulkewal6@gmail.com). Team: Bhavika (editor), Deepak (editor).

Deployed on **Streamlit Cloud** (live: https://atkdashboard.streamlit.app), code on GitHub repo `atk-dashboard` (public).

> **Full internal record:** `PROJECT_LOG.md` (gitignored) holds the complete decision log,
> changelog, credentials, rollback details, and pending work. Read it first on long sessions.

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
  --exclude='PROJECT_LOG.md' \
  "/Users/deepakkewal/Desktop/Dashboard build/" \
  "/Users/deepakkewal/Desktop/atk-dashboard/"
```

**Push:** Rahul uses GitHub Desktop (terminal push fails — needs stored credentials).

---

## NEVER do these things
- **NEVER commit `.streamlit/secrets.toml`** — contains all API keys, passwords, service account
- **NEVER commit `.claude/`, `SETUP.md`, `RULES.md`, `STRATEGY.md`, `PROJECT_LOG.md`** — internal only
- **NEVER use `google-generativeai`** — wrong SDK. Use `google-genai>=1.0.0`
- **NEVER create new standalone Google Spreadsheets** — service account has 0 GB Drive quota (gets 403)
- **NEVER use Python 3.10+ type syntax** (`str | None`) — Streamlit Cloud runs Python 3.9. Use `Optional[str]` or `str = None`
- **NEVER use nested `@st.cache_data` decorators** — causes ImportError on Streamlit Cloud
- **NEVER push `--force` or skip hooks**

---

## App pages (sidebar order)
Navigation uses `st.navigation` in `app.py` (the entrypoint/router — do not rename it).
Pages must NOT call `st.set_page_config` — it is called once in `app.py`.

| File | Page | Notes |
|------|------|-------|
| `home.py` | 🏠 Home | Metric tiles + per-user 🔔 notification panel (open tasks/follow-ups) |
| `pages/9_Quick_Add.py` | ✨ Quick Add | Voice (Whisper) + screenshot (GPT-4o vision) → new lead OR stage update, confirm-first |
| `pages/0_Tasks.py` | 📋 Tasks | Tasks: ⋮ edit/delete, Active/Completed/All views, completion history, due time |
| `pages/1_Leads.py` | 🎯 Leads | Pipeline: 6-tier status cards, inline stage popover, ⋮ delete, lead #, Stand Size |
| `pages/2_Follow_Ups.py` | 📅 Follow Ups | Follow-ups w/ time; ⋮ edit/delete; appear in Tasks banner when due |
| `pages/8_Design_Tracker.py` | 🎨 Designs | Briefs pending with the designer; days waiting; chase-task action |
| `pages/10_Design_Brief.py` | 📐 Design Brief | Compose/preview/send a brief to Imran w/ attachments; polish AI; auto-tracks |
| `pages/3_Sequences.py` | ✉️ Sequences | Apollo sequences + "who replied" list (opens-per-person not in Apollo API) |
| `pages/4_Reports.py` | 📊 Reports | Dashboard metrics |
| `pages/5_Calendar.py` | 🗓️ Calendar | Exhibition event calendar |
| `pages/6_Database.py` | 🗂️ Database | Exhibitor database (upload + call tracking) |
| `pages/7_List_Maker.py` | 🕷️ List Maker | AI web scraper → Excel download |

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
Defined in `utils/constants.py` → `PIPELINE_STAGES`, grouped by `STAGE_TIERS` / `TIER_STYLE` into 6 status buckets (shown as clickable filter cards on the Leads page):

- 🔴 **red — Action needed** (pending on us): Hot Leads, Info Request Replied, Brief Received v1-3, New Brief Received, Additional Changes Requested, Client Requested Discount, No Response
- 🟡 **design_prog — Design in progress**: Brief Sent to Designer, Revised Brief Sent to Designer
- 🟠 **quote_prog — Quotation in progress**: Brief Sent to Vendor, Vendor Quotation Received, Client Quotation Prepared
- 🟢 **design_client — Design with client**: Design Option 1/2/3 Sent, Waiting for Design Feedback
- 🔵 **quote_client — Quotation with client**: Client Quotation 1 Sent, Discounted/Revised Quotation Sent, Waiting for Final Approval
- ✅ **won** / ❌ **lost**

---

## Email + notifications + time (added after initial build)
- **Emails:** `utils/email_util.py` (pure SMTP+HTML, shared by app & GitHub Actions), `utils/notify.py`
  (instant in-app sends). Instant emails on task/follow-up assignment. Scheduled via GitHub Actions:
  `.github/workflows/atk_digest.yml` (Sun + Mon/Wed/Fri) and `atk_deadline.yml` (every 15 min, ~1 hr before due).
  Gmail account `atk.dashboard0@gmail.com` + App Password. GitHub repo Secrets: GMAIL_ADDRESS,
  GMAIL_APP_PASSWORD, GOOGLE_SHEET_ID, GCP_SERVICE_ACCOUNT, DASHBOARD_URL.
- **Time:** all times stored in **UAE (UTC+4)**; India (IST = UAE + 1h30m) shown alongside via
  `utils/timeutil.py` (`time_with_ist`). Time picker = 12-hr AM/PM 15-min dropdown (`utils/ui.py` `time_select`).
- **Notifications:** `utils/notifications.py` — Home panel of the user's open items; sidebar badge uses
  `st.switch_page` (NOT an `<a href>` — a full reload logs the user out).
- **AI intake:** `utils/ai_intake.py` — Whisper transcribe + GPT-4o-mini vision → structured lead JSON.
  Model via `OPENAI_LEAD_MODEL` secret (default gpt-4o-mini). Confirm-first, never auto-saves.

## Theme (light + dark sidebar, 2026-06-30)
- `.streamlit/config.toml`: `base="light"` + `[theme.sidebar]` dark. `utils/branding.py` = white cards,
  dark sidebar, orange accents. `TIER_STYLE` colors are light-theme (dark text on light tint).
- **Rollback:** dark theme saved as Desktop backup folder + git tag `dark-theme-v1`.

## Shared utilities
- `utils/sheets.py` — all Google Sheets read/write; `_ensure_columns` (grows grid before adding cols);
  session read-cache; row = df-index + 2.
- `utils/constants.py` — PIPELINE_STAGES, STAGE_TIERS, TIER_STYLE, EXHIBITIONS (incl. GITEX), SOURCES,
  USERS (Rahul/Bhavika/Deepak), USER_EMAILS, all `*_HEADERS`.
- `utils/branding.py` — `inject_css()`, `show_logo()` — called on every page
- `utils/auth.py` — `require_login()`, `show_user_bar()`, `is_admin()`, `get_display_name()`, `can_modify(owner)`
- `utils/scraper.py` — Jina.ai + AI scraping functions for List Maker
- `utils/lead_detail.py` — `show_lead_dialog` (st.dialog): contact (copy boxes, no tel/mailto),
  stage funnel, Add-to-Follow-up/Task, edit/history/delete
- `utils/design_brief.py` (pure builder), `utils/brief_ui.py` (composer) — brief → Imran
- `utils/ai_intake.py` — `extract(images=[...])` multi-image, `pdf_text`, `polish_notes(text, instruction)`
- `utils/ui.py` — `time_select`, `greeting_header(dark=)`, `pipeline_bars`
- **Streamlit gotchas** (see `PROJECT_LOG.md`): file-uploaders reset via rotating key; can't set a widget's
  session key after it rendered (stage into a pending key, apply next run); `st-key-*` classes target CSS;
  st.dialog/pills/audio_input/[theme.sidebar] need streamlit>=1.40; `<a href>` nav logs users out (use switch_page)

---

## Secrets structure (never commit — reference only)
```toml
APOLLO_API_KEY = "..."
GEMINI_API_KEY = "AQ...."           # Google AI Studio
OPENAI_API_KEY = "sk-..."           # OpenAI (List Maker + Quick Add AI)
OPENAI_LEAD_MODEL = "gpt-4o-mini"   # optional — upgrade Quick Add model, no code change
GOOGLE_SHEET_ID = "..."             # Main ATK Dashboard spreadsheet
EXHIBITOR_SHEET_ID = "..."          # ATK Exhibitor Database spreadsheet
GMAIL_ADDRESS = "atk.dashboard0@gmail.com"
GMAIL_APP_PASSWORD = "..."          # 16-char Gmail App Password (2FA on)
DASHBOARD_URL = "https://atkdashboard.streamlit.app"

[users.rahul]   # admin
[users.bhavika] # editor
[users.deepak]  # editor

[gcp_service_account]  # full service account JSON
```
GitHub repo Secrets (for the email Actions) mirror: GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
GOOGLE_SHEET_ID, GCP_SERVICE_ACCOUNT, DASHBOARD_URL.

---

## Coding standards for this project
- No comments unless the WHY is non-obvious
- Python 3.9 compatible syntax only
- **streamlit>=1.40** (st.audio_input, `[theme.sidebar]`); `st.container(border=True)`, popovers etc. OK
- Keep all business logic in `utils/` — pages are thin UI layers
- `st.rerun()` after any Google Sheets write to refresh state
- Use `st.cache_data(ttl=60)` on public read functions, never on private helpers
