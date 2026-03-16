"""
AI Web Scraper Prototype
Target: books.toscrape.com (public scraping sandbox)
Extracts: book title, price, rating, availability
Saves to: output/scrape_[timestamp].xlsx
"""

import asyncio
import json
import os
from datetime import datetime

import pandas as pd
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMConfig
from pydantic import BaseModel
from typing import ForwardRef

# Explicitly resolve ForwardRef for LLMConfig
LLMConfig = ForwardRef("LLMConfig")


# ── 1. Data Model ────────────────────────────────────────────────────────────

class Book(BaseModel):
    title: str
    price: str
    rating: str
    availability: str


# ── 2. Scrape ────────────────────────────────────────────────────────────────

async def scrape_books() -> list[dict]:
    llm_config = LLMConfig(
        provider="openai/gpt-4o-mini",  # Replace with your preferred provider
        api_token=os.getenv("OPENAI_API_KEY"),
    )

    strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=Book.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract up to 10 books from this page. "
            "For each book capture: title, price (with £ symbol), "
            "star rating as a word (e.g. 'Three'), and availability status."
        ),
    )

    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com/catalogue/page-1.html",
            config=config,
        )

    if not result.success:
        raise RuntimeError(f"Crawl failed: {result.error_message}")

    raw = json.loads(result.extracted_content)

    # Normalize: handle both list and {"items": [...]} shapes
    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        records = raw.get("items", raw.get("books", [raw]))
    else:
        records = []

    # Keep only valid Book records (drop error/metadata entries)
    books = []
    for r in records:
        if isinstance(r, dict) and "title" in r:
            books.append({k: str(v) for k, v in r.items() if k in Book.model_fields})

    return books[:10]  # cap at 10


# ── 3. Save ───────────────────────────────────────────────────────────────────

def save_to_excel(records: list[dict]) -> str:
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filepath = f"output/scrape_{timestamp}.xlsx"

    df = pd.DataFrame(records)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Books")

        # Auto-size columns
        ws = writer.sheets["Books"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) + 4
            ws.column_dimensions[col[0].column_letter].width = min(max_len, 50)

    return filepath


# ── 4. Main ───────────────────────────────────────────────────────────────────

async def main():
    print("🔍 Scraping books.toscrape.com …")
    start = datetime.now()

    books = await scrape_books()

    if not books:
        print("⚠️  No records extracted. Check your API key or page structure.")
        return

    print(f"\n✅ Extracted {len(books)} books:\n")
    for i, b in enumerate(books, 1):
        print(f"  {i:>2}. {b.get('title', 'N/A'):<45} {b.get('price', ''):<10} ★ {b.get('rating', '')}")

    filepath = save_to_excel(books)
    elapsed = (datetime.now() - start).seconds
    print(f"\n💾 Saved → {filepath}  ({elapsed}s)")


if __name__ == "__main__":
    asyncio.run(main())
