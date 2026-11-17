"""HTML parser for Books to Scrape catalogue and detail pages."""

from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.models import RawBook


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


def extract_book_details(
    html_content: str,
    product_url: str,
    source_page: str,
    fetched_at: str,
) -> RawBook:
    """Extract raw book attributes from a detail page HTML.
    
    Aims selectors strictly at the product area (<article class="product_page">).
    Never invents descriptions: stores None if missing.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    product_elem = soup.select_one("article.product_page")

    # Scope all queries to the product area
    context = product_elem if product_elem is not None else soup

    # Title
    title_elem = context.select_one("h1")
    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

    # Price
    price_elem = context.select_one("p.price_color")
    price_text = price_elem.get_text(strip=True) if price_elem else ""

    # Availability
    avail_elem = context.select_one("p.availability")
    availability_text = avail_elem.get_text(strip=True) if avail_elem else ""

    # Star rating
    rating_elem = context.select_one("p.star-rating")
    rating_text = ""
    if rating_elem:
        classes = rating_elem.get("class", [])
        rating_classes = [c for c in classes if c != "star-rating"]
        if rating_classes:
            rating_text = rating_classes[0]

    # Description (optional)
    description: Optional[str] = None
    desc_header = context.select_one("#product_description")
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            desc_text = desc_p.get_text(strip=True)
            if desc_text:
                description = desc_text

    return RawBook(
        title=title,
        product_url=product_url,
        price_text=price_text,
        availability_text=availability_text,
        rating_text=rating_text,
        description=description,
        source_page=source_page,
        fetched_at=fetched_at,
    )
