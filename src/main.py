"""Polite Scraper - Main Entry Point."""

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import START_URL
from src.fetcher import PoliteFetcher


def run_stage_1() -> None:
    """Milestone 1: Fetch once, cache once."""
    fetcher = PoliteFetcher()
    result = fetcher.fetch(START_URL)
    if result is None:
        print(f"Failed to fetch {START_URL}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Polite Scraper Pipeline")
    parser.add_argument(
        "--stage",
        type=int,
        default=1,
        help="Run up to or specific stage checkpoint (1-6)",
    )
    args = parser.parse_args()

    if args.stage == 1:
        run_stage_1()


if __name__ == "__main__":
    main()
