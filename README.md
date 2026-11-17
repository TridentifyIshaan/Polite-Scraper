# Polite Scraper

A robust, polite, and fault-tolerant web scraping pipeline built in Python. It downloads catalogue pages from [Books to Scrape](https://books.toscrape.com), visits book detail pages, normalizes messy HTML into clean, validated JSON records, survives broken pages without crashing, and generates an honest run report at the end of every run.

---

## 1. Target Classification

- **Target Site**: Books to Scrape (`https://books.toscrape.com`)
- **Purpose & Authorization**: Books to Scrape is an open educational sandbox specifically built and hosted for developers and students to safely practice web scraping without commercial consequences or copyright concerns.
- **Scope**: Exactly the first 3 catalogue pages, discovering and scraping all 60 book detail records.
- **Data Collected**:
  - `title`: Book title (string)
  - `product_url`: Canonical absolute URL to book detail page (string, starting with `https://`)
  - `price_text`: Raw price string with currency symbol (e.g., `£51.77`)
  - `price_gbp`: Normalized price as a numeric float (e.g., `51.77`)
  - `availability_text`: Raw stock availability status (e.g., `In stock (22 available)`)
  - `rating_text`: Star rating as textual representation (e.g., `Three`)
  - `description`: Book description text or `null` if omitted
  - `source_page`: Provenance URL of the originating catalogue page
  - `fetched_at`: UTC timestamp in ISO 8601 format when the page was fetched
- **Why this is appropriate**: Collecting a sample of 60 items from an explicit educational sandbox at low request rates causes negligible server load and aligns completely with the site's intended use.
- **Robots.txt Analysis**: A request to `https://books.toscrape.com/robots.txt` returned HTTP 404 (`no robots file found`). A missing `robots.txt` is not an implicit permission grant; our permission relies strictly on the site operator's explicit declaration that this is a practice sandbox for web scraping.

> **Ethics statement:**
> *"I will not reuse this code on another site without checking its rules and terms first."*

---

## 2. Quickstart & Run Command

Run the pipeline in under 5 minutes with a single copy-pasteable command:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python src/main.py
```

To run individual milestone checkpoints:
```bash
# Milestone 1: Fetch once, cache once
python src/main.py --stage 1

# Milestone 2: Discover 3 catalogue pages (60 books)
python src/main.py --stage 2

# Milestone 3: Extract raw records from detail pages
python src/main.py --stage 3

# Milestone 4: Normalize, validate schema, and store output/books.json
python src/main.py --stage 4

# Milestone 5: Fault-tolerance test with injected broken URL
python src/main.py --stage 5
```

---

## 3. Tech Stack & Installation

This project utilizes the Python stack:
- **Language**: Python 3.10+ (tested on Python 3.14)
- **HTTP Client**: `requests` (v2.34.2)
- **HTML Parser**: `beautifulsoup4` (v4.15.0)
- **Schema Validation**: `pydantic` (v2.14.3)
- **Testing**: `pytest` (v9.2.0)
- **Data Persistence**: Built-in `json` module

### Manual Installation
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

---

## 4. Record Schema

Each stored record conforms to the Pydantic `BookRecord` model:

| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `title` | `str` | Yes | Book title (non-empty string) | `"A Light in the Attic"` |
| `product_url` | `str` | Yes | Canonical absolute URL starting with `https://` | `"https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"` |
| `price_text` | `str` | Yes | Original price text with currency symbol | `"£51.77"` |
| `price_gbp` | `float` | Yes | Cleaned numeric price in GBP (>= 0.0) | `51.77` |
| `availability_text` | `str` | Yes | Raw stock availability string | `"In stock (22 available)"` |
| `rating_text` | `str` | Yes | Rating text | `"Three"` |
| `description` | `str \| null` | Optional | Book description text or null if absent | `"It's hard to imagine..."` |
| `source_page` | `str` | Yes | Catalogue page URL where discovered | `"https://books.toscrape.com/catalogue/page-1.html"` |
| `fetched_at` | `str` | Yes | ISO 8601 UTC timestamp of fetch | `"2026-11-17T11:47:40Z"` |

Records failing schema validation are diverted to `output/errors.json` with the failure reason and never written to `output/books.json`.

---

## 5. Politeness Rules

The scraper strictly adheres to respectful web scraping standards:
1. **Honest User-Agent**: Every request carries an identifying header:
   `FlyRankPoliteScraper/1.0 (+https://github.com/TridentifyIshaan/Polite-Scraper)`
2. **Rate Limiting**: Enforces a minimum delay of 500 ms (0.5s) between consecutive live requests to respect server capacity. Cached requests require no delay.
3. **Request Timeout**: All HTTP requests enforce a 10.0s timeout to prevent hanging connections.
4. **Local Disk Caching**: Responses are cached locally under `cache/`. Re-runs read from cache first, avoiding repeated traffic to the server.
5. **Strict Status Code & Retry Policy**:
   - Only HTTP 200 responses are treated as valid pages.
   - HTTP 404 (Not Found) and HTTP 403 (Forbidden) are terminal failures and are **never retried**.
   - HTTP 5xx (Server Errors) or connection timeouts are politely retried once with backoff or `Retry-After` adherence.

---

## 6. Architecture & Browser Decision

> **Browser assessment:**
> *The data is already in the HTML the server sends, so a browser would only add cost.*

Modern client-side browsers consume hundreds of megabytes of memory and CPU cycles executing JavaScript engines. Because Books to Scrape delivers complete server-side rendered HTML, a lightweight HTTP client with an HTML parser (Requests + BeautifulSoup) performs extraction in a fraction of the time and memory with zero headless browser overhead.

---

## 7. Run Proof & Evidence

Sample `output/run-report.json` generated from a verified run:

```json
{
  "start_time": "2026-11-17T11:47:40Z",
  "duration_seconds": 0.35,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

When a broken URL is encountered (tested via `--inject-fake-url` or `--stage 5`), the scraper survives without crashing, logs the failure, and records `failed_pages: 1`:

```json
{
  "start_time": "2026-11-17T11:47:04Z",
  "duration_seconds": 1.37,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```

---

## 8. Honest Limitations

- **Static Content Only**: The pipeline is tailored for server-rendered HTML. It does not execute client-side JavaScript or SPA frameworks (e.g. React/Vue hydration).
- **Hardcoded Catalogue Depth**: The crawler is intentionally bounded to the first 3 catalogue pages per project specifications.
- **Local Single-Node Storage**: Output is persisted as flat JSON files (`output/books.json`), which is ideal for datasets up to thousands of records, but distributed pipelines would require database storage.

---

## 9. Ethics Note

Always adhere to ethical data collection principles:
- **Use an official API when one exists** — direct structured interfaces are faster, cleaner, and intended for programmatic access.
- **Never bypass logins, paywalls, or blocks** — respect authentication boundaries and access restrictions.
- **Collect only what you need** — minimize data footprint and respect the target server's resources.
