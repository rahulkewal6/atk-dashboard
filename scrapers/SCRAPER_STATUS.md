# ATK Exhibition Scraper — Status Log

Last updated: 2026-06-12

## Completed ✅

| Exhibition | File | Companies | Notes |
|---|---|---|---|
| Beautyworld Dubai | `beautyworld_dubai_scraper.py` | 2,482 | Full data: name, country, phone, email, website, hall, stand |
| Paperworld Middle East | `paperworld_me_scraper.py` | 489 | Full data |
| Automechanika Dubai | `automechanika_dubai_scraper.py` | 2,229 | Different detail URL pattern: `exhibitor-list.detail.html` |
| Gifts & Lifestyle ME | `gifts_lifestyle_me_scraper.py` | 221 | Full data |
| Intersec KSA | `intersec_ksa_scraper.py` | 490 | Full data |
| Intersec UAE | `intersec_uae_scraper.py` | 1,197 | Full data |
| Light Middle East | `light_middle_east_scraper.py` | 340 | Full data |
| Beauty World KSA | `beautyworld_ksa_scraper.py` | 201 | Full data |
| Achema Middle East | `achema_me_scraper.py` | 52 | Static list page — NO phone or email on site at all |
| ADIHEX 2026 | `adihex_scraper.py` | 775 | **Company Name, Country, Website ONLY** (no phone/email in ADIHEX's data model) |

All output files saved to Desktop as `NEW <exhibition>_exhibitors.xlsx`

---

## Pending / On Hold ⏳

| Exhibition | Status | Reason |
|---|---|---|
| Automechanika Frankfurt | ❌ Failing | 360 pages, ~32,400 companies. Playwright timeouts on pages 3-4. Site aggressively throttles headless browsers. Needs alternative approach. |
| ATM (Arabian Travel Market) | ⏳ On hold | ReedExpo/Algolia platform. 0 exhibitors published — event Sept 2026. Check back ~2 months before event. |

---

## Fields Requested by Rahul
- Company Name
- Website
- Phone
- Email
- Country
- Hall / Stand

**Exception:** ADIHEX — Rahul accepted Name + Country + Website only (will find emails manually via Apollo)

---

## Output File Naming Convention
Always: `NEW <exhibition_name>_exhibitors.xlsx` saved to `/Users/deepakkewal/Desktop/`
