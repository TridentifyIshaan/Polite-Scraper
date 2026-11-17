"""HTML parser for Books to Scrape catalogue and detail pages."""

from typing import List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def extract_catalogue_book_urls(html_content: str, base_url: str) -> List[str]:
    """Extract book detail page URLs from a catalogue page HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    book_links: List[str] = []

    for pod in soup.select("article.product_pod"):
        link_elem = pod.select_one("h3 a")
        if link_elem and link_elem.get("href"):
            raw_href = link_elem["href"].strip()
            absolute_url = urljoin(base_url, raw_href)
            book_links.append(absolute_url)

    return book_links


def extract_next_page_url(html_content: str, current_page_url: str) -> Optional[str]:
    """Extract the URL of the next catalogue page from the pager, if present."""
    soup = BeautifulSoup(html_content, "html.parser")
    next_elem = soup.select_one("li.next a")
    if next_elem and next_elem.get("href"):
        next_href = next_elem["href"].strip()
        return urljoin(current_page_url, next_href)
    return None
