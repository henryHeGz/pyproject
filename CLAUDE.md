# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web scraper that uses Playwright to collect Chinese tax law and regulation data from the 国家税务总局法规库 (State Taxation Administration Legal Database). The scraper downloads list data (title, document number, publication date) and saves it to CSV with automatic deduplication.

## Development Commands

### Installation
```bash
pip install .
playwright install
```

### Running the scraper
```bash
# Direct execution
python chinatax_scraper.py

# Or via console script entry point
chinatax-scraper

# With options
chinatax-scraper --csv output.csv --headed
```

### Testing
```bash
# Run all tests
python -m unittest tests/test_scraper.py

# Run specific test class
python -m unittest tests.test_scraper.RecordTests

# Run individual test
python -m unittest tests.test_scraper.RecordTests.test_csv_row_matches_order
```

## Architecture

The scraper is a single-module application ([chinatax_scraper.py](chinatax_scraper.py)) with the following core components:

**Data Model (`Record` dataclass):**
- Immutable container for scraped records (sequence, title, document_no, publish_date)
- `unique_key` property uses title + document number for deduplication (not sequence, since new rows can be inserted at the top of the list)

**Deduplication Strategy:**
- `load_existing_keys()` reads existing CSV and returns set of (title, document_no) tuples
- Main scrape loop checks each record's `unique_key` against seen keys before adding
- Only new records are appended to CSV

**Extraction Logic (`extract_records()`):**
- Primary strategy: extract from `<table><tbody><tr>` structure
- Fallback strategy: extract from `<li>` with `<span>` elements
- Both strategies filter out header rows (where 序号 column contains literal "序号")

**Pagination (`goto_next_page()`):**
- Locates "下一页" (Next Page) link
- Checks if disabled via class attribute or aria-disabled
- Clicks and waits for networkidle before continuing

**Main Flow (`scrape()`):**
1. Load existing keys from CSV (if file exists)
2. Launch Chromium browser
3. Visit BASE_URL and wait for networkidle
4. Extract records from current page, filter duplicates
5. Navigate to next page if available, repeat extraction
6. Close browser
7. Create CSV with headers if it doesn't exist
8. Append new records to CSV
9. Return count of newly added records

## Important Implementation Details

- **Type checking:** Uses `TYPE_CHECKING` guard for Playwright imports to avoid runtime dependency in type hints
- **Error handling:** Playwright import wrapped in try/except with localized error message
- **Network constraints:** README documents workarounds for restricted network environments (offline installation, proxies, mirrors)
- **CSV encoding:** Always uses UTF-8 with newline="" for cross-platform compatibility
- **Async execution:** All scraping logic is async, entry point uses `asyncio.run()`
