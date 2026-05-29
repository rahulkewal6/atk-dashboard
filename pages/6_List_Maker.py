import streamlit as st
import pandas as pd
from utils.scraper import (
    fetch_page, paginate_url, extract_exhibitors,
    enrich_missing_websites, rows_to_df, df_to_excel_bytes,
)
from utils.branding import inject_css, show_logo
from utils.auth import require_login, show_user_bar

st.set_page_config(page_title="List Maker", page_icon="🕷️", layout="wide")
inject_css()
require_login()
show_logo()
show_user_bar()

st.title("🕷️ List Maker")
st.markdown("Paste any exhibitor list URL — Claude reads the page and returns a downloadable Excel sheet.")

# ── API key check ─────────────────────────────────────────────────────────────
api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
if not api_key:
    st.error(
        "**Claude API key not configured.** "
        "Add `ANTHROPIC_API_KEY` to your Streamlit Cloud secrets to enable this feature.  \n"
        "Get a free key at [console.anthropic.com](https://console.anthropic.com)."
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
        "Pages to scrape",
        min_value=1, max_value=30, value=1,
        help="If the list has pagination (page 1, 2, 3…), set how many pages to fetch.",
        key="lm_pages",
    )

instructions = st.text_area(
    "📝 Page notes — tell Claude what this page looks like (optional but helps a lot)",
    placeholder=(
        "Examples:\n"
        "• Each exhibitor has a clickable card — details (email, phone) are on the individual page\n"
        "• The page loads more companies as you scroll down (infinite scroll)\n"
        "• Pagination at the bottom — set 'Pages to scrape' above\n"
        "• Only company names are shown; no contact details on this page\n"
        "• Company names are in a table with columns: Name, Country, Stand, Hall"
    ),
    height=130,
    key="lm_notes",
)

col_enrich, col_warn = st.columns([1, 2])
with col_enrich:
    do_enrich = st.checkbox(
        "🔍 Search for missing website URLs",
        help="For companies without a website listed, uses Jina.ai search to find one. Adds a few seconds per company.",
        key="lm_enrich",
    )
with col_warn:
    if do_enrich:
        st.caption("⏱️ This adds ~3–5 seconds per company with a missing website. For large lists, uncheck this and enrich later.")

st.markdown("---")

# ── LIMITATION NOTE ───────────────────────────────────────────────────────────
with st.expander("ℹ️ What this tool can and can't do"):
    st.markdown("""
**Works great:**
- Standard HTML exhibitor lists (tables, cards, grids)
- JavaScript/React-rendered pages (handled by Jina.ai)
- Infinite scroll pages (Jina.ai auto-scrolls)
- Paginated lists — set the page count above

**Partial support:**
- Pages where you click each exhibitor for details — the tool extracts names from the listing page, but can't automatically click through to each detail page. Add a note above to let Claude know, and it will extract what's visible.

**Not supported:**
- Login-required pages
- Bot-protected / Captcha pages (Cloudflare, PerimeterX)
""")

# ── SCRAPE BUTTON ─────────────────────────────────────────────────────────────
if st.button("🕷️  Scrape & Extract", type="primary", disabled=not url):

    all_rows = []
    has_more_hint = False

    with st.status("Working…", expanded=True) as status:

        for page_num in range(1, max_pages + 1):
            page_url = paginate_url(url, page_num)
            st.write(f"📄 Fetching page {page_num}: `{page_url}`")

            content, err = fetch_page(page_url)
            if err:
                st.warning(f"Could not fetch page {page_num}: {err}")
                break
            if not content.strip():
                st.warning(f"Page {page_num} returned empty content.")
                break

            st.write(f"   ✅ {len(content):,} characters received")
            st.write(f"🤖 Extracting exhibitors from page {page_num}…")

            rows, extract_err, page_has_more = extract_exhibitors(
                content, page_url, instructions, api_key
            )
            if extract_err:
                st.error(f"Extraction error on page {page_num}: {extract_err}")
                break

            st.write(f"   ✅ {len(rows)} exhibitors found on page {page_num}")
            all_rows.extend(rows)

            if page_has_more and page_num < max_pages:
                st.write(f"   ↪️ More pages detected — continuing…")
            elif not page_has_more and page_num > 1:
                st.write(f"   🏁 No more pages detected.")
                break

        # Deduplicate by company name
        seen = set()
        deduped = []
        for r in all_rows:
            key = r.get("company_name", "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(r)
            elif not key:
                deduped.append(r)  # Keep rows with no name (might have other data)

        st.write(f"🧹 Deduplicated: {len(all_rows)} → {len(deduped)} unique companies")

        # Website enrichment
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
            else:
                st.write("   ✅ All companies already have website URLs.")

        if not deduped:
            status.update(label="⚠️ No exhibitors found", state="error")
            st.warning(
                "No exhibitors were extracted. Try:\n"
                "- Adding page notes above describing the page structure\n"
                "- Increasing 'Pages to scrape' if it's a paginated list\n"
                "- Checking if the page requires login or has bot protection"
            )
        else:
            df = rows_to_df(deduped)
            st.session_state["lm_df"] = df
            status.update(
                label=f"✅ Done — {len(df)} exhibitors extracted",
                state="complete",
            )

# ── RESULTS ───────────────────────────────────────────────────────────────────
if "lm_df" in st.session_state:
    df = st.session_state["lm_df"]

    st.markdown("---")
    st.subheader(f"📋 {len(df)} Exhibitors")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", len(df))
    m2.metric("With Email",
              int(df["Email"].str.contains("@", na=False).sum()) if "Email" in df.columns else 0)
    m3.metric("With Phone",
              int((df["Phone"].str.len() > 3).sum()) if "Phone" in df.columns else 0)
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
            st.rerun()
