"""
ATM (Arabian Travel Market) 2026 — Exhibitor Scraper
Fields: Company Name, Website, Email, Phone (also Country, Stand)
Source: WTM/ReedExpo Algolia search API
Output: /Users/deepakkewal/Desktop/NEW atm_exhibitors.xlsx
"""

import time
import requests
import pandas as pd

APP_ID = "XD0U5M6Y4R"
API_KEY = "d5cd7d4ec26134ff4a34d736a7f9ad47"
INDEX = "evt-1aafcc50-e1bd-4fb8-9f3e-5668b885277c-index"
EVENT_EDITION = "eve-10bc3b35-320d-4b88-a577-08149c81a02f"
URL = f"https://{APP_ID.lower()}-dsn.algolia.net/1/indexes/{INDEX}/query"
OUTPUT_FILE = "/Users/deepakkewal/Desktop/NEW atm_exhibitors.xlsx"

FILTERS = f"recordType:exhibitor AND locale:en-gb AND eventEditionId:{EVENT_EDITION}"
HEADERS = {"Content-Type": "application/json"}
PARAMS = {"x-algolia-application-id": APP_ID, "x-algolia-api-key": API_KEY}


def scrape():
    records = []
    page = 0
    hits_per_page = 100

    while True:
        body = {"params": f"query=&hitsPerPage={hits_per_page}&page={page}&filters={requests.utils.quote(FILTERS)}"}
        r = requests.post(URL, params=PARAMS, headers=HEADERS, json=body, timeout=20)
        d = r.json()
        hits = d.get("hits", [])
        nb_pages = d.get("nbPages", 1)
        total = d.get("nbHits", 0)

        for h in hits:
            records.append({
                "Company Name": h.get("companyName", "") or h.get("exhibitorName", ""),
                "Website": h.get("website", "") or "",
                "Email": h.get("email", "") or "",
                "Phone": h.get("phone", "") or "",
                "Country": h.get("countryName", "") or "",
                "Stand": h.get("standReference", "") or "",
            })

        print(f"  Page {page+1}/{nb_pages}: {len(hits)} items (total {total})")
        page += 1
        if page >= nb_pages:
            break
        time.sleep(0.4)

    # Dedup by company name
    seen, deduped = set(), []
    for rec in records:
        key = rec["Company Name"]
        if key and key not in seen:
            seen.add(key)
            deduped.append(rec)

    print(f"\nTotal unique companies: {len(deduped)}")
    cols = ["Company Name", "Website", "Email", "Phone", "Country", "Stand"]
    pd.DataFrame(deduped, columns=cols).to_excel(OUTPUT_FILE, index=False)
    print(f"Saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape()
