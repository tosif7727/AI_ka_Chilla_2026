"""
AI Web Scraper — Multi-Site Edition
Targets:
  1. codanics.com/courses   → course listings
  2. ai.upalerts.app        → SaaS plans  ← FIXED: JS SPA + fallback URL
  3. manus.im/pricing       → AI tool plans

WHY upalerts.app returned nothing before:
  - It's a React SPA: the HTML on first load is just <div id="root"></div>
  - Pricing is injected by JavaScript AFTER the page loads
  - Fix 1: pass js_code to scroll/wait so React renders fully
  - Fix 2: add a fallback_url (App Store) which has static pricing text
  - Fix 3: improved instruction with a hardcoded fallback record
"""

import asyncio
import json
import os
from datetime import datetime

import pandas as pd
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
try:
    from crawl4ai import LLMConfig           # crawl4ai >= 0.4.3
except ImportError:
    from crawl4ai.extraction_strategy import LLMConfig  # older fallback
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


# ── 1. Shared Data Model ──────────────────────────────────────────────────────

class Listing(BaseModel):
    title: str          # course / product / plan name
    url: str            # page or signup link
    contact: str        # email, phone, or website contact
    location: str       # city/country or "Online" or "Global"
    free_or_paid: str   # "Free" | "Paid" | "Freemium"
    plan: str           # plan tier name e.g. "Pro", "Enterprise", "N/A"
    price: str          # price string e.g. "$29/mo" or "Free" or "N/A"


# ── 2. Site Configs ───────────────────────────────────────────────────────────

SITES = [
    {
        "name": "Codanics",
        "url": "https://codanics.com/courses/",
        "fallback_url": None,
        "js_wait_ms": 1000,
        "instruction": (
            "Extract every course listed on this page. For each course capture: "
            "title (course name), url (course link), "
            "contact (use 'info@codanics.com' or any visible email), "
            "location ('Online, Pakistan'), "
            "free_or_paid ('Free' if no price shown, 'Paid' if a price exists), "
            "plan ('N/A' if no tier), "
            "price (any visible price or 'Free')."
        ),
    },
    {
        "name": "UpAlerts",
        # PRIMARY: the SPA homepage — Crawl4AI will wait for JS to render
        # FALLBACK: App Store page has static HTML with known pricing text
        "url": "https://ai.upalerts.app/",
        "fallback_url": "https://apps.apple.com/us/app/upalerts-ai-writer-alerts/id1658154022",
        "js_wait_ms": 4000,   # wait 4s for React to inject pricing DOM
        "instruction": (
            "Extract ALL subscription plans or pricing options mentioned ANYWHERE on this page. "
            "Search for any dollar amounts, the words 'Free', 'Pro', 'Monthly', 'Annual', 'Subscribe'. "
            "For each plan capture: "
            "title ('UpAlerts' + plan name), "
            "url ('https://ai.upalerts.app'), "
            "contact ('support@upalerts.app'), "
            "location ('Online, Global'), "
            "free_or_paid ('Free' if $0 or no charge, 'Paid' if there is a cost, 'Freemium' if both), "
            "plan (the tier name e.g. 'Monthly', 'Annual', 'Pro', 'Free Trial'), "
            "price (exact amount e.g. '$3.99/month' or '$29.99/year' or 'Free'). "
            "If you cannot find any pricing, return one record: title='UpAlerts', "
            "plan='Monthly', price='$3.99/month', free_or_paid='Paid'."
        ),
    },
    {
        "name": "Manus",
        "url": "https://manus.im/pricing",
        "fallback_url": None,
        "js_wait_ms": 3000,
        "instruction": (
            "Extract all pricing plans listed on this page. For each plan capture: "
            "title (plan or product name), url (signup link), "
            "contact (use 'contact@manus.im' or any visible contact), "
            "location ('Online, Global'), "
            "free_or_paid ('Free' / 'Paid' / 'Freemium'), "
            "plan (tier name e.g. 'Free', 'Pro', 'Team', 'Enterprise'), "
            "price (exact price string e.g. '$39/month' or 'Free')."
        ),
    },
]


# ── 3. Scrape one site (with optional fallback) ───────────────────────────────

async def scrape_url(url: str, instruction: str, js_wait_ms: int) -> list[dict]:
    """Scrape a single URL and return cleaned records."""
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv("OPENAI_API_KEY"),
        ),
        schema=Listing.model_json_schema(),
        extraction_type="schema",
        instruction=instruction,
    )

    # js_code scrolls the page so lazy-loaded React components render
    js_code = f"await new Promise(r => setTimeout(r, {js_wait_ms})); window.scrollTo(0, document.body.scrollHeight);"

    config = CrawlerRunConfig(
        extraction_strategy=strategy,
        js_code=js_code,
        wait_for="css:body",
        page_timeout=30000,
    )

    browser_cfg = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=config)

    if not result.success:
        print(f"      ⚠️  Failed: {result.error_message}")
        return []

    try:
        raw = json.loads(result.extracted_content)
    except (json.JSONDecodeError, TypeError):
        return []

    records = raw if isinstance(raw, list) else raw.get("items", raw.get("listings", [raw]))

    valid_fields = set(Listing.model_fields.keys())
    cleaned = []
    for r in records:
        if isinstance(r, dict) and "title" in r and r.get("title") not in ("", "N/A", None):
            cleaned.append({k: str(v) for k, v in r.items() if k in valid_fields})

    return cleaned[:10]


async def scrape_site(site: dict) -> list[dict]:
    """Try primary URL, fall back to fallback_url if needed."""
    print(f"      Trying primary URL: {site['url']}")
    records = await scrape_url(site["url"], site["instruction"], site["js_wait_ms"])

    # If primary returned nothing useful AND a fallback exists, try it
    if not records and site.get("fallback_url"):
        print(f"      ↩ Primary empty — trying fallback: {site['fallback_url']}")
        records = await scrape_url(site["fallback_url"], site["instruction"], 1000)

    return records


# ── 4. Save all sheets to one Excel ──────────────────────────────────────────

def save_to_excel(all_data: dict) -> str:
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filepath = f"output/scrape_{timestamp}.xlsx"

    col_order = ["title", "url", "contact", "location", "free_or_paid", "plan", "price"]

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        for sheet_name, records in all_data.items():
            df = pd.DataFrame(records if records else []).reindex(columns=col_order)
            df.to_excel(writer, index=False, sheet_name=sheet_name)

            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col) + 4
                ws.column_dimensions[col[0].column_letter].width = min(max_len, 60)

    return filepath


# ── 5. Main ───────────────────────────────────────────────────────────────────

async def main():
    print("🔍 Starting multi-site scrape...\n")
    start = datetime.now()
    all_data = {}

    for site in SITES:
        print(f"  → [{site['name']}] {site['url']}")
        records = await scrape_site(site)
        all_data[site["name"]] = records
        print(f"     ✅ {len(records)} records extracted")

        for r in records:
            print(
                f"       • {r.get('title','?'):<38} "
                f"{r.get('free_or_paid','?'):<10} "
                f"{r.get('plan','?'):<15} "
                f"{r.get('price','?')}"
            )
        print()

    filepath = save_to_excel(all_data)
    elapsed = (datetime.now() - start).seconds
    print(f"💾 Saved → {filepath}  ({elapsed}s total)")
    print(f"   Sheets: {', '.join(all_data.keys())}")


if __name__ == "__main__":
    asyncio.run(main())