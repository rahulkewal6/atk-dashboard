"""
ADIHEX 2026 — Exhibitor Scraper
Fields: Company Name, Country, Website
Output: /Users/deepakkewal/Desktop/NEW adihex_exhibitors.xlsx
"""

import time
import requests
import pandas as pd

BASE_API = "https://ezone.adihex.com/exhibitors-list-json/4/?event_id=4&orderby=name&tag=_all_&search=&start=_all_&page={page}"
OUTPUT_FILE = "/Users/deepakkewal/Desktop/NEW adihex_exhibitors.xlsx"
HEADERS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def scrape():
    records = []
    page = 1

    # Get first page to find total pages
    r = requests.get(BASE_API.format(page=1), headers=HEADERS, timeout=15)
    j = r.json()
    last_page = j["meta"]["last_page"]
    total = j["meta"]["total"]
    print(f"Total: {total} companies, {last_page} pages")

    def extract(items):
        for item in items:
            name = item.get("name", "").strip()
            if not name:
                continue
            country_obj = item.get("country") or {}
            country = country_obj.get("name", "") if isinstance(country_obj, dict) else str(country_obj)
            website = item.get("website", "") or ""
            records.append({"Company Name": name, "Country": country, "Website": website})

    extract(j["data"])
    print(f"  Page 1/{last_page}: {len(j['data'])} items")

    for pg in range(2, last_page + 1):
        r = requests.get(BASE_API.format(page=pg), headers=HEADERS, timeout=15)
        j = r.json()
        extract(j["data"])
        print(f"  Page {pg}/{last_page}: {len(j['data'])} items")
        time.sleep(0.5)

    print(f"\nTotal scraped: {len(records)}")
    df = pd.DataFrame(records, columns=["Company Name", "Country", "Website"])
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape()
