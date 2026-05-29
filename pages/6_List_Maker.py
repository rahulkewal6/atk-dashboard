import streamlit as st
import pandas as pd
from utils.scraper import (
    fetch_page, find_next_page_url, extract_exhibitors,
    enrich_missing_websites, enrich_detail_pages, rows_to_df, df_to_excel_bytes,
)
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

st.set_page_config(page_title="List Maker", page_icon="🕷️", layout="wide")
inject_css()
require_login()
show_logo()
show_user_bar()

st.title("🕷️ List Maker")
st.markdown("Paste any exhibitor list URL — Gemini scrapes every page and returns a downloadable Excel sheet.")

# ── API key check ─────────────────────────────────────────────────────────────
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    st.error(
        "**Gemini API key not configured.**  \n"
        "1. Go to [aistudio.google.com](https://aistudio.google.com) → **Get API key**  \n"
        "2. Copy the key  \n"
        "3. Add it to Streamlit Cloud secrets as: `GEMINI_API_KEY = \"your-key-here\"`  \n\n"
        "_Gemini 1.5 Flash is completely free (15 requests/min, 1M tokens/day)._"
    )
    st.stop()

st.markdown("---")

# ── INPUT FORM ────────────────────────────────────────────────────────────────
c1, c2 = st.columns([3, 1])
with c1:
    url = st.text_input(
        "Exhibitor list URL *",
        placeholder="https://www.adipec.com/exhibitors/",
        key="lm_url",
    )
with c2:
    max_pages = st.number_input(
        "Max pages (safety cap)",
        min_value=1, max_value=100, value=30,
        help=(
            "Gemini auto-detects the next page URL from each page's content — "
            "this is just a safety cap so the scraper doesn't run forever. "
            "Set it higher than the number of pages you expect."
        ),
        key="lm_pages",
    )

instructions = st.text_area(
    "📝 Page notes — describe the page structure to get better results",
    placeholder=(
        "Examples:\n"
        "• Exhibitor names are listed with country and stand number — 10 per page, pagination at the bottom\n"
        "• Each company has a clickable card — details (email, phone, website) are only on the individual company page\n"
        "• The page loads more companies as you scroll (infinite scroll)\n"
        "• Company names are in a table with columns: Name, Country, Stand, Hall\n"
        "• Only company names shown — no contact details on this page"
    ),
    height=130,
    key="lm_notes",
)

col_enrich, col_detail, col_warn = st.columns([1, 1, 1])
with col_enrich:
    do_enrich = st.checkbox(
        "🔍 Search for missing website URLs",
        help="For companies without a website listed, Jina.ai search finds the official site. ~3 sec per company.",
        key="lm_enrich",
    )
with col_detail:
    do_detail = st.checkbox(
        "🔗 Follow company pages for contact info",
        help=(
            "Fetches each company's individual profile page to get email, phone, website and country. "
            "Uses 15 concurrent requests. ~1 min per 200 companies."
        ),
        key="lm_detail",
    )
with col_warn:
    if do_detail:
        st.caption("⏱️ ~1 min per 200 companies. For large shows (2,000+ exhibitors) expect 10–15 min.")
    elif do_enrich:
        st.caption("⏱️ ~3 sec per company with a missing website.")

st.markdown("---")

with st.expander("ℹ️ What this tool can and can't do"):
    st.markdown("""
**Works great:**
- Standard HTML exhibitor lists (tables, cards, grids)
- JavaScript/React-rendered pages — handled automatically by Jina.ai
- Infinite scroll — Jina.ai auto-scrolls before returning content
- **Any pagination pattern** — Gemini reads each page and finds the real "Next" link, no guessing

**Partial support:**
- Pages where you must click each exhibitor for their details (email, phone).
  The tool will capture names/countries from the listing page. Add a note above describing this.

**Not supported:**
- Login-required pages
- Bot-protected / Captcha pages (Cloudflare, PerimeterX)
""")

