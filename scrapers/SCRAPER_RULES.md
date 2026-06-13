# ATK Scraper — Technical Rules & Decisions

Last updated: 2026-06-12

---

## Platform Identification

### Messe Frankfurt Platform
Sites: Beautyworld Dubai, Paperworld ME, Automechanika Dubai, Gifts & Lifestyle, Intersec KSA/UAE, Light Middle East, Beauty World KSA, Achema ME, Automechanika Frankfurt

**Pattern:**
- List pages are JS-rendered → use Playwright to collect detail URLs
- Detail pages are server-side rendered → use requests + BeautifulSoup
- CSS selectors (same across ALL Messe Frankfurt sites):
  - Company: `h1`
  - Country: `.ex-contact-box__address-field-full-address` → last non-empty line
  - Phone: `a.ex-contact-box__address-field-tel-number`
  - Email: regex on raw `r.text` (NOT `<a href="mailto:">` — email is in JS data blocks)
  - Website: `<a>` with text containing "website" whose href is not in SKIP_DOMAINS
  - Hall: `.ex-contact-box__container-location-category` + `.ex-contact-box__container-location-hall`
  - Stand: `.ex-contact-box__container-location-stand`

**Email extraction (CRITICAL):**
```python
SKIP_EMAIL = {"messefrankfurt.com", "sentry.io", "w3.org", "example.com"}
emails_found = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', r.text)
email = next((e for e in dict.fromkeys(emails_found) if not any(s in e for s in SKIP_EMAIL)), "")
```
Do NOT use `soup.find('a', href=re.compile('mailto'))` — emails are in JS blocks, not DOM links.

**List URL patterns (differ by site):**
- Most sites: `/en/exhibitor-search.html?page={page}&pagesize=90`
- Automechanika Dubai: `/en/exhibitor-search/exhibitor-list.html?page={page}&pagesize=90`

**Detail URL patterns (differ by site):**
- Most sites: `exhibitor-search.detail.html/{slug}.html`
- Automechanika Dubai: `exhibitor-list.detail.html/{slug}.html`

**Playwright settings for Messe Frankfurt:**
```python
await page.goto(url, wait_until="domcontentloaded", timeout=90000)
await page.wait_for_selector('a[href*="detail"]', timeout=30000)
```
Use `domcontentloaded` NOT `networkidle` — networkidle causes timeouts.

---

### ADIHEX Platform (ezone.adihex.com)
- Vue 3 + Pinia app embedded in adihex.com
- **API endpoint (no auth required, call directly with requests):**
  ```
  https://ezone.adihex.com/exhibitors-list-json/4/?event_id=4&orderby=name&tag=_all_&search=&start=_all_&page={page}
  ```
  - event_id=4 = ADIHEX 2026
  - Returns 40 per page, 20 pages total, 775 companies
- **Data model has NO phone or email fields** — website, country (nested dict), name, hall, stand available
- Country extraction: `item["country"]["name"]` (nested dict)
- If the list returns 0 with `tag=` or `start=` empty, use `tag=_all_&start=_all_`

**Why API returns 0 with direct curl (without browser):**
- Earlier sessions found 0 results when `tag=` and `start=` were empty strings
- Must use `tag=_all_&start=_all_` to get all results
- No CSRF or session cookie needed — just correct query params

---

### ReedExpo / WTM Platform (ATM)
- Uses Algolia search with protected API key
- Cannot scrape programmatically
- Wait until closer to event date — exhibitor list may be published by then

---

## General Rules

1. **Output files:** Always `/Users/deepakkewal/Desktop/NEW {exhibition}_exhibitors.xlsx`
2. **Columns order:** Company Name, Country, Phone, Email, Website, Hall, Stand, Profile URL
   - Exception ADIHEX: Company Name, Country, Website (no phone/email available)
3. **Background jobs:** Use `nohup bash -c 'python3 -u script.py > /tmp/logfile.log 2>&1' &` for long-running scrapers
4. **Rate limiting:** 0.4-0.5s sleep between detail page requests; 2s between list pages
5. **Deduplication:** Always deduplicate by URL before detail scraping; by company name in output

---

## Automechanika Frankfurt — Unresolved Issue
- 360 pages, ~32,400 companies
- Playwright times out on pages 3-4 even with domcontentloaded + 90s timeout + 3 retries
- Site appears to detect and throttle headless browsers
- Options to try next session:
  1. Add realistic browser headers + viewport to Playwright context
  2. Use slower page loads with random delays (3-8s between pages)
  3. Try with `wait_until="load"` instead of `domcontentloaded`
  4. Split into batches and run multiple nohup jobs in parallel
