"""
Light Middle East 2026 — Exhibitor Scraper
Output: /Users/deepakkewal/Desktop/NEW light_middle_east_exhibitors.xlsx
"""

import asyncio
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://light-middle-east.ae.messefrankfurt.com"
LIST_URL = BASE_URL + "/dubai/en/exhibitor-search.html?page={page}&pagesize=90"
TOTAL_PAGES = 4
OUTPUT_FILE = "/Users/deepakkewal/Desktop/NEW light_middle_east_exhibitors.xlsx"

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
SKIP_DOMAINS = {"messefrankfurt.com", "facebook.com", "instagram.com", "linkedin.com",
                "youtube.com", "twitter.com", "x.com", "vk.com", "xing.com", "wa.me", "line.me", "conzoom-circle"}
SKIP_EMAIL = {"messefrankfurt.com", "sentry.io", "w3.org", "example.com"}


async def collect_exhibitor_urls() -> list[str]:
    urls = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for pg in range(1, TOTAL_PAGES + 1):
            print(f"  Page {pg}/{TOTAL_PAGES}...", flush=True)
            await page.goto(LIST_URL.format(page=pg), wait_until="networkidle", timeout=30000)
            links = await page.eval_on_selector_all(
                'a[href*="detail"]',
                "els => els.map(e => e.href.split('#')[0])"
            )
            urls.extend(links)
            await asyncio.sleep(1)
        await browser.close()

    seen, deduped = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    print(f"  → {len(deduped)} unique exhibitors found\n")
    return deduped


def parse_detail(url: str) -> dict:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return {"Company Name": "", "Country": "", "Phone": "", "Email": "",
                "Website": "", "Hall": "", "Stand": "", "Profile URL": url, "Error": str(e)}

    soup = BeautifulSoup(r.text, "html.parser")

    def sel(css):
        el = soup.select_one(css)
        return el.get_text(strip=True) if el else ""

    company = sel("h1")

    addr_el = soup.select_one(".ex-contact-box__address-field-full-address")
    country = ""
    if addr_el:
        lines = [s.strip() for s in addr_el.get_text("\n").split("\n") if s.strip()]
        country = lines[-1] if lines else ""

    phone_el = soup.select_one("a.ex-contact-box__address-field-tel-number")
    phone = phone_el.get_text(strip=True) if phone_el else ""

    emails_found = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', r.text)
    email = next((e for e in dict.fromkeys(emails_found) if not any(s in e for s in SKIP_EMAIL)), "")

    website = ""
    for a in soup.find_all("a", string=lambda t: t and "website" in t.lower()):
        href = a.get("href", "")
        if href.startswith("http") and not any(d in href for d in SKIP_DOMAINS):
            website = href
            break

    hall = sel(".ex-contact-box__container-location-category")
    hall_num = sel(".ex-contact-box__container-location-hall")
    stand = sel(".ex-contact-box__container-location-stand")
    hall_full = f"{hall} {hall_num}".strip() if hall or hall_num else ""

    return {
        "Company Name": company, "Country": country, "Phone": phone,
        "Email": email, "Website": website, "Hall": hall_full,
        "Stand": stand, "Profile URL": url,
    }


def export(records):
    cols = ["Company Name", "Country", "Phone", "Email", "Website", "Hall", "Stand", "Profile URL"]
    pd.DataFrame(records, columns=cols).to_excel(OUTPUT_FILE, index=False)
    print(f"\nDone. Saved {len(records)} rows → {OUTPUT_FILE}")


async def main():
    print("Step 1: Collecting exhibitor URLs (4 pages)...")
    urls = await collect_exhibitor_urls()
    print("Step 2: Scraping detail pages...")
    records = []
    for i, url in enumerate(urls, 1):
        print(f"  [{i}/{len(urls)}] {url.split('/')[-1][:50]}")
        records.append(parse_detail(url))
        time.sleep(0.4)
    print("\nStep 3: Exporting...")
    export(records)


if __name__ == "__main__":
    asyncio.run(main())
