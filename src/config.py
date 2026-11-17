"""Configuration settings for Polite Scraper."""

from pathlib import Path

BASE_URL: str = "https://books.toscrape.com"
START_URL: str = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT: str = "FlyRankPoliteScraper/1.0 (+https://github.com/TridentifyIshaan/Polite-Scraper)"

REQUEST_TIMEOUT: float = 10.0
POLITE_DELAY_SECONDS: float = 0.5

CACHE_DIR: Path = Path("cache")
OUTPUT_DIR: Path = Path("output")

MAX_CATALOGUE_PAGES: int = 3