# ── SCRAPE BUTTON ─────────────────────────────────────────────────────────────
if st.button("🕷️  Scrape & Extract", type="primary", disabled=not url):

    all_rows = []
    page_counts = []          # track how many companies per page for verification
    visited_urls = set()      # duplicate-page guard
    current_url = url.strip()
    base_url = url.strip()

    with st.status("Working…", expanded=True) as status:

        for page_num in range(1, max_pages + 1):

            # Guard: don't re-fetch the same URL (loop detection)
            if current_url in visited_urls:
                st.write(f"   🔁 Loop detected — same URL returned again. Stopping.")
                break
            visited_urls.add(current_url)

            st.write(f"📄 Page {page_num}: `{current_url}`")
            content, err = fetch_page(current_url)

            if err:
                st.warning(f"   ⚠️ Could not fetch: {err}")
                break
            if not content.strip():
                st.warning(f"   ⚠️ Empty response.")
                break

            st.write(f"   ✅ {len(content):,} chars received")
            st.write(f"   🤖 Extracting exhibitors…")

            rows, extract_err, gemini_has_more = extract_exhibitors(
                content, current_url, instructions, api_key
            )
            if extract_err:
                st.error(f"   ❌ Extraction error: {extract_err}")
                break

            page_counts.append(len(rows))
            all_rows.extend(rows)
            st.write(f"   ✅ **{len(rows)} companies** extracted from page {page_num} "
                     f"(running total: {len(all_rows)})")

            # Find real next page URL using Gemini
            next_url = find_next_page_url(content, current_url, base_url, api_key)

            if not next_url:
                st.write(f"   🏁 No next page found — all pages scraped.")
                break
            if next_url == current_url:
                st.write(f"   🏁 Next page URL identical — end of pagination.")
                break

            current_url = next_url

        # ── Deduplicate ──────────────────────────────────────────────────────
        seen = set()
        deduped = []
        for r in all_rows:
            key = r.get("company_name", "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(r)
            elif not key:
                deduped.append(r)

        duplicates_removed = len(all_rows) - len(deduped)
        if duplicates_removed:
            st.write(f"🧹 Removed {duplicates_removed} duplicates → **{len(deduped)} unique companies**")

        # ── Detail page enrichment ───────────────────────────────────────────
        if do_detail and deduped:
            detail_count = sum(
                1 for r in deduped if r.get("detail_url", "").strip().startswith("http")
            )
            if detail_count:
                st.write(f"🔗 Fetching {detail_count} company detail pages (15 concurrent)…")
                detail_placeholder = st.empty()
                detail_bar = st.progress(0.0)

                from urllib.parse import urlparse
                site_domain = urlparse(base_url).netloc

                def _detail_cb(done, total, name):
                    detail_placeholder.caption(f"   ✓ {done}/{total} — {name}")
                    detail_bar.progress(done / total)

                deduped = enrich_detail_pages(
                    deduped, api_key,
                    site_domain=site_domain,
                    progress_callback=_detail_cb,
                )
                detail_placeholder.empty()
                detail_bar.empty()

                emails_found = sum(1 for r in deduped if r.get("email"))
                webs_found   = sum(1 for r in deduped if r.get("website"))
                st.write(f"   ✅ Detail enrichment done — "
                         f"**{emails_found} emails**, **{webs_found} websites** found")
            else:
                st.write("   ℹ️ No detail page URLs found in the listing. "
                         "Add a note above describing that company names are clickable links.")

        # ── Website enrichment ────────────────────────────────────────────────
        if do_enrich and deduped:
            missing_count = sum(1 for r in deduped if not r.get("website"))
            if missing_count:
                st.write(f"🔍 Searching for {missing_count} missing website URLs…")
                placeholder = st.empty()

                def _cb(name):
                    placeholder.caption(f"   Searching: {name}")

                deduped = enrich_missing_websites(deduped, progress_callback=_cb)
                placeholder.empty()
                found = sum(1 for r in deduped if r.get("website"))
                st.write(f"   ✅ Websites found: {found} / {len(deduped)}")

        if not deduped:
            status.update(label="⚠️ No exhibitors found", state="error")
            st.warning(
                "No exhibitors were extracted. Try:\n"
                "- Adding page notes above describing the page structure\n"
                "- Checking if the page requires login or has bot protection"
            )
        else:
            df = rows_to_df(deduped)
            st.session_state["lm_df"] = df
            st.session_state["lm_page_counts"] = page_counts
            status.update(
                label=f"✅ Done — {len(df)} unique companies across {len(page_counts)} page(s)",
                state="complete",
            )

# ── RESULTS ───────────────────────────────────────────────────────────────────
if "lm_df" in st.session_state:
    df = st.session_state["lm_df"]
    page_counts = st.session_state.get("lm_page_counts", [])

    st.markdown("---")
    st.subheader(f"📋 {len(df)} Unique Companies Extracted")

    # Per-page count — lets user verify nothing was missed
    if len(page_counts) > 1:
        with st.expander(f"📊 Companies per page — verify completeness ({len(page_counts)} pages scraped)"):
            pc_df = pd.DataFrame({
                "Page": [f"Page {i+1}" for i in range(len(page_counts))],
                "Companies found": page_counts,
            })
            st.dataframe(pc_df, use_container_width=True, hide_index=True)
            st.caption(
                "Cross-check these counts against the website to confirm nothing was missed. "
                "If a page shows 0 companies, that page may have failed to load."
            )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Companies", len(df))
    m2.metric("With Email",
              int(df["Email"].str.contains("@", na=False).sum()) if "Email" in df.columns else 0)
    m3.metric("With Phone",
              int((df["Phone"].astype(str).str.len() > 3).sum()) if "Phone" in df.columns else 0)
    m4.metric("With Website",
              int(df["Website"].str.startswith("http", na=False).sum()) if "Website" in df.columns else 0)

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button(
            "⬇️ Download Excel",
            data=df_to_excel_bytes(df),
            file_name="exhibitors.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )
    with dl2:
        st.download_button(
            "⬇️ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="exhibitors.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl3:
        if st.button("🗑️ Clear results", use_container_width=True):
            del st.session_state["lm_df"]
            if "lm_page_counts" in st.session_state:
                del st.session_state["lm_page_counts"]
            st.rerun()
