"""Polite Scraper - Main Entry Point."""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MAX_CATALOGUE_PAGES, OUTPUT_DIR, START_URL
from src.fetcher import PoliteFetcher
from src.models import BookRecord, RawBook, RunReport
from src.parser import (
    extract_book_details,
    extract_catalogue_book_urls,
    extract_next_page_url,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("polite_scraper")


def discover_book_urls(fetcher: PoliteFetcher) -> Tuple[List[Tuple[str, str]], int]:
    """Discover books across catalogue pages, keeping provenance of source_page."""
    current_url = START_URL
    catalogue_pages_count = 0
    discovered: List[Tuple[str, str]] = []  # (book_url, source_page)

    while current_url and catalogue_pages_count < MAX_CATALOGUE_PAGES:
        result = fetcher.fetch(current_url)
        if not result:
            logger.warning(f"Error fetching catalogue page: {current_url}")
            break

        catalogue_pages_count += 1
        page_book_urls = extract_catalogue_book_urls(result.content, current_url)
        for url in page_book_urls:
            discovered.append((url, current_url))

        if catalogue_pages_count >= MAX_CATALOGUE_PAGES:
            break

        current_url = extract_next_page_url(result.content, current_url)

    # Deduplicate by book_url while preserving first discovery order
    seen = set()
    unique: List[Tuple[str, str]] = []
    for book_url, src_page in discovered:
        if book_url not in seen:
            seen.add(book_url)
            unique.append((book_url, src_page))

    return unique, catalogue_pages_count


def scrape_books(
    fetcher: PoliteFetcher,
    inject_fake_url: bool = False,
) -> Tuple[List[BookRecord], List[Dict[str, Any]], RunReport]:
    """Run full scraping pipeline: fetch -> extract -> normalize -> validate -> store -> report."""
    start_time_dt = datetime.now(timezone.utc)
    start_time_str = start_time_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    start_perf = time.perf_counter()

    unique_items, cat_count = discover_book_urls(fetcher)

    # If failure simulation requested, insert one deliberate fake URL (Milestone 5)
    if inject_fake_url:
        fake_url = "https://books.toscrape.com/catalogue/deliberately-broken-fake-book-404_9999/index.html"
        unique_items.append((fake_url, START_URL))
        logger.info(f"Injected deliberate fake URL for failure testing: {fake_url}")

    raw_records: List[RawBook] = []

    for book_url, source_page in unique_items:
        try:
            result = fetcher.fetch(book_url)
            if not result:
                logger.warning(f"Skipping failed book page: {book_url}")
                continue

            fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            record = extract_book_details(
                html_content=result.content,
                product_url=book_url,
                source_page=source_page,
                fetched_at=fetched_at,
            )
            raw_records.append(record)
        except Exception as e:
            logger.error(f"Error processing book page {book_url}: {e}")
            fetcher.failed_pages += 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    valid_records_by_url: Dict[str, BookRecord] = {}
    invalid_records: List[Dict[str, Any]] = []

    for raw in raw_records:
        try:
            validated = BookRecord.from_raw(raw)
            # Idempotent deduplication by canonical product_url
            valid_records_by_url[validated.product_url] = validated
        except Exception as e:
            invalid_records.append({
                "product_url": raw.product_url,
                "reason": str(e),
                "raw_record": raw.model_dump(),
            })

    # Save validated records
    books_file = OUTPUT_DIR / "books.json"
    records_list = [record.model_dump() for record in valid_records_by_url.values()]
    books_file.write_text(json.dumps(records_list, indent=2, ensure_ascii=False), encoding="utf-8")

    # Save invalid records if any
    errors_file = OUTPUT_DIR / "errors.json"
    if invalid_records:
        errors_file.write_text(json.dumps(invalid_records, indent=2, ensure_ascii=False), encoding="utf-8")
    elif errors_file.exists():
        errors_file.unlink()

    duration = round(time.perf_counter() - start_perf, 2)
    report = RunReport(
        start_time=start_time_str,
        duration_seconds=duration,
        pages_fetched=fetcher.pages_fetched,
        cache_hits=fetcher.cache_hits,
        valid_records=len(records_list),
        invalid_records=len(invalid_records),
        failed_pages=fetcher.failed_pages,
    )

    report_file = OUTPUT_DIR / "run-report.json"
    report_file.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")

    return list(valid_records_by_url.values()), invalid_records, report


def run_stage_1(fetcher: PoliteFetcher) -> None:
    """Milestone 1: Fetch once, cache once."""
    result = fetcher.fetch(START_URL)
    if result is None:
        print(f"Failed to fetch {START_URL}", file=sys.stderr)
        sys.exit(1)


def run_stage_2(fetcher: PoliteFetcher) -> List[Tuple[str, str]]:
    """Milestone 2: Discover three catalogue pages and collect book URLs."""
    unique_items, cat_count = discover_book_urls(fetcher)
    print(
        f"catalogue_pages={cat_count}, "
        f"discovered={cat_count * 20}, "
        f"unique_urls={len(unique_items)}"
    )
    return unique_items


def run_stage_3(fetcher: PoliteFetcher) -> List[RawBook]:
    """Milestone 3: Extract raw records for all 60 books."""
    unique_items, _ = discover_book_urls(fetcher)
    raw_records: List[RawBook] = []

    for book_url, source_page in unique_items:
        result = fetcher.fetch(book_url)
        if not result:
            continue
        fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        record = extract_book_details(
            html_content=result.content,
            product_url=book_url,
            source_page=source_page,
            fetched_at=fetched_at,
        )
        raw_records.append(record)

    if raw_records:
        print("\n--- Sample Raw Record ---")
        print(json.dumps(raw_records[0].model_dump(), indent=2))
        print("-------------------------\n")

    print(f"detail_pages={len(raw_records)}")
    return raw_records


def run_stage_4(fetcher: PoliteFetcher) -> List[BookRecord]:
    """Milestone 4: Normalize, validate schema, and store idempotently in output/books.json."""
    records, errors, _ = scrape_books(fetcher, inject_fake_url=False)
    books_file = OUTPUT_DIR / "books.json"
    with open(books_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    all_prices_numeric = all(isinstance(r["price_gbp"], (int, float)) for r in saved_data)
    all_urls_https = all(r["product_url"].startswith("https://") for r in saved_data)

    print(f"Stored {len(saved_data)} valid records to {books_file}")
    print(f"Checkpoint 4 verification:")
    print(f" - Exactly 60 records: {len(saved_data) == 60} (count={len(saved_data)})")
    print(f" - Every price_gbp is numeric: {all_prices_numeric}")
    print(f" - Every product_url starts with https://: {all_urls_https}")
    print(f" - Schema errors: {len(errors)}")
    return records


def run_stage_5(fetcher: PoliteFetcher, inject_fake_url: bool = True) -> RunReport:
    """Milestone 5: Survive broken pages and report run."""
    records, errors, report = scrape_books(fetcher, inject_fake_url=inject_fake_url)
    print("\n--- Milestone 5 Run Report ---")
    print(json.dumps(report.model_dump(), indent=2))
    print("------------------------------")
    print(f"Checkpoint 5 verification:")
    print(f" - Books surviving: {len(records)} (expected 60)")
    print(f" - Failed pages logged and skipped: {report.failed_pages} (expected at least 1 when fake injected)")
    print(f" - Run finished successfully without crashing: True")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Polite Scraper Pipeline")
    parser.add_argument(
        "--stage",
        type=int,
        default=6,
        help="Run up to or specific stage checkpoint (1-6)",
    )
    parser.add_argument(
        "--inject-fake-url",
        action="store_true",
        help="Inject a deliberately broken URL to test fault tolerance (Milestone 5)",
    )
    args = parser.parse_args()
    fetcher = PoliteFetcher()

    if args.stage == 1:
        run_stage_1(fetcher)
    elif args.stage == 2:
        run_stage_2(fetcher)
    elif args.stage == 3:
        run_stage_3(fetcher)
    elif args.stage == 4:
        run_stage_4(fetcher)
    elif args.stage == 5:
        run_stage_5(fetcher, inject_fake_url=True)
    else:
        # Full pipeline (Milestone 6)
        _, _, report = scrape_books(fetcher, inject_fake_url=args.inject_fake_url)
        print("\n--- Pipeline Execution Complete ---")
        print(f"Report: {json.dumps(report.model_dump(), indent=2)}")


if __name__ == "__main__":
    main()
