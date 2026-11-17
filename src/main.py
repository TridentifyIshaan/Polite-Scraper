"""Polite Scraper - Main Entry Point."""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MAX_CATALOGUE_PAGES, START_URL
from src.fetcher import PoliteFetcher
from src.parser import extract_catalogue_book_urls, extract_next_page_url


def run_stage_1(fetcher: PoliteFetcher) -> None:
    """Milestone 1: Fetch once, cache once."""
    result = fetcher.fetch(START_URL)
    if result is None:
        print(f"Failed to fetch {START_URL}", file=sys.stderr)
        sys.exit(1)


def run_stage_2(fetcher: PoliteFetcher) -> Tuple[List[str], int, int, int]:
    """Milestone 2: Discover three catalogue pages and collect book URLs."""
    current_url = START_URL
    catalogue_pages_count = 0
    discovered_urls: List[str] = []

    while current_url and catalogue_pages_count < MAX_CATALOGUE_PAGES:
        result = fetcher.fetch(current_url)
        if not result:
            print(f"Error fetching catalogue page: {current_url}", file=sys.stderr)
            break

        catalogue_pages_count += 1
        page_book_urls = extract_catalogue_book_urls(result.content, current_url)
        discovered_urls.extend(page_book_urls)

        # Stop after MAX_CATALOGUE_PAGES
        if catalogue_pages_count >= MAX_CATALOGUE_PAGES:
            break

        current_url = extract_next_page_url(result.content, current_url)

    # Deduplicate while preserving order
    unique_urls: List[str] = list(dict.fromkeys(discovered_urls))

    print(
        f"catalogue_pages={catalogue_pages_count}, "
        f"discovered={len(discovered_urls)}, "
        f"unique_urls={len(unique_urls)}"
    )
    return unique_urls, catalogue_pages_count, len(discovered_urls), len(unique_urls)


def main() -> None:
    parser = argparse.ArgumentParser(description="Polite Scraper Pipeline")
    parser.add_argument(
        "--stage",
        type=int,
        default=2,
        help="Run up to or specific stage checkpoint (1-6)",
    )
    args = parser.parse_args()
    fetcher = PoliteFetcher()

    if args.stage == 1:
        run_stage_1(fetcher)
    elif args.stage == 2:
        run_stage_2(fetcher)


if __name__ == "__main__":
    main()
