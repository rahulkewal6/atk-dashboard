"""
ACHEMA Middle East — Exhibitor Scraper (static list page)
Output: /Users/deepakkewal/Desktop/NEW achema_middle_east_exhibitors.xlsx
"""

import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = "https://achema-middle-east.ksa.messefrankfurt.com/ksa/en/exhibitor-list.html"
OUTPUT_FILE = "/Users/deepakkewal/Desktop/NEW achema_middle_east_exhibitors.xlsx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
SKIP_EMAIL = {"messefrankfurt.com", "sentry.io", "w3.org", "example.com"}


def scrape():
    print("Fetching ACHEMA Middle East exhibitor list...")
    r = requests.get(URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    records = []

    # Exhibitors appear as structured blocks — find all exhibitor name elements
    # Based on page structure: company name in heading, country and website follow
    main = soup.select_one("main")
    if not main:
        print("Could not find main content")
        return

    # Each exhibitor block contains name, country label, and website
    # Parse by finding all <p> or <div> blocks with "Country:" text
    text_blocks = main.get_text("\n").split("\n")
    text_blocks = [t.strip() for t in text_blocks if t.strip()]

    i = 0
    while i < len(text_blocks):
        line = text_blocks[i]
        # Detect company name: followed by "Country: X" pattern
        if i + 1 < len(text_blocks) and text_blocks[i + 1].startswith("Country:"):
            company = line
            country = text_blocks[i + 1].replace("Country:", "").strip()
            website = ""
            if i + 2 < len(text_blocks) and text_blocks[i + 2].startswith("www."):
                website = "https://" + text_blocks[i + 2]
                i += 3
            else:
                i += 2

            # Try to find email in raw HTML near this company (regex)
            emails_found = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', r.text)
            email = next((e for e in dict.fromkeys(emails_found) if not any(s in e for s in SKIP_EMAIL)), "")

            records.append({
                "Company Name": company,
                "Country": country,
                "Phone": "",
                "Email": email,
                "Website": website,
                "Hall": "",
                "Stand": "",
                "Profile URL": URL,
            })
        else:
            i += 1

    cols = ["Company Name", "Country", "Phone", "Email", "Website", "Hall", "Stand", "Profile URL"]
    df = pd.DataFrame(records, columns=cols)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Done. Saved {len(df)} rows → {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape()
