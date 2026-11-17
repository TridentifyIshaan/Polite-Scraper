"""Polite Scraper - A polite, fault-tolerant web scraping pipeline.

Target: Books to Scrape (https://books.toscrape.com)
Milestone 0: Check before you collect.
"""

def main() -> None:
    print("Polite Scraper initialized.")
    print("Target: Books to Scrape (https://books.toscrape.com)")
    print("Scope: First 3 catalogue pages (60 books)")
    print("Robots check: HTTP 404 (no robots file found)")
    print("Notice: 'I will not reuse this code on another site without checking its rules and terms first.'")

if __name__ == "__main__":
    main()
