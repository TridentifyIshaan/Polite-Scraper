# 🕷️ The Polite Scraper: Fault-Tolerant Web Data Extraction Pipeline

A production-grade, polite, and fault-tolerant web scraping pipeline engineered in Python with **Astral uv**. It crawls catalogue pages from [Books to Scrape](https://books.toscrape.com), extracts detail attributes, normalizes messy HTML into clean Pydantic-validated JSON, survives broken pages without crashing, and generates comprehensive telemetry reports at the end of every run.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Astral%20Tooling-DE5FE9?style=for-the-badge&logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2%20Schema%20Validation-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-HTML%20Parsing-59666C?style=for-the-badge)](https://www.crummy.com/software/BeautifulSoup/)
[![Requests](https://img.shields.io/badge/Requests-HTTP%20Client-2B5B84?style=for-the-badge)](https://requests.readthedocs.io/)
[![pytest](https://img.shields.io/badge/pytest-Unit%20Testing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)

---

## 📑 Table of Contents

- [Core Principles & Architectural Flow](#-core-principles--architectural-flow)
- [Target Classification & Ethics](#-target-classification--ethics)
- [Quickstart with Astral uv](#-quickstart-with-astral-uv)
- [Milestone Checkpoints (Stages 0–6)](#-milestone-checkpoints-stages-06)
- [Record Schema Specification](#-record-schema-specification)
- [Politeness & Rate Limiting Protocols](#-politeness--rate-limiting-protocols)
- [Headless Browser Decision & Trade-offs](#-headless-browser-decision--trade-offs)
- [Run Telemetry & Evidence](#-run-telemetry--evidence)
- [Production Enhancements & Observability](#-production-enhancements--observability)
- [Honest Limitations](#-honest-limitations)
- [Testing & Quality Assurance](#-testing--quality-assurance)

---

## 🏗️ Core Principles & Architectural Flow

The pipeline is built on three core backend engineering tenets:
1. **Check before you collect**: Explicitly classify and verify the target sandbox before issuing any requests.
2. **Be a polite guest**: Announce identity via custom user-agent, rate-limit requests, and cache aggressively.
3. **Trust nothing you scraped**: Treat all external markup as untrusted input; enforce rigid Pydantic validation before persistence.

```text
       ┌─────────────────────────────────────────────────────────────┐
       │                 TARGET: BOOKS TO SCRAPE                     │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
                        [1. POLITE FETCHER & CACHE]
               • Honest User-Agent: FlyRankPoliteScraper/1.0
               • 500ms Rate Limit Delay & 10.0s Timeout
               • Local Disk Cache in cache/ (Avoids Hammering)
               • Exponential Backoff for 5xx (Terminal on 403/404)
                                      │
                                      ▼
                       [2. CRAWLER & PAGER ENGINE]
               • Follows li.next a dynamically (3 Pages Max)
               • urljoin() Relative -> Absolute URL Resolution
               • Canonical Deduplication (60 Unique Book URLs)
                                      │
                                      ▼
                       [3. HTML EXTRACTOR & PARSER]
               • Scoped strictly to <article class="product_page">
               • 8 Raw Fields + Null-Safe Optional Description
               • Provenance Metadata (source_page, fetched_at UTC)
                                      │
                                      ▼
                     [4. NORMALIZATION & PYDANTIC GATE]
               • Price String -> price_gbp Numeric Normalization
               • Schema Validation against BookRecord Model
               • Schema Failures Quarantined to errors.json
                                      │
                                      ▼
                     [5. IDEMPOTENT PERSISTENCE & TELEMETRY]
               • output/books.json (Exactly 60 Records)
               • output/books.csv (RFC 4180 Flattened Export)
               • output/change-report.json (SHA-256 Content Hash Delta)
               • output/dashboard.html (Standalone HTML Observability)
               • output/run-report.json (Telemetry & Run Diagnostics)
```

---

## 🎯 Target Classification & Ethics

- **Target Host**: `https://books.toscrape.com`
- **Purpose & Permission**: Books to Scrape is an open educational sandbox specifically designed and hosted for students and engineers to safely practice web scraping without causing commercial harm or violating copyright.
- **Collection Scope**: Exactly the first 3 catalogue pages, visiting all 60 book detail pages.
- **Data Collected**:
  - `title`: Book title (string)
  - `product_url`: Canonical absolute URL starting with `https://`
  - `price_text`: Raw price string with currency symbol (e.g., `£51.77`)
  - `price_gbp`: Normalized numeric price in GBP (float, e.g., `51.77`)
  - `availability_text`: Raw stock availability string (e.g., `In stock (22 available)`)
  - `rating_text`: Textual star rating (e.g., `Three`)
  - `description`: Book description or `null` if absent
  - `source_page`: Provenance URL of the originating catalogue page
  - `fetched_at`: ISO 8601 UTC timestamp of fetch
- **Appropriateness**: Collecting 60 records from a practice sandbox at low request rates causes negligible server load and aligns completely with the site's explicit purpose.
- **Robots.txt Analysis**: A request to `https://books.toscrape.com/robots.txt` returned HTTP 404 (`no robots file found`). A missing `robots.txt` is not an implicit permission grant; our permission relies strictly on the site operator's explicit declaration that this is a practice sandbox for web scraping.

> **Mandatory Ethics Notice:**  
> *"I will not reuse this code on another site without checking its rules and terms first."*

---

## ⚡ Quickstart with Astral uv

This repository leverages **Astral uv** for deterministic dependency resolution and lightning-fast execution.

### Prerequisites
- Python 3.10+
- [Astral uv](https://docs.astral.sh/uv/) installed:
  ```bash
  # macOS / Linux:
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### One-Command Pipeline Run
Run the full scraping pipeline in under 5 minutes:

```bash
uv sync && uv run python src/main.py
```

### Alternative (Standard Python venv)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

---

## 📌 Milestone Checkpoints (Stages 0–6)

Each milestone represents a distinct architectural step with verifiable proof:

| Stage | Milestone Name | Run Command | Verifiable Checkpoint Proof |
| :--- | :--- | :--- | :--- |
| **Stage 0** | Classify Scraping Target | Inspected in README | Documented sandbox purpose, robots 404 result, and ethics statement. |
| **Stage 1** | Fetch Once, Cache Once | `uv run python src/main.py --stage 1` | Run 1 logs `[FETCH]` with bytes; Run 2 logs `[CACHE HIT]`. Zero HTML dumps. |
| **Stage 2** | Discover Three Pages | `uv run python src/main.py --stage 2` | Output: `catalogue_pages=3, discovered=60, unique_urls=60`. |
| **Stage 3** | Extract Book Details | `uv run python src/main.py --stage 3` | Prints sample record with all 8 raw fields; summary `detail_pages=60`. |
| **Stage 4** | Validate Normalized Records | `uv run python src/main.py --stage 4` | `output/books.json` has exactly 60 records; idempotent on repeated runs. |
| **Stage 5** | Survive Failures & Report | `uv run python src/main.py --stage 5` | Injected broken URL is skipped; run finishes with `failed_pages: 1` and 60 records. |
| **Stage 6** | Publish Scraper Evidence | `uv run python src/main.py` | Complete pipeline produces `books.json` + `run-report.json`. |

---

## 📋 Record Schema Specification

Records are strictly validated via Pydantic (`BookRecord`) prior to storage:

| Field | Type | Required | Description | Example |
| :--- | :--- | :---: | :--- | :--- |
| `title` | `str` | Yes | Non-empty sanitized book title | `"A Light in the Attic"` |
| `product_url` | `str` | Yes | Canonical absolute URL starting with `https://` | `"https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"` |
| `price_text` | `str` | Yes | Original price text with currency symbol | `"£51.77"` |
| `price_gbp` | `float` | Yes | Normalized floating-point price in GBP (>= 0.0) | `51.77` |
| `availability_text` | `str` | Yes | Raw stock availability status | `"In stock (22 available)"` |
| `rating_text` | `str` | Yes | Rating text representation | `"Three"` |
| `description` | `str \| null` | Optional | Book synopsis or null if not provided | `"It's hard to imagine..."` |
| `source_page` | `str` | Yes | Catalogue page URL of discovery | `"https://books.toscrape.com/catalogue/page-1.html"` |
| `fetched_at` | `str` | Yes | ISO 8601 UTC timestamp of fetch | `"2026-11-17T12:27:35Z"` |

Any record failing validation is diverted to `output/errors.json` alongside the specific validation error, preventing corrupt data from ever entering `output/books.json`.

---

## 🛡️ Politeness & Rate Limiting Protocols

1. **Honest User-Agent**: Every request carries:
   ```text
   FlyRankPoliteScraper/1.0 (+https://github.com/TridentifyIshaan/Polite-Scraper)
   ```
2. **Rate Limiting**: Enforces a mandatory minimum delay of **500 ms** between live HTTP requests.
3. **Connection Timeout**: Requests enforce a **10.0-second** timeout to avoid resource starvation.
4. **Local Disk Caching**: Responses are stored in `cache/`. Re-runs read from cache first, avoiding repeated traffic to the server.
5. **Selective Retries**:
   - HTTP 404 (Not Found) and HTTP 403 (Forbidden) are terminal and **never retried**.
   - HTTP 5xx errors or network timeouts trigger exponential backoff or `Retry-After` adherence.

---

## 🚀 Headless Browser Decision & Trade-offs

> **Architecture assessment:**  
> *"The data is already in the HTML the server sends, so a browser would only add cost."*

Unlike Single Page Applications (SPAs) that require client-side JavaScript execution, Books to Scrape delivers fully-rendered HTML from the server. Driving a headless browser (Playwright/Selenium) would consume 300MB+ RAM and significant CPU cycles per process for zero extra information. A lightweight client (`requests` + `BeautifulSoup`) performs the complete extraction in milliseconds with near-zero overhead.

---

## 📊 Run Telemetry & Evidence

### Clean Run (`output/run-report.json`)
```json
{
  "start_time": "2026-11-17T12:27:35Z",
  "duration_seconds": 0.36,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

### Fault-Tolerance Run with Injected Broken URL (`--stage 5`)
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

## 🌟 Production Enhancements & Observability

- **CSV Export (`output/books.csv`)**: Normalized tabular export of all 60 records with RFC 4180 escaping and whitespace-flattened descriptions.
- **Change Detection (`output/change-report.json`)**: Content hashing (SHA-256) per book to track newly added, modified, unchanged, or removed books across scraper runs.
- **Observability Dashboard (`output/dashboard.html`)**: Self-contained local HTML dashboard displaying real-time scraping stats, price metrics (min, max, average), stock status, and an interactive book table.
- **HTML Selector Fixtures (`tests/fixtures/`)**: Static HTML fixtures testing edge cases (missing descriptions, extra whitespace, malformed HTML) without network dependency.

---

## ⚠️ Honest Limitations

- **Static Content Only**: Tailored specifically for server-side rendered HTML; does not execute dynamic JavaScript hydration.
- **Hardcoded Catalogue Depth**: Crawler boundary is fixed to 3 catalogue pages per project specifications.
- **Local Single-Node Storage**: Output is persisted as flat JSON files (`output/books.json`), ideal for datasets under 100,000 records.

---

## 🧪 Testing & Quality Assurance

Run the comprehensive unit test suite with **Astral uv**:

```bash
uv run pytest -v
```

See [tests.md](file:///Users/ishaanrastogi/Desktop/Polite-Scraper/tests.md) for full execution details, fixture specifications, and edge-case testing documentation.
