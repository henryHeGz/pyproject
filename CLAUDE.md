# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web scraper that uses Playwright to collect Chinese tax law and regulation data from the 国家税务总局法规库 (State Taxation Administration Legal Database) and 留言公开 (Public Comments). The scrapers store data in a database (PostgreSQL or SQLite) with automatic deduplication. A web management interface provides task management and CSV export functionality.

## Development Commands

### Installation
```bash
pip install -e .
playwright install
```

### Running the web management interface
```bash
# Start the FastAPI web server
python web_app.py

# Access the web interface at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### Running scrapers directly
```bash
# Run 法律法规 scraper
python flfg_scraper/chinatax_scraper.py --start-page 1 --page-count 5

# Run 留言公开 scraper
python comments_scraper/chinatax_comments_scraper.py --start-page 1 --max-pages 5
```

### Testing
```bash
# Run all tests
python -m unittest discover tests

# Run specific test module
python -m unittest tests.test_scraper
```

## Architecture

### Core Components

**Web Application ([web_app.py](web_app.py)):**
- FastAPI-based management interface for all scraping tasks
- Task management with database persistence
- CSV export functionality with unique file naming
- Background task execution for long-running operations

**CSV File Management ([csv_manager.py](csv_manager.py)):**
- Centralized CSV file path generation and management
- All CSV exports stored in `csv_exports/` directory
- Unique filename format: `{task_name}_{YYMMDDHHmmss}_{4-char-random}.csv`
- Never stores CSV files in project root directory

**Database Layer ([db_config.py](db_config.py)):**
- Supports both PostgreSQL and SQLite
- Auto-detection via `DB_TYPE` environment variable
- Provides `get_db_cursor()` context manager for all database operations

**法律法规 Scraper ([flfg_scraper/chinatax_scraper.py](flfg_scraper/chinatax_scraper.py)):**
- Extracts from `<li>` structure on list pages
- Uses MD5 hash of (title + document_no + publish_date + link) as unique ID
- Stores records directly to `flfg_records` database table
- Supports pagination and incremental updates

**留言公开 Scraper ([comments_scraper/chinatax_comments_scraper.py](comments_scraper/chinatax_comments_scraper.py)):**
- Extracts comment list and detail pages
- Uses MD5 hash of (question + date + link) as unique ID
- Stores records directly to `comment_records` database table
- Auto-download option for fetching full comment content

### Data Model

**Record (法律法规):**
- `id` (MD5 hash): Unique identifier
- `title`: Document title
- `document_no`: Official document number
- `publish_date`: Publication date
- `link`: Full URL to document
- `downloaded`: Status flag ("Y" or "N")

**CommentRecord (留言公开):**
- `id` (MD5 hash): Unique identifier
- `question`: Comment title/question
- `date`: Comment date
- `link`: Full URL to comment
- `downloaded`: Status flag ("Y" or "N")
- `question_content`: Full question text
- `answer_content`: Official answer text

### Deduplication Strategy

- Database-driven: `load_existing_keys()` / `load_existing_ids()` query existing records
- MD5 hash-based unique IDs prevent duplicate insertions
- Scraper stops when duplicate records are encountered (incremental mode)

### CSV Export System

**Location:** All CSV files are stored in `csv_exports/` directory (never in project root)

**Naming Convention:** `{task_name}_{timestamp}_{random}.csv`
- `task_name`: Descriptive task identifier (e.g., "flfg", "comments", "export_法律法规")
- `timestamp`: YYMMDDHHmmss format
- `random`: 4-character alphanumeric suffix for uniqueness

**Example filenames:**
- `flfg_25101708304_a3f2.csv`
- `comments_251017083512_x9k1.csv`
- `export_法律法规_251017084235_k7m3.csv`

**Usage:**
```python
from csv_manager import get_csv_path, list_csv_files, CSV_EXPORTS_DIR

# Generate new CSV path
csv_path = get_csv_path("my_task")  # Returns: csv_exports/my_task_251017083045_x7a2.csv

# List all CSV files
files = list_csv_files()  # Returns sorted list by modification time

# Get latest CSV for specific task
latest = get_latest_csv("flfg")
```

## Important Implementation Details

- **Database persistence:** All scraped data stored in database, not CSV files
- **CSV exports:** Only used for user downloads, generated on-demand with unique filenames
- **Type checking:** Uses `TYPE_CHECKING` guard for Playwright imports
- **Error handling:** Comprehensive exception handling with user-friendly messages
- **Async execution:** All scraping operations are async using `asyncio`
- **Background tasks:** FastAPI BackgroundTasks for non-blocking operations
- **Auto-detection:** Database type auto-detected from environment
