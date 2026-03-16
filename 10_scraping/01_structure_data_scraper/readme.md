# AI Web Scraper — Prototype

Extract structured data from any webpage using an LLM and save it to Excel. No cloud services, no complex auth — just Python, an API key, and a target URL.

---

## What It Does

1. Loads a target page via a headless browser (Crawl4AI + Playwright)
2. Sends the rendered HTML to an LLM with a schema-constrained prompt
3. Parses the response into structured records using a Pydantic model
4. Saves results to a timestamped `.xlsx` file in the `output/` folder

**Current target:** `books.toscrape.com` — a public scraping sandbox  
**Extracts:** title, price, star rating, availability (up to 10 records)

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and add your key:

```
OPENAI_API_KEY=sk-...
```

### 3. Run

```bash
python prototype.py
```

**Expected output:**

```
🔍 Scraping books.toscrape.com …

✅ Extracted 10 books:

   1. A Light in the Attic                          £51.77     ★ Three
   2. Tipping the Velvet                            £53.74     ★ One
   ...

💾 Saved → output/scrape_2024-03-04_1430.xlsx  (18s)
```

---

## Project Structure

```
.
├── prototype.py          # Single-file scraper (core logic)
├── requirements.txt      # Python dependencies
├── .env.example          # API key template
└── output/
    └── scrape_[timestamp].xlsx   # Generated on each run
```

---

## Configuration

### Switch to Gemini

Change lines 27–28 in `prototype.py`:

```python
provider="gemini/gemini-1.5-flash",
api_token=os.getenv("GEMINI_API_KEY"),
```

And update `.env`:

```
GEMINI_API_KEY=AIza...
```

### Change the target URL

Update the `url` in `scrape_books()` and adjust the `Book` model fields and extraction `instruction` to match your target page.

---

## Dependencies

| Package | Purpose |
|---|---|
| `crawl4ai` | Headless browser + LLM extraction |
| `pandas` | DataFrame handling |
| `openpyxl` | Excel file export |
| `python-dotenv` | API key management |

---

## Roadmap

This prototype proves the **AI extraction → local file** pipeline. Planned next steps:

- [ ] Add 2nd and 3rd target sites
- [ ] Swap LLM extraction for CSS selectors where possible (cost reduction)
- [ ] Add Browser-Use for complex multi-step navigation
- [ ] Implement batching and resume logic for 10k+ records
- [ ] Optional: Google Sheets export

---

## Troubleshooting

**No records extracted**
- Verify your API key is set correctly in `.env`
- Run `playwright install chromium` if not already done
- Check that the target URL is publicly accessible

**`ModuleNotFoundError`**
- Run `pip install -r requirements.txt` again
- Ensure you're using Python 3.10+

**Slow runtime**
- `gpt-4o-mini` is the fastest/cheapest option; `gemini-1.5-flash` is comparable
- LLM latency dominates — 10 records typically completes in 15–30s