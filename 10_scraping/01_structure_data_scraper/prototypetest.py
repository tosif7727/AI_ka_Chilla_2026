"""
AI Web Scraper — Multi-Site Edition
Targets:
  1. codanics.com/courses   → course listings (title, url, free/paid, category)
  2. ai.upalerts.app        → SaaS plans (title, plan, price, free/paid, contact)
  3. manus.im/pricing       → AI tool plans (title, plan, price, free/paid, contact)

Extracts: title, location/url, contact, free_or_paid, plan, price
Saves to: output/scrape_[timestamp].xlsx  (one sheet per site)
"""

import asyncio
import json
import os
from datetime import datetime

import pandas as pd
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
try:
    from crawl4ai import LLMConfig          # crawl4ai >= 0.4.3
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
        "url": "https://ai.upalerts.app/",
        "instruction": (
            "Extract all pricing plans or product tiers on this page. For each plan capture: "
            "title (product or plan name), url (signup or product link), "
            "contact (any email, phone, or support link visible), "
            "location ('Online, Global'), "
            "free_or_paid ('Free' / 'Paid' / 'Freemium'), "
            "plan (tier name e.g. 'Starter', 'Pro', 'Enterprise'), "
            "price (exact price string or 'Free')."
        ),
    },
    {
        "name": "Manus",
        "url": "https://manus.im/pricing",
        "instruction": (
            "Extract all pricing plans listed on this page. For each plan capture: "
            "title (plan or product name), url (signup link), "
            "contact (use 'contact@manus.im' or any visible contact), "
            "location ('Online, Global'), "
            "free_or_paid ('Free' / 'Paid' / 'Freemium'), "
            "plan (tier name e.g. 'Free', 'Pro', 'Team', 'Enterprise'), "
            "price (exact price string e.g. '$29/month' or 'Free')."
        ),
    },
]


# ── 3. Scrape one site ────────────────────────────────────────────────────────

async def scrape_site(site: dict) -> list[dict]:
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv("OPENAI_API_KEY"),
        ),
        schema=Listing.model_json_schema(),
        extraction_type="schema",
        instruction=site["instruction"],
    )

    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=site["url"], config=config)

    if not result.success:
        print(f"  ⚠️  Crawl failed for {site['name']}: {result.error_message}")
        return []

    try:
        raw = json.loads(result.extracted_content)
    except json.JSONDecodeError:
        print(f"  ⚠️  JSON parse error for {site['name']}")
        return []

    records = raw if isinstance(raw, list) else raw.get("items", raw.get("listings", [raw]))

    valid_fields = set(Listing.model_fields.keys())
    cleaned = []
    for r in records:
        if isinstance(r, dict) and "title" in r:
            cleaned.append({k: str(v) for k, v in r.items() if k in valid_fields})

    return cleaned[:10]


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
        print(f"  → Scraping {site['name']} ({site['url']}) ...")
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