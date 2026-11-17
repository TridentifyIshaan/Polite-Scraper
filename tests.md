# 🧪 Polite Scraper: Test Execution & Verification Manual

This document provides a comprehensive reference for executing the test suites, validating scraping pipeline milestones, and verifying fault tolerance and idempotent data persistence for **The Polite Scraper**.

---

## 🚀 Quick Execution with Astral uv

Run the complete test suite with **Astral uv**:

```bash
uv run pytest -v
```

To run individual test modules:
```bash
# Parser and schema tests
uv run pytest -v tests/test_parser.py

# Export and observability tests
uv run pytest -v tests/test_export.py
```

---

## 📋 Unit Test Suite Overview

All unit tests run completely offline using deterministic test fixtures in `tests/fixtures/`, requiring zero network requests to the target sandbox:

| Test File | Test Case | Purpose & Invariant Verified |
| :--- | :--- | :--- |
| `test_parser.py` | `test_price_normalization` | Verifies `"£51.77"` cleanly normalizes to `float` `51.77` with raw text preserved. |
| `test_parser.py` | `test_relative_to_absolute_urls` | Ensures relative links (`../book/index.html`) resolve to canonical `https://` URLs using `urljoin`. |
| `test_parser.py` | `test_missing_description_stored_as_none` | Confirms books without `#product_description` store `None` (`null`) and never fabricate text. |
| `test_parser.py` | `test_extra_whitespace_handling` | Confirms parser strips irregular whitespace, indentation, and interior line breaks. |
| `test_parser.py` | `test_duplicate_url_deduplication` | Confirms duplicate book links across pages are deduplicated while preserving discovery order. |
| `test_parser.py` | `test_malformed_html_fixture_does_not_crash` | Proves malformed HTML without standard product containers fails gracefully without unhandled exceptions. |
| `test_parser.py` | `test_schema_validation_rejects_invalid_urls` | Ensures Pydantic schema rejects non-https URLs (`http://`) or malformed payloads before storage. |
| `test_export.py` | `test_export_books_to_csv` | Verifies CSV export adheres to RFC 4180 with flattened whitespace in multiline descriptions. |
| `test_export.py` | `test_change_detection_workflow` | Validates SHA-256 state tracking for `new`, `changed`, `unchanged`, and `gone` records. |
| `test_export.py` | `test_generate_dashboard` | Confirms standalone HTML dashboard renders metrics, price ranges, and tabular records. |

---

## 🔍 Milestone Verification Checkpoints

Run and verify each specific project milestone from the CLI:

### Milestone 1: Fetch Once, Cache Once
```bash
uv run python src/main.py --stage 1
```
- **First run**: Prints `[FETCH] https://books.toscrape.com/catalogue/page-1.html (<size> bytes)`.
- **Second run**: Prints `[CACHE HIT] cache/catalogue-page-1.html (<size> bytes)`. Neither dumps raw HTML.

### Milestone 2: Discover 3 Catalogue Pages
```bash
uv run python src/main.py --stage 2
```
- **Output**: `catalogue_pages=3, discovered=60, unique_urls=60`.
- Verifies crawler follows `li.next a` without hardcoding URLs.

### Milestone 3: Extract Raw Detail Records
```bash
uv run python src/main.py --stage 3
```
- **Output**: Prints formatted sample record containing all 8 raw fields and ends with `detail_pages=60`.

### Milestone 4: Normalize, Validate & Store Idempotently
```bash
uv run python src/main.py --stage 4
```
- **Output**: Validates against `BookRecord` Pydantic schema and writes `output/books.json`.
- **Checkpoint**: Exactly 60 records, all numeric `price_gbp`, all `https://` URLs; re-running produces identical 60 records.

### Milestone 5: Survive Broken Pages & Run Report
```bash
uv run python src/main.py --stage 5
```
- **Output**: Injects a deliberate broken URL; verifies pipeline survives, logs and skips the bad page, maintains 60 good records, and writes `output/run-report.json` with `failed_pages: 1`.

### Milestone 6: Full End-to-End Pipeline
```bash
uv run python src/main.py
```
- **Artifacts Produced**:
  - `output/books.json`: 60 schema-validated book records
  - `output/books.csv`: RFC 4180 tabular export
  - `output/change-report.json`: Content-hash delta tracking
  - `output/dashboard.html`: Self-contained observability dashboard
  - `output/run-report.json`: Complete execution telemetry
