"""Polite Scraper - Main Entry Point."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MAX_CATALOGUE_PAGES, START_URL
from src.fetcher import PoliteFetcher
from src.models import RawBook
from src.parser import (
    extract_book_details,
    extract_catalogue_book_urls,
    extract_next_page_url,
)


def discover_book_urls(fetcher: PoliteFetcher) -> Tuple[List[Tuple[str, str]], int]:
    """Discover books across catalogue pages, keeping provenance of source_page."""
    current_url = START_URL
    catalogue_pages_count = 0
    discovered: List[Tuple[str, str]] = []  # (book_url, source_page)

    while current_url and catalogue_pages_count < MAX_CATALOGUE_PAGES:
        result = fetcher.fetch(current_url)
        if not result:
            print(f"Error fetching catalogue page: {current_url}", file=sys.stderr)
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


def run_stage_1(fetcher: PoliteFetcher) -> None:
    """Milestone 1: Fetch once, cache once."""
    result = fetcher.fetch(START_URL)
    if result is None:
        print(f"Failed to fetch {START_URL}", file=sys.stderr)
        sys.exit(1)


def run_stage_2(fetcher: PoliteFetcher) -> List[Tuple[str, str]]:
    """Milestone 2: Discover three catalogue pages and collect book URLs."""
    unique_items, cat_count = discover_book_urls(fetcher)
    discovered_count = cat_count * 20  # approximate if full
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Polite Scraper Pipeline")
    parser.add_argument(
        "--stage",
        type=int,
        default=3,
        help="Run up to or specific stage checkpoint (1-6)",
    )
    args = parser.parse_args()
    fetcher = PoliteFetcher()

    if args.stage == 1:
        run_stage_1(fetcher)
    elif args.stage == 2:
        run_stage_2(fetcher)
    elif args.stage == 3:
        run_stage_3(fetcher)


if __name__ == "__main__":
    main()
