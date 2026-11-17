# Polite Scraper

A robust, polite, and fault-tolerant web scraping pipeline in Python. It downloads catalogue pages from Books to Scrape, visits detail pages, normalizes messy HTML into clean, validated JSON records, survives broken pages without crashing, and generates an honest run report.

## Target Classification

- **Target Site**: Books to Scrape (`https://books.toscrape.com`)
- **Purpose & Permission**: Books to Scrape is an open educational sandbox specifically designed and hosted for developers and students to practice web scraping safely without causing commercial disruption or copyright violations.
- **Scope**: Exactly the first 3 catalogue pages (60 book records total).
- **Data Collected**:
  - `title`: Book title (string)
  - `product_url`: Canonical absolute URL to book detail page (string)
  - `price_text`: Raw price string (e.g., `£51.77`)
  - `price_gbp`: Normalized price as a floating-point number (e.g., `51.77`)
  - `availability_text`: Raw stock availability status (e.g., `In stock (22 available)`)
  - `rating_text`: Star rating as textual representation (e.g., `Three`)
  - `description`: Book description text or `null` if omitted
  - `source_page`: Provenance URL of the originating catalogue page
  - `fetched_at`: UTC timestamp in ISO 8601 format when the page was fetched
- **Why this is appropriate**: Collecting a limited volume of 60 items from an explicit educational sandbox at low request rates causes negligible server load and aligns completely with the site's intended use.
- **Robots.txt Analysis**: A request to `https://books.toscrape.com/robots.txt` returned HTTP 404 (`no robots file found`). A missing `robots.txt` is not an implicit permission grant; our permission relies strictly on the site operator's explicit declaration that this is a practice sandbox for web scraping.

> "I will not reuse this code on another site without checking its rules and terms first."
